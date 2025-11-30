"""
Simple logger implementation for testing
"""
import logging
import sys

_loggers = {}

def get_logger(name: str) -> logging.Logger:
    """Get or create a logger instance"""
    if name not in _loggers:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        
        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        _loggers[name] = logger
    
    return _loggers[name]

