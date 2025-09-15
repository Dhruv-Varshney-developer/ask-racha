"""
Centralized logging configuration with structured output.
"""
import logging
import logging.handlers
import sys
import json
from datetime import datetime
from typing import Dict, Any
import os


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)


class BotLogger:
    """Centralized logger for the Discord bot."""
    
    def __init__(self, log_level: str = 'INFO'):
        self.log_level = log_level
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configure logging with structured output."""
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler with structured format
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.log_level))
        console_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(console_handler)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, 'bot.log'),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # Always log debug to file
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, 'error.log'),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(error_handler)
        
        # Suppress discord.py debug logs unless we're in debug mode
        if self.log_level != 'DEBUG':
            logging.getLogger('discord').setLevel(logging.WARNING)
            logging.getLogger('discord.http').setLevel(logging.WARNING)
        
        logging.info("Logging system initialized", extra={
            'extra_fields': {
                'log_level': self.log_level,
                'log_directory': log_dir
            }
        })
    
    @staticmethod
    def log_bot_event(event_type: str, **kwargs) -> None:
        """Log bot-specific events with structured data."""
        logger = logging.getLogger('bot.events')
        logger.info(f"Bot event: {event_type}", extra={
            'extra_fields': {
                'event_type': event_type,
                **kwargs
            }
        })
    
    @staticmethod
    def log_message_processing(user_id: str, channel_id: str, question: str, 
                             response_time: float = None, success: bool = None) -> None:
        """Log message processing events."""
        logger = logging.getLogger('bot.messages')
        extra_fields = {
            'user_id': user_id,
            'channel_id': channel_id,
            'question_length': len(question),
            'question_preview': question[:100] + '...' if len(question) > 100 else question
        }
        
        if response_time is not None:
            extra_fields['response_time'] = response_time
        if success is not None:
            extra_fields['success'] = success
        
        logger.info("Message processed", extra={'extra_fields': extra_fields})
    
    @staticmethod
    def log_api_request(endpoint: str, response_time: float, status_code: int, 
                       success: bool, error: str = None) -> None:
        """Log API request events."""
        logger = logging.getLogger('bot.api')
        extra_fields = {
            'endpoint': endpoint,
            'response_time': response_time,
            'status_code': status_code,
            'success': success
        }
        
        if error:
            extra_fields['error'] = error
        
        level = logging.INFO if success else logging.ERROR
        message = f"API request to {endpoint}"
        logger.log(level, message, extra={'extra_fields': extra_fields})
    
    @staticmethod
    def log_performance_metrics(questions_processed: int, successful_responses: int,
                              failed_responses: int, average_response_time: float) -> None:
        """Log performance metrics."""
        logger = logging.getLogger('bot.metrics')
        logger.info("Performance metrics", extra={
            'extra_fields': {
                'questions_processed': questions_processed,
                'successful_responses': successful_responses,
                'failed_responses': failed_responses,
                'success_rate': successful_responses / max(questions_processed, 1),
                'average_response_time': average_response_time
            }
        })


def setup_logging(log_level: str = 'INFO') -> BotLogger:
    """
    Set up logging configuration for the bot.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        BotLogger: Configured logger instance
    """
    return BotLogger(log_level)