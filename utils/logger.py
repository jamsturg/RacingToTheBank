import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import json
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

class CustomFormatter(logging.Formatter):
    """Custom formatter with color support and structured logging"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[41m', # Red background
    }
    RESET = '\033[0m'

    def __init__(self, include_timestamp: bool = True):
        self.include_timestamp = include_timestamp
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        # Add custom fields
        record.hostname = getattr(record, 'hostname', '-')
        record.environment = getattr(record, 'environment', 'development')
        
        # Create structured log entry
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'hostname': record.hostname,
            'environment': record.environment
        }

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Add custom fields from extra
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)

        # Color formatting for console output
        if sys.stdout.isatty():  # Only apply colors when outputting to terminal
            color = self.COLORS.get(record.levelname, '')
            return f"{color}{json.dumps(log_entry)}{self.RESET}"
        
        return json.dumps(log_entry)

class LoggerFactory:
    """Factory class for creating and configuring loggers"""
    
    @staticmethod
    def create_logger(
        name: str,
        level: str = 'INFO',
        log_file: Optional[str] = None,
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5,
        rotating_when: str = 'midnight',
        include_console: bool = True,
        structured: bool = True
    ) -> logging.Logger:
        """
        Create a configured logger instance
        
        Args:
            name: Logger name
            level: Logging level
            log_file: Path to log file (optional)
            max_bytes: Maximum size of each log file
            backup_count: Number of backup files to keep
            rotating_when: When to rotate logs ('midnight', 'W0', etc.)
            include_console: Whether to include console output
            structured: Whether to use structured logging format
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Remove existing handlers
        logger.handlers = []

        # Create formatters
        if structured:
            formatter = CustomFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        # Add console handler if requested
        if include_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # Add file handlers if log file specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Size-based rotation
            size_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            size_handler.setFormatter(formatter)
            logger.addHandler(size_handler)

            # Time-based rotation
            time_handler = TimedRotatingFileHandler(
                log_file,
                when=rotating_when,
                backupCount=backup_count
            )
            time_handler.setFormatter(formatter)
            logger.addHandler(time_handler)

        return logger

class LoggerAdapter(logging.LoggerAdapter):
    """Custom adapter for adding context to log messages"""
    
    def __init__(self, logger: logging.Logger, extra: dict = None):
        super().__init__(logger, extra or {})

    def process(self, msg: str, kwargs: dict) -> tuple:
        """Process the logging message and keyword arguments"""
        extra = kwargs.get('extra', {})
        if self.extra:
            extra.update(self.extra)
        kwargs['extra'] = extra
        return msg, kwargs

def get_logger(
    name: str,
    context: dict = None,
    **kwargs
) -> LoggerAdapter:
    """
    Get a configured logger with optional context
    
    Args:
        name: Logger name
        context: Additional context to include in logs
        **kwargs: Additional arguments for logger configuration
    """
    logger = LoggerFactory.create_logger(name, **kwargs)
    return LoggerAdapter(logger, context)

# Performance monitoring
class LoggerPerformanceMonitor:
    """Monitor and log performance metrics"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.start_times = {}

    def start_operation(self, operation_name: str):
        """Start timing an operation"""
        self.start_times[operation_name] = datetime.now()

    def end_operation(self, operation_name: str, extra_data: dict = None):
        """End timing an operation and log the duration"""
        if operation_name in self.start_times:
            duration = datetime.now() - self.start_times[operation_name]
            log_data = {
                'operation': operation_name,
                'duration_ms': duration.total_seconds() * 1000
            }
            if extra_data:
                log_data.update(extra_data)
            self.logger.info('Operation completed', extra={'performance': log_data})
            del self.start_times[operation_name]

# Example usage
if __name__ == '__main__':
    # Create logger with context
    logger = get_logger(
        'racing_app',
        context={'app_version': '1.0.0'},
        log_file='logs/racing_app.log',
        level='DEBUG'
    )

    # Create performance monitor
    perf_monitor = LoggerPerformanceMonitor(logger)

    # Example logging
    try:
        perf_monitor.start_operation('sample_operation')
        logger.info('Application started')
        logger.debug('Debug message', extra={'user_id': '123'})
        raise ValueError('Sample error')
    except Exception as e:
        logger.error('Error occurred', exc_info=True)
    finally:
        perf_monitor.end_operation('sample_operation', {'status': 'completed'})
