"""
Logging Configuration Module
Centralized logging setup for the Crypto Intelligence Pipeline
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(log_level: str = "INFO", log_to_file: bool = True, log_dir: str = "logs") -> logging.Logger:
    """
    Setup centralized logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_dir: Directory for log files
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if needed
    if log_to_file:
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger("crypto_intelligence")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter with timestamp, level, and module info
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_to_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_path / f"crypto_pipeline_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"Log file created: {log_file}")
    
    return logger


# Create a default logger instance
logger = setup_logging()


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance with optional custom name.
    
    Args:
        name: Optional logger name (creates child logger)
        
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"crypto_intelligence.{name}")
    return logger
