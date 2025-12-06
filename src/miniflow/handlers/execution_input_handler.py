import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from typing import Dict, Any, List, Optional

from ..utils import ConfigurationHandler
from ..services import SchedulerForInputHandler
from ..core.logger import get_logger


logger = get_logger(__name__)


class ExecutionInputHandler:
    """
    Execution input handler: Hazır execution input'ları alır, context oluşturur ve engine'e gönderir.
    
    Lifecycle:
    1. start() -> Handler'ı başlatır (main loop thread'i başlar)
    2. _main_loop() -> Sürekli çalışan ana döngü
       - get_ready_execution_inputs() -> Hazır input'ları getirir
       - _process_tasks() -> Task'ları işler
       - _create_contexts_batch() -> Context'leri oluşturur (paralel)
       - _prepare_payloads() -> Engine payload'larını hazırlar
       - _submit_to_engine() -> Engine'e gönderir
    3. stop() -> Handler'ı durdurur
    """
    
    _initialized = False
    _running = False
    _shutdown_event: Optional[threading.Event] = None
    _main_thread: Optional[threading.Thread] = None
    _worker_pool: Optional[ThreadPoolExecutor] = None
    _engine_manager = None
    _current_polling_interval: float = 0.1

    batch_size: int = 50
    worker_threads: int = 4
    max_retries: int = 3
    context_timeout: float = 30.0
    engine_timeout: float = 60.0
    min_polling_interval: float = 0.1
    max_polling_interval: float = 5.0
    retry_delay: float = 1.0
    adaptive_polling: bool = True
    parallel_context: bool = True

    @classmethod
    def _load_config(cls):
        """Config dosyasından ayarları yükler."""
        if cls._initialized:
            return
        
        try:
            ConfigurationHandler.ensure_loaded()
            section = "INPUT_HANDLER"
            
            cls.batch_size = ConfigurationHandler.get_int(section, "input_handler_batch_size", fallback=50)
            cls.worker_threads = ConfigurationHandler.get_int(section, "input_handler_worker_threads", fallback=4)
            cls.max_retries = ConfigurationHandler.get_int(section, "input_handler_max_retries", fallback=3)
            cls.context_timeout = ConfigurationHandler.get_float(section, "input_handler_context_timeout", fallback=30.0)
            cls.engine_timeout = ConfigurationHandler.get_float(section, "input_handler_engine_timeout", fallback=60.0)
            cls.min_polling_interval = ConfigurationHandler.get_float(section, "input_handler_min_polling_interval", fallback=0.1)
            cls.max_polling_interval = ConfigurationHandler.get_float(section, "input_handler_max_polling_interval", fallback=5.0)
            cls.retry_delay = ConfigurationHandler.get_float(section, "input_handler_retry_delay", fallback=1.0)
            cls.adaptive_polling = ConfigurationHandler.get_bool(section, "input_handler_adaptive_polling", fallback=True)
            cls.parallel_context = ConfigurationHandler.get_bool(section, "input_handler_parallel_context", fallback=True)
            
            cls._initialized = True
            logger.info(f"ExecutionInputHandler config loaded: batch_size={cls.batch_size}, worker_threads={cls.worker_threads}")
            
        except Exception as e:
            logger.error(f"Failed to load ExecutionInputHandler config: {e}")
            raise

    @classmethod
    def start(cls, engine_manager):
        """Handler'ı başlatır ve main loop thread'ini başlatır."""
        if cls._running:
            logger.warning("ExecutionInputHandler is already running")
            return True
        
        try:
            cls._load_config()
            cls._engine_manager = engine_manager
            
            if not engine_manager:
                raise ValueError("engine_manager is required")
            
            cls._shutdown_event = threading.Event()
            cls._shutdown_event.clear()
            
            cls._worker_pool = ThreadPoolExecutor(
                max_workers=cls.worker_threads,
                thread_name_prefix="ExecutionInputHandlerWorker"
            )
            
            cls._current_polling_interval = cls.min_polling_interval
            cls._running = True
            
            cls._main_thread = threading.Thread(
                target=cls._main_loop,
                name="ExecutionInputHandlerThread",
                daemon=True
            )
            cls._main_thread.start()
            
            logger.info("ExecutionInputHandler started successfully")
            return True
            
        except Exception as e:
            cls._running = False
            logger.error(f"Failed to start ExecutionInputHandler: {e}")
            raise

    @classmethod
    def stop(cls):
        """Handler'ı durdurur ve kaynakları temizler."""
        if not cls._running:
            return True
        
        try:
            logger.info("Stopping ExecutionInputHandler...")
            cls._shutdown_event.set()
            
            if cls._worker_pool:
                cls._worker_pool.shutdown(wait=True)
                cls._worker_pool = None
            
            if cls._main_thread and cls._main_thread.is_alive():
                cls._main_thread.join(timeout=10)
            
            # Grace period for active transactions to complete
            time.sleep(0.5)
            
            cls._running = False
            logger.info("ExecutionInputHandler stopped successfully")
            return True
            
        except Exception as e:
            cls._running = False
            logger.error(f"Error stopping ExecutionInputHandler: {e}")
            raise

    @classmethod
    def _main_loop(cls):
        """Ana döngü: sürekli olarak hazır execution input'ları kontrol eder ve işler."""
        logger.info("ExecutionInputHandler main loop started")
        
        while cls._running and not cls._shutdown_event.is_set():
            try:
                result = SchedulerForInputHandler.get_ready_execution_inputs(batch_size=cls.batch_size)
                task_ids = result.get("ids", [])
                count = result.get("count", 0)
                
                if not task_ids:
                    cls._adjust_polling_interval(idle=True)
                    time.sleep(cls._current_polling_interval)
                    continue
                
                logger.debug(f"Found {count} ready execution inputs")
                cls._adjust_polling_interval(idle=False)
                
                cls._process_tasks(task_ids)
                
            except Exception as e:
                logger.error(f"Error in ExecutionInputHandler main loop: {e}")
                time.sleep(cls._current_polling_interval)
        
        logger.info("ExecutionInputHandler main loop stopped")

    @classmethod
    def _process_tasks(cls, task_ids: List[str]):
        """Task'ları işler: context oluşturur, payload hazırlar ve engine'e gönderir."""
        if not task_ids:
            return
        
        try:
            contexts = cls._create_contexts_batch(task_ids)
            
            if not contexts:
                logger.warning(f"No contexts created for {len(task_ids)} task IDs")
                return
            
            payloads, execution_input_ids = cls._prepare_payloads(contexts)
            
            if not payloads:
                logger.warning(f"No payloads prepared for {len(contexts)} contexts")
                return
            
            if len(payloads) != len(execution_input_ids):
                logger.warning(f"Payload count mismatch: {len(payloads)} payloads vs {len(execution_input_ids)} execution_input_ids")
                return
            
            try:
                cls._submit_to_engine(payloads)
                cls._remove_execution_inputs(execution_input_ids)
            except Exception as e:
                logger.error(f"Failed to submit payloads to engine, not removing execution inputs: {e}")
                raise
            
            logger.info(f"Successfully processed {len(payloads)} tasks")
            
        except Exception as e:
            logger.error(f"Error processing tasks: {e}")
            raise

    @classmethod
    def _create_contexts_batch(cls, task_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Paralel olarak execution context'leri oluşturur."""
        contexts = {}
        
        if cls.parallel_context and cls._worker_pool:
            future_to_id = {
                cls._worker_pool.submit(cls._create_single_context, task_id): task_id
                for task_id in task_ids
            }
            
            try:
                for future in as_completed(future_to_id.keys(), timeout=cls.context_timeout):
                    task_id = future_to_id[future]
                    try:
                        context = future.result(timeout=1.0)
                        if context:
                            contexts[task_id] = context
                    except Exception as e:
                        logger.error(f"Failed to create context for {task_id}: {e}")
            except FuturesTimeoutError:
                for future in future_to_id.keys():
                    if not future.done():
                        future.cancel()
                logger.warning(f"Timeout creating contexts. Created: {len(contexts)}/{len(task_ids)}")
        else:
            for task_id in task_ids:
                try:
                    context = cls._create_single_context(task_id)
                    if context:
                        contexts[task_id] = context
                except Exception as e:
                    logger.error(f"Failed to create context for {task_id}: {e}")
        
        return contexts

    @classmethod
    def _create_single_context(cls, execution_input_id: str) -> Optional[Dict[str, Any]]:
        """Tek bir execution context oluşturur."""
        try:
            context = SchedulerForInputHandler.create_execution_context(execution_input_id=execution_input_id)
            logger.debug(f"Created context for execution_input_id: {execution_input_id}")
            return context
        except Exception as e:
            logger.error(f"Failed to create context for execution_input_id {execution_input_id}: {e}")
            return None

    @classmethod
    def _prepare_payloads(cls, contexts: Dict[str, Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[str]]:
        """Context'leri engine payload'larına dönüştürür."""
        payloads = []
        execution_input_ids = []
        
        for execution_input_id, context in contexts.items():
            try:
                params = context.get('params', {})
                
                payload = {
                    'script_path': context.get('script_path'),
                    'params': params,
                    'execution_id': context.get('execution_id'),
                    'node_id': context.get('node_id'),
                    'max_retries': context.get('max_retries', 3),
                    'timeout_seconds': context.get('timeout_seconds', 300),
                    'process_type': 'iob'
                }
                
                if not payload['script_path']:
                    logger.error(f"Missing script_path in context for execution_input_id: {execution_input_id}")
                    continue
                
                payloads.append(payload)
                execution_input_ids.append(execution_input_id)
                
            except Exception as e:
                logger.error(f"Failed to prepare payload for execution_input_id {execution_input_id}: {e}")
                continue
        
        return payloads, execution_input_ids

    @classmethod
    def _submit_to_engine(cls, payloads: List[Dict[str, Any]]):
        """Engine'e batch olarak payload'ları gönderir."""
        if not payloads:
            return
        
        if not cls._engine_manager:
            raise ValueError("Engine manager is not initialized")
        
        for attempt in range(cls.max_retries):
            try:
                success = cls._engine_manager.put_items_bulk(payloads)
                
                if success:
                    logger.info(f"Successfully submitted {len(payloads)} payloads to engine")
                    return
                else:
                    if attempt < cls.max_retries - 1:
                        delay = cls.retry_delay * (attempt + 1)
                        logger.warning(f"Engine submission failed, retrying in {delay}s (attempt {attempt + 1}/{cls.max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        raise Exception(f"Failed to submit payloads to engine after {cls.max_retries} attempts")
                        
            except Exception as e:
                if attempt < cls.max_retries - 1:
                    delay = cls.retry_delay * (attempt + 1)
                    logger.warning(f"Engine submission error, retrying in {delay}s (attempt {attempt + 1}/{cls.max_retries}): {e}")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Failed to submit payloads to engine after {cls.max_retries} attempts: {e}")
                    raise

    @classmethod
    def _remove_execution_inputs(cls, execution_input_ids: List[str]):
        """Engine'e gönderilen execution input'ları siler."""
        if not execution_input_ids:
            return
        
        for attempt in range(cls.max_retries):
            try:
                deleted_count = SchedulerForInputHandler.remove_processed_execution_inputs(execution_input_ids=execution_input_ids)
                logger.info(f"Removed {deleted_count} execution inputs (attempt {attempt + 1})")
                return
            except Exception as e:
                if attempt < cls.max_retries - 1:
                    delay = cls.retry_delay * (attempt + 1)
                    logger.warning(f"Failed to remove execution inputs, retrying in {delay}s (attempt {attempt + 1}/{cls.max_retries}): {e}")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Failed to remove execution inputs after {cls.max_retries} attempts: {e}")
                    raise

    @classmethod
    def _adjust_polling_interval(cls, idle: bool):
        """Adaptive polling interval'ı ayarlar."""
        if not cls.adaptive_polling:
            return
        
        old_interval = cls._current_polling_interval
        
        if idle:
            new_interval = min(old_interval * 1.2, cls.max_polling_interval)
        else:
            new_interval = max(old_interval * 0.8, cls.min_polling_interval)
        
        if old_interval != new_interval:
            cls._current_polling_interval = new_interval
            logger.debug(f"Polling interval adjusted: {old_interval:.2f}s -> {new_interval:.2f}s")