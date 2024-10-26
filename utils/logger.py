import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
import streamlit as st
from typing import Optional, Dict, Any
import json
import traceback

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging formats
CONSOLE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"

# Log file paths
BACKEND_LOG = LOGS_DIR / "backend.log"
FRONTEND_LOG = LOGS_DIR / "frontend.log"
API_LOG = LOGS_DIR / "api.log"
ERROR_LOG = LOGS_DIR / "error.log"

class StreamlitHandler(logging.Handler):
    """Custom logging handler that writes to Streamlit"""
    
    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelname.lower()
            
            if hasattr(st, level):
                getattr(st, level)(msg)
            else:
                st.write(msg)
                
        except Exception:
            self.handleError(record)

class JsonFormatter(logging.Formatter):
    """Formatter that outputs JSON strings after gathering all the attributes from the log record"""
    
    def format(self, record):
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        
        json_record = {
            "timestamp": timestamp,
            "level": record.levelname,
            "name": record.name,
            "file": record.filename,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        
        if hasattr(record, "request_id"):
            json_record["request_id"] = record.request_id
            
        if record.exc_info:
            json_record["exception"] = traceback.format_exception(*record.exc_info)
            
        if hasattr(record, "extra_data"):
            json_record["extra_data"] = record.extra_data
            
        return json.dumps(json_record)

def setup_logger(
    name: str,
    log_file: Path,
    level: int = logging.INFO,
    rotation: str = "midnight",
    retention: int = 30,
    format_type: str = "standard"
) -> logging.Logger:
    """Setup a logger with file and console handlers"""
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear any existing handlers
    logger.handlers = []
    
    # File handler with rotation
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_file,
        when=rotation,
        interval=1,
        backupCount=retention,
        encoding="utf-8"
    )
    
    # Choose formatter based on format_type
    if format_type == "json":
        file_formatter = JsonFormatter()
    else:
        file_formatter = logging.Formatter(FILE_FORMAT)
        
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(CONSOLE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger

# Setup main loggers
backend_logger = setup_logger("backend", BACKEND_LOG)
frontend_logger = setup_logger("frontend", FRONTEND_LOG)
api_logger = setup_logger("api", API_LOG, format_type="json")
error_logger = setup_logger("error", ERROR_LOG, level=logging.ERROR)

class LoggerMixin:
    """Mixin to add logging capabilities to any class"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def log_method_call(self, method_name: str, *args, **kwargs):
        """Log method calls with arguments"""
        self.logger.debug(
            f"Calling {method_name} with args={args} kwargs={kwargs}"
        )
        
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log errors with context"""
        error_logger.error(
            f"Error in {self.__class__.__name__}",
            exc_info=error,
            extra={"context": context}
        )

def log_execution_time(logger):
    """Decorator to log execution time of functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.debug(
                    f"{func.__name__} executed in {execution_time:.2f} seconds"
                )
                return result
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.error(
                    f"{func.__name__} failed after {execution_time:.2f} seconds",
                    exc_info=e
                )
                raise
        return wrapper
    return decorator
