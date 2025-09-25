import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logging(log_level: str = "INFO", log_file: str = None):
    """
    Set up logging configuration for the bot
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    # Create logs directory if needed
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    # Set up formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
    
    # Reduce noise from external libraries
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    
    return root_logger

class BotLogger:
    """Custom logger for bot-specific logging"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_user_action(self, user_id: int, action: str, details: str = None):
        """Log user actions with consistent format"""
        message = f"User {user_id} - {action}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
    
    def log_admin_action(self, admin_id: int, action: str, target: str = None):
        """Log admin actions"""
        message = f"Admin {admin_id} - {action}"
        if target:
            message += f" - Target: {target}"
        self.logger.info(message)
    
    def log_notification(self, user_id: int, notification_type: str, status: str):
        """Log notification events"""
        self.logger.info(f"Notification - Type: {notification_type}, User: {user_id}, Status: {status}")
    
    def log_error(self, error: Exception, context: str = None):
        """Log errors with context"""
        if context:
            self.logger.error(f"{context}: {str(error)}", exc_info=True)
        else:
            self.logger.error(str(error), exc_info=True)