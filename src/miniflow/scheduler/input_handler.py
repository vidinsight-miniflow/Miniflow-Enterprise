import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from typing import Dict, Any, List, Optional

from ..utils.handlers.configuration_handler import ConfigurationHandler
from ..services import SchedulerForInputHandler
from ..core.exceptions import (
    HandlerConfigurationError,
    ContextCreationError,
    PayloadPreparationError,
    EngineSubmissionError,
    SchedulerError,
    ErrorCode
)


class InputHandler:
    """
    InputHandler: Ready execution inputs'ları alır, context oluşturur ve engine'e gönderir.
    
    Sorumluluklar:
    - SchedulerForInputHandler.get_ready_execution_inputs() ile ready task'ları al
    - Her task için SchedulerForInputHandler.create_execution_context() ile context oluştur
    - Payload'ları hazırla ve engine'e gönder
    """
    
    def __init__(self, scheduler_service: SchedulerForInputHandler, exec_engine):
        self.scheduler_service = scheduler_service
        self.exec_engine = exec_engine

        # Config'den ayarları yükle
        self._load_config()

        # Threading ve lifecycle
        self.running = False
        self.shutdown_event = threading.Event()
        self.main_thread: Optional[threading.Thread] = None
        self.worker_pool: Optional[ThreadPoolExecutor] = None
        
        # Adaptive polling için current interval
        self.current_polling_interval = self.min_polling_interval

    def _load_config(self):
        """Config'den ayarları yükle"""
        section = "Scheduler"
        
        try:
            # Ensure config is loaded (safe to call multiple times)
            ConfigurationHandler.ensure_loaded()
            
            # Integer values - use fallback directly, don't use 'or' operator (0 is valid)
            self.batch_size = ConfigurationHandler.get_int(section, "input_handler_batch_size", fallback=50)
            self.worker_threads = ConfigurationHandler.get_int(section, "input_handler_worker_threads", fallback=4)
            self.max_retries = ConfigurationHandler.get_int(section, "input_handler_max_retries", fallback=3)
            
            # Float values - use new get_float method
            self.context_timeout = ConfigurationHandler.get_float(section, "input_handler_context_timeout", fallback=30.0)
            self.engine_timeout = ConfigurationHandler.get_float(section, "input_handler_engine_timeout", fallback=60.0)
            self.min_polling_interval = ConfigurationHandler.get_float(section, "input_handler_min_polling_interval", fallback=0.1)
            self.max_polling_interval = ConfigurationHandler.get_float(section, "input_handler_max_polling_interval", fallback=5.0)
            self.retry_delay = ConfigurationHandler.get_float(section, "input_handler_retry_delay", fallback=1.0)
            
            # Boolean values - use fallback for default
            self.adaptive_polling = ConfigurationHandler.get_bool(section, "input_handler_adaptive_polling", fallback=True)
            self.parallel_context = ConfigurationHandler.get_bool(section, "input_handler_parallel_context", fallback=True)
            
        except Exception as e:
            raise HandlerConfigurationError(
                handler_name="InputHandler",
                original_error=e
            ) from e

    def start(self) -> bool:
        """Handler'ı başlat"""
        if self.running:
            return True

        try:
            self.shutdown_event.clear()

            # Worker pool oluştur
            self.worker_pool = ThreadPoolExecutor(
                max_workers=self.worker_threads,
                thread_name_prefix="InputHandlerWorker"
            )

            # Reset polling interval
            self.current_polling_interval = self.min_polling_interval

            self.running = True
            
            # Main thread başlat
            self.main_thread = threading.Thread(
                target=self._main_loop,
                name="InputHandlerThread", 
                daemon=True
            )
            self.main_thread.start()
            
            return True
            
        except Exception as e:
            self.running = False
            raise SchedulerError(
                ErrorCode.SCHEDULER_ERROR,
                f"Failed to start InputHandler: {str(e)}",
                error_details={"handler": "InputHandler", "original_error": str(e)}
            ) from e

    def stop(self) -> bool:
        """Handler'ı durdur"""
        if not self.running:
            return True

        try:
            self.shutdown_event.set()

            if self.worker_pool:
                self.worker_pool.shutdown(wait=True)

            if self.main_thread and self.main_thread.is_alive():
                self.main_thread.join(timeout=5)

            self.running = False
            return True
            
        except Exception as e:
            self.running = False
            raise SchedulerError(
                ErrorCode.SCHEDULER_ERROR,
                f"Error stopping InputHandler: {str(e)}",
                error_details={"handler": "InputHandler", "original_error": str(e)}
            ) from e

    def _main_loop(self):
        """Ana döngü"""
        while self.running and not self.shutdown_event.is_set():
            try:
                # Ready task ID'lerini al
                result = self.scheduler_service.get_ready_execution_inputs(batch_size=self.batch_size)
                task_ids = result.get("ids", [])
                count = result.get("count", 0)
                
                if not task_ids:
                    self._adjust_polling_interval(idle=True)
                    time.sleep(self.current_polling_interval)
                    continue

                self._adjust_polling_interval(idle=False)

                # Task'ları işle
                self._process_tasks(task_ids)

            except Exception as e:
                # Hataları logla ve devam et (main loop kesilmemeli)
                print(f"[ERROR] InputHandler._main_loop: {type(e).__name__}: {e}")
                time.sleep(self.current_polling_interval)

    def _process_tasks(self, task_ids: List[str]):
        """Task'ları işle: context oluştur, payload hazırla, engine'e gönder"""
        if not task_ids:
            return
        
        # Context'leri oluştur (paralel)
        contexts = self._create_contexts_batch(task_ids)
        
        if not contexts:
            return
        
        # Payload'ları hazırla
        payloads, execution_input_ids = self._prepare_payloads(contexts)
        
        if not payloads:
            return

        # Engine'e gönder
        try:
            self._submit_to_engine(payloads)
            # Başarılı gönderimden sonra ExecutionInput'ları sil
            self._remove_execution_inputs(execution_input_ids)
        except Exception as e:
            # Engine'e gönderim başarısız oldu, ExecutionInput'ları silme
            raise
    
    def _create_contexts_batch(self, task_ids: List[str]) -> Dict[str, Dict]:
        """Paralel olarak context'leri oluştur"""
        contexts = {}
        
        if self.parallel_context and self.worker_pool:
            # Paralel işlem
            future_to_id = {
                self.worker_pool.submit(self._create_single_context, task_id): task_id
                for task_id in task_ids
            }
            
            try:
                for future in as_completed(future_to_id.keys(), timeout=self.context_timeout):
                    task_id = future_to_id[future]
                    try:
                        context = future.result(timeout=1.0)
                        if context:
                            contexts[task_id] = context
                    except Exception as e:
                        print(f"[ERROR] InputHandler._create_contexts_batch: Failed to create context for {task_id}: {type(e).__name__}: {e}")
            except FuturesTimeoutError:
                # Kalan future'ları cancel et
                for future in future_to_id.keys():
                    if not future.done():
                        future.cancel()
                print(f"[ERROR] InputHandler._create_contexts_batch: Timeout creating contexts. Created: {len(contexts)}/{len(task_ids)}")
        else:
            # Sequential işlem
            for task_id in task_ids:
                try:
                    context = self._create_single_context(task_id)
                    if context:
                        contexts[task_id] = context
                except Exception as e:
                    print(f"[ERROR] InputHandler._create_contexts_batch: Failed to create context for {task_id}: {type(e).__name__}: {e}")
        
        return contexts
    
    def _create_single_context(self, execution_input_id: str) -> Optional[Dict]:
        """Tek bir context oluştur"""
        try:
            return self.scheduler_service.create_execution_context(execution_input_id=execution_input_id)
        except Exception as e:
            raise ContextCreationError(
                execution_input_id=execution_input_id,
                original_error=e
            ) from e
    
    def _prepare_payloads(self, contexts: Dict[str, Dict]) -> tuple[List[Dict], List[str]]:
        """Context'leri engine payload'larına dönüştür
        
        Engine'e gönderilecek yapı:
        - script_path: Script dosya yolu
        - params: Flat yapıda script parametreleri (iç içe değil)
        - execution_id: Takip için
        - node_id: Takip için
        - max_retries: Retry sayısı
        - timeout_seconds: Timeout süresi
        
        Returns:
            (payloads, execution_input_ids) tuple
        """
        payloads = []
        execution_input_ids = []
        
        for execution_input_id, context in contexts.items():
            try:
                # Script parametrelerini flat yapıda hazırla
                params = context.get('params', {})
                
                payload = {
                    'script_path': context.get('script_path'),
                    'params': params,  # Flat yapıda script parametreleri
                    'execution_id': context.get('execution_id'),  # Takip için
                    'node_id': context.get('node_id'),  # Takip için
                    'max_retries': context.get('max_retries', 3),
                    'timeout_seconds': context.get('timeout_seconds', 300),
                    'process_type': 'iob'  # Default IO-bound
                }
                
                # Validation
                if not payload['script_path']:
                    raise PayloadPreparationError(
                        execution_input_id=execution_input_id,
                        reason="Missing script_path"
                    )
                
                payloads.append(payload)
                execution_input_ids.append(execution_input_id)
                
            except PayloadPreparationError:
                # Re-raise payload preparation errors
                raise
            except Exception as e:
                raise PayloadPreparationError(
                    execution_input_id=execution_input_id,
                    original_error=e
                ) from e
        
        return payloads, execution_input_ids
    
    def _submit_to_engine(self, payloads: List[Dict]):
        """Engine'e batch gönderim yap"""
        if not payloads:
            return
        
        for attempt in range(self.max_retries):
            try:
                success = self.exec_engine.put_items_bulk(payloads)
                
                if success:
                    return
                else:
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    else:
                        raise EngineSubmissionError(
                            payload_count=len(payloads),
                            attempt=attempt + 1
                        )
                        
            except EngineSubmissionError:
                # Re-raise if it's the last attempt
                raise
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    print(f"[ERROR] InputHandler._submit_to_engine: Failed after {attempt + 1} attempts: {type(e).__name__}: {e}")
                    raise EngineSubmissionError(
                        payload_count=len(payloads),
                        attempt=attempt + 1,
                        original_error=e
                    ) from e
    
    def _remove_execution_inputs(self, execution_input_ids: List[str]):
        """Engine'e gönderilen ExecutionInput'ları sil"""
        if not execution_input_ids:
                    return

        try:
            self.scheduler_service.remove_processed_execution_inputs(execution_input_ids=execution_input_ids)
        except Exception as e:
            # ExecutionInput silme hatası - log'la ama devam et
            # Çünkü task zaten engine'e gönderildi
            print(f"[ERROR] InputHandler._remove_execution_inputs: Failed to remove execution inputs: {type(e).__name__}: {e}")
    
    def _adjust_polling_interval(self, idle: bool):
        """Adaptive polling interval ayarla"""
        if not self.adaptive_polling:
            return
            
        old_interval = self.current_polling_interval
        
        if idle:
            new_interval = min(old_interval * 1.2, self.max_polling_interval)
        else:
            new_interval = max(old_interval * 0.8, self.min_polling_interval)
        
        if old_interval != new_interval:
            self.current_polling_interval = new_interval
