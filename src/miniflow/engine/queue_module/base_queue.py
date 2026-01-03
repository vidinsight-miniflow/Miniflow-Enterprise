import multiprocessing
import json
import queue
import time
from miniflow.core.logger import get_logger

# Logger instance
logger = get_logger(__name__)


class BaseQueue:
    def __init__(self, maxsize=1000):  # Increased from 100 to 1000
        self.q = multiprocessing.Queue(maxsize=maxsize)
        self.dropped_items = 0  # Track dropped items for monitoring

    def put(self, item: json):
        """Enhanced put with better error handling"""
        try:
            self.q.put_nowait(item)
            return True
        except queue.Full:
            self.dropped_items += 1
            logger.warning(f"Queue full, item dropped (total dropped: {self.dropped_items})")
            return False
        except Exception as e:
            self.dropped_items += 1
            logger.error(f"Put failed: {e}", exc_info=True)
            return False
    
    def put_with_retry(self, item: json, max_retries=3, retry_delay=0.1):
        """Put with retry mechanism"""
        for attempt in range(max_retries):
            if self.put(item):
                return True
            
            if attempt < max_retries - 1:  # Don't sleep on last attempt
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
        
        # Final attempt with blocking put
        try:
            self.q.put(item, timeout=1.0)
            return True
        except Exception as e:
            self.dropped_items += 1
            logger.critical(f"Queue full after 3 retries, item dropped: {e}", exc_info=True)
            return False
    
    def put_batch(self, items: list, max_retries: int = 3, retry_delay: float = 0.1):
        """
        Batch put operation with retry mechanism.
        Requires 100% success - all items must be successfully added to queue.
        
        Args:
            items: List of items to add to queue
            max_retries: Maximum number of retry attempts per item
            retry_delay: Initial delay between retries (exponential backoff)
        
        Returns:
            bool: True if ALL items were successfully added, False otherwise
        """
        if not items:
            return True
        
        failed_items = []
        
        for item in items:
            success = False
            for attempt in range(max_retries):
                if self.put(item):
                    success = True
                    break
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
            
            if not success:
                failed_items.append(item)
        
        if failed_items:
            logger.error(f"Failed to add {len(failed_items)}/{len(items)} items to queue after {max_retries} retries")
            return False
        
        return True

    def get_with_timeout(self, timeout=1.0):
        """Get with timeout - safer version"""
        try:
            return self.q.get(timeout=timeout)
        except queue.Empty:
            return None
        except Exception as e:
            logger.error(f"Get with timeout failed: {e}", exc_info=True)
            return None

    def get(self):
        """Legacy get method - kept for compatibility"""
        try:
            item = self.q.get_nowait()
            return item
        except queue.Empty:
            return None
        except Exception as e:
            logger.error(f"Get error: {e}", exc_info=True)
            return None

    def get_without_task(self):
        return self.get()

    def is_empty(self):
        return self.q.empty()

    def size(self):
        """Get queue size with error handling"""
        try:
            return self.q.qsize()
        except Exception:
            return 0

    def qsize(self):
        """Alias for size() - compatibility"""
        return self.size()

    def get_stats(self):
        """Get queue statistics"""
        try:
            size = self.q.qsize()
        except:
            size = -1  # Unknown size
        
        return {
            'size': size,
            'dropped_items': self.dropped_items,
            'is_empty': size == 0 if size >= 0 else False
        }


