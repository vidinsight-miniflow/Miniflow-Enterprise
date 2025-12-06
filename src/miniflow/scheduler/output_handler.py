import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from typing import Dict, Any, List, Optional

from ..utils.handlers.configuration_handler import ConfigurationHandler
from ..services import SchedulerForOutputHandler
from ..core.exceptions import (
    HandlerConfigurationError,
    ResultProcessingError,
    SchedulerError,
    ErrorCode,
    InvalidInputError
)


class OutputHandler:
    """
    OutputHandler: Engine'den result'ları alır ve SchedulerService ile işler.
    
    Sorumluluklar:
    - Engine'den result'ları al (batch)
    - Her result için SchedulerForOutputHandler.process_execution_result() çağır
    - Başarılı/başarısız işlemleri takip et
    """
    
    def __init__(self, scheduler_service: SchedulerForOutputHandler, exec_engine):
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
            self.batch_size = ConfigurationHandler.get_int(section, "output_handler_batch_size", fallback=50)
            self.worker_threads = ConfigurationHandler.get_int(section, "output_handler_worker_threads", fallback=4)
            self.max_retries = ConfigurationHandler.get_int(section, "output_handler_max_retries", fallback=3)
            
            # Float values - use new get_float method
            self.result_timeout = ConfigurationHandler.get_float(section, "output_handler_result_timeout", fallback=60.0)
            self.min_polling_interval = ConfigurationHandler.get_float(section, "output_handler_min_polling_interval", fallback=0.1)
            self.max_polling_interval = ConfigurationHandler.get_float(section, "output_handler_max_polling_interval", fallback=5.0)
            self.retry_delay = ConfigurationHandler.get_float(section, "output_handler_retry_delay", fallback=1.0)
            
            # Boolean values - use fallback for default
            self.adaptive_polling = ConfigurationHandler.get_bool(section, "output_handler_adaptive_polling", fallback=True)
            self.parallel_processing = ConfigurationHandler.get_bool(section, "output_handler_parallel_processing", fallback=True)
            
        except Exception as e:
            raise HandlerConfigurationError(
                handler_name="OutputHandler",
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
                thread_name_prefix="OutputHandlerWorker"
            )

            # Reset polling interval
            self.current_polling_interval = self.min_polling_interval

            self.running = True

            # Main thread başlat
            self.main_thread = threading.Thread(
                target=self._main_loop,
                name="OutputHandlerThread", 
                daemon=True
            )
            self.main_thread.start()
            
            return True
            
        except Exception as e:
            self.running = False
            raise SchedulerError(
                ErrorCode.SCHEDULER_ERROR,
                f"Failed to start OutputHandler: {str(e)}",
                error_details={"handler": "OutputHandler", "original_error": str(e)}
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
                f"Error stopping OutputHandler: {str(e)}",
                error_details={"handler": "OutputHandler", "original_error": str(e)}
            ) from e

    def _main_loop(self):
        """Ana döngü"""
        while self.running and not self.shutdown_event.is_set():
            try:
                # Engine'den result'ları al
                results = self.exec_engine.get_execution_results(max_items=self.batch_size)
                
                if not results:
                    self._adjust_polling_interval(idle=True)
                    time.sleep(self.current_polling_interval)
                    continue
                
                self._adjust_polling_interval(idle=False)
                
                # Result'ları işle
                self._process_results(results)
                
            except Exception as e:
                # Hataları logla ve devam et (main loop kesilmemeli)
                print(f"[ERROR] OutputHandler._main_loop: {type(e).__name__}: {e}")
                time.sleep(self.current_polling_interval)
    
    def _process_results(self, results: List[Dict[str, Any]]):
        """Result'ları işle (paralel)"""
        if not results:
            return
        
        if self.parallel_processing and self.worker_pool:
            # Paralel işlem
            future_to_result = {
                self.worker_pool.submit(self._process_single_result, result): result
                for result in results
            }
            
            try:
                for future in as_completed(future_to_result.keys(), timeout=self.result_timeout):
                    result = future_to_result[future]
                    try:
                        success = future.result(timeout=1.0)
                        if not success:
                            print(f"[ERROR] OutputHandler._process_results (parallel): Result processing returned False")
                    except Exception as e:
                        print(f"[ERROR] OutputHandler._process_results (parallel): {type(e).__name__}: {e}")
            except FuturesTimeoutError:
                # Kalan future'ları cancel et
                for future in future_to_result.keys():
                    if not future.done():
                        future.cancel()
                print(f"[ERROR] OutputHandler._process_results: Timeout processing results")
                
        else:
            # Sequential işlem
            for result in results:
                try:
                    success = self._process_single_result(result)
                    if not success:
                        print(f"[ERROR] OutputHandler._process_results (sequential): Result processing returned False")
                except Exception as e:
                    print(f"[ERROR] OutputHandler._process_results (sequential): {type(e).__name__}: {e}")
    
    def _process_single_result(self, result: Dict[str, Any]) -> bool:
        """Tek bir result'ı işle (retry ile)"""
        # Validation
        if not self._validate_result(result):
            raise InvalidInputError(
                field_name="result",
                message=f"Invalid result structure: missing required fields. Result: {result}"
            )
        
        for attempt in range(self.max_retries):
            try:
                # SchedulerService ile işle
                self.scheduler_service.process_execution_result(result=result)
                return True
                
            except InvalidInputError:
                # Validation hatası - retry yapma
                raise
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    print(f"[ERROR] OutputHandler._process_single_result: Failed after {attempt + 1} attempts for execution_id={result.get('execution_id')}, node_id={result.get('node_id')}: {type(e).__name__}: {e}")
                    raise ResultProcessingError(
                        execution_id=result.get('execution_id'),
                        node_id=result.get('node_id'),
                        attempt=attempt + 1,
                        original_error=e
                    ) from e
        
        return False
    
    def _validate_result(self, result: Dict[str, Any]) -> bool:
        """Result validation"""
        # Eğer sadece error varsa (thread controller hatası), bu geçerli bir result değil
        if 'error' in result and len(result) == 1:
            print(f"[WARNING] OutputHandler: Skipping error-only result (not a valid execution result): {result}")
            return False
        
        required_fields = ['execution_id', 'node_id', 'status']
        return all(field in result for field in required_fields)
    
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
