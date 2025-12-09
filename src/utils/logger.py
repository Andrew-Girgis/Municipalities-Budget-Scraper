"""Logger configuration for the municipalities budget scraper."""
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager


def setup_logger(name: str = "municipalities_scraper", log_level: str = "INFO") -> logging.Logger:
    """
    Set up and configure logger for the application.
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # File handler - detailed logs
    log_file = log_dir / f"scraper_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler - simpler output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


@contextmanager
def log_time(logger: logging.Logger, operation: str, level: int = logging.INFO):
    """
    Context manager for logging operation duration.
    
    Args:
        logger: Logger instance to use
        operation: Description of the operation being timed
        level: Logging level for the completion message
    
    Example:
        with log_time(logger, "PDF extraction"):
            text = extract_pdf_text(path)
    """
    start = time.time()
    yield
    duration = time.time() - start
    logger.log(level, f"{operation} completed in {duration:.2f}s")
