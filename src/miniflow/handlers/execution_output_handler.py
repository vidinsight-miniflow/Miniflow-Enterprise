import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from typing import Dict, Any, List, Optional

from ..utils import ConfigurationHandler
from ..services import SchedulerForOutputHandler
from ..core.logger import get_logger


logger = get_logger(__name__)


class ExecutionOutputHandler:
    """
    Execution output handler: Engine'den gelen execution result'ları alır ve işler.
    
    Lifecycle:
    1. start() -> Handler'ı başlatır (main loop thread'i başlar)
    2. _main_loop() -> Sürekli çalışan ana döngü
       - get_execution_results() -> Engine'den result'ları getirir
       - _process_results() -> Result'ları işler
       - _process_results_batch() -> Result'ları batch olarak işler (paralel)
       - process_execution_result() -> Her result'ı scheduler'a gönderir
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
    result_timeout: float = 60.0
    min_polling_interval: float = 0.1
    max_polling_interval: float = 5.0
    retry_delay: float = 1.0
    adaptive_polling: bool = True
    parallel_processing: bool = True

    @classmethod
    def _load_config(cls):
        """Config dosyasından ayarları yükler."""
        if cls._initialized:
            return
        
        try:
            ConfigurationHandler.ensure_loaded()
            section = "OUTPUT_HANDLER"
            
            cls.batch_size = ConfigurationHandler.get_int(section, "output_handler_batch_size", fallback=50)
            cls.worker_threads = ConfigurationHandler.get_int(section, "output_handler_worker_threads", fallback=4)
            cls.max_retries = ConfigurationHandler.get_int(section, "output_handler_max_retries", fallback=3)
            cls.result_timeout = ConfigurationHandler.get_float(section, "output_handler_result_timeout", fallback=60.0)
            cls.min_polling_interval = ConfigurationHandler.get_float(section, "output_handler_min_polling_interval", fallback=0.1)
            cls.max_polling_interval = ConfigurationHandler.get_float(section, "output_handler_max_polling_interval", fallback=5.0)
            cls.retry_delay = ConfigurationHandler.get_float(section, "output_handler_retry_delay", fallback=1.0)
            cls.adaptive_polling = ConfigurationHandler.get_bool(section, "output_handler_adaptive_polling", fallback=True)
            cls.parallel_processing = ConfigurationHandler.get_bool(section, "output_handler_parallel_processing", fallback=True)
            
            cls._initialized = True
            logger.info(f"ExecutionOutputHandler config loaded: batch_size={cls.batch_size}, worker_threads={cls.worker_threads}")
            
        except Exception as e:
            logger.error(f"Failed to load ExecutionOutputHandler config: {e}")
            raise

    @classmethod
    def start(cls, engine_manager):
        """Handler'ı başlatır ve main loop thread'ini başlatır."""
        if cls._running:
            logger.warning("ExecutionOutputHandler is already running")
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
                thread_name_prefix="ExecutionOutputHandlerWorker"
            )
            
            cls._current_polling_interval = cls.min_polling_interval
            cls._running = True
            
            cls._main_thread = threading.Thread(
                target=cls._main_loop,
                name="ExecutionOutputHandlerThread",
                daemon=True
            )
            cls._main_thread.start()
            
            logger.info("ExecutionOutputHandler started successfully")
            return True
            
        except Exception as e:
            cls._running = False
            logger.error(f"Failed to start ExecutionOutputHandler: {e}")
            raise

    @classmethod
    def stop(cls):
        """Handler'ı durdurur ve kaynakları temizler."""
        if not cls._running:
            return True
        
        try:
            logger.info("Stopping ExecutionOutputHandler...")
            cls._shutdown_event.set()
            
            if cls._worker_pool:
                cls._worker_pool.shutdown(wait=True)
                cls._worker_pool = None
            
            if cls._main_thread and cls._main_thread.is_alive():
                cls._main_thread.join(timeout=10)
            
            # Grace period for active transactions to complete
            time.sleep(0.5)
            
            cls._running = False
            logger.info("ExecutionOutputHandler stopped successfully")
            return True
            
        except Exception as e:
            cls._running = False
            logger.error(f"Error stopping ExecutionOutputHandler: {e}")
            raise

    @classmethod
    def _main_loop(cls):
        """Ana döngü: sürekli olarak engine'den execution result'ları kontrol eder ve işler."""
        logger.info("ExecutionOutputHandler main loop started")
        
        while cls._running and not cls._shutdown_event.is_set():
            try:
                results = cls._engine_manager.get_execution_results(max_items=cls.batch_size, timeout=0.1)
                
                if not results:
                    cls._adjust_polling_interval(idle=True)
                    time.sleep(cls._current_polling_interval)
                    continue
                
                logger.debug(f"Found {len(results)} execution results from engine")
                cls._adjust_polling_interval(idle=False)
                
                cls._process_results(results)
                
            except Exception as e:
                logger.error(f"Error in ExecutionOutputHandler main loop: {e}")
                time.sleep(cls._current_polling_interval)
        
        logger.info("ExecutionOutputHandler main loop stopped")

    @classmethod
    def _process_results(cls, results: List[Dict[str, Any]]):
        """Result'ları işler: scheduler'a gönderir."""
        if not results:
            return
        
        try:
            cls._process_results_batch(results)
            logger.info(f"Successfully processed {len(results)} execution results")
            
        except Exception as e:
            logger.error(f"Error processing results: {e}")
            raise

    @classmethod
    def _process_results_batch(cls, results: List[Dict[str, Any]]):
        """Paralel olarak execution result'ları işler."""
        if not results:
            return
        
        if cls.parallel_processing and cls._worker_pool:
            future_to_result = {
                cls._worker_pool.submit(cls._process_single_result, result): result
                for result in results
            }
            
            try:
                for future in as_completed(future_to_result.keys(), timeout=cls.result_timeout):
                    result = future_to_result[future]
                    try:
                        future.result(timeout=1.0)
                    except Exception as e:
                        logger.error(f"Failed to process result for execution_id={result.get('execution_id')}, node_id={result.get('node_id')}: {e}")
            except FuturesTimeoutError:
                for future in future_to_result.keys():
                    if not future.done():
                        future.cancel()
                logger.warning(f"Timeout processing results. Processed: {len([f for f in future_to_result.keys() if f.done()])}/{len(results)}")
        else:
            for result in results:
                try:
                    cls._process_single_result(result)
                except Exception as e:
                    logger.error(f"Failed to process result for execution_id={result.get('execution_id')}, node_id={result.get('node_id')}: {e}")

    @classmethod
    def _process_single_result(cls, result: Dict[str, Any]):
        """Tek bir execution result'ı işler."""
        try:
            execution_id = result.get('execution_id')
            node_id = result.get('node_id')
            status = result.get('status')
            
            if not execution_id or not node_id or not status:
                logger.error(f"Invalid result format: missing execution_id, node_id, or status")
                return
            
            processed_result = SchedulerForOutputHandler.process_execution_result(result=result)
            logger.debug(f"Processed result for execution_id={execution_id}, node_id={node_id}, status={status}")
            
        except Exception as e:
            logger.error(f"Failed to process result for execution_id={result.get('execution_id')}, node_id={result.get('node_id')}: {e}")
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