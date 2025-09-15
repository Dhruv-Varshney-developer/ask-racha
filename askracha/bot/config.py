"""
Configuration management system with environment variable validation.
"""
import os
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BotConfig:
    """Configuration class for Discord bot settings."""
    discord_token: str
    askracha_api_url: str
    api_timeout: int
    max_response_length: int
    log_level: str
    retry_attempts: int
    retry_delay: float


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


def load_config() -> BotConfig:
    """
    Load and validate configuration from environment variables.
    
    Returns:
        BotConfig: Validated configuration object
        
    Raises:
        ConfigurationError: If required configuration is missing or invalid
    """
    # Required configuration
    discord_token = os.getenv('DISCORD_TOKEN')
    if not discord_token:
        raise ConfigurationError("DISCORD_TOKEN environment variable is required")
    
    # Optional configuration with defaults
    askracha_api_url = os.getenv('ASKRACHA_API_URL', 'http://localhost:5000')
    
    # Validate and convert numeric values
    try:
        api_timeout = int(os.getenv('API_TIMEOUT', '10'))
        if api_timeout <= 0:
            raise ValueError("API_TIMEOUT must be positive")
    except ValueError as e:
        raise ConfigurationError(f"Invalid API_TIMEOUT: {e}")
    
    try:
        max_response_length = int(os.getenv('MAX_RESPONSE_LENGTH', '2000'))
        if max_response_length <= 0:
            raise ValueError("MAX_RESPONSE_LENGTH must be positive")
    except ValueError as e:
        raise ConfigurationError(f"Invalid MAX_RESPONSE_LENGTH: {e}")
    
    try:
        retry_attempts = int(os.getenv('RETRY_ATTEMPTS', '3'))
        if retry_attempts < 0:
            raise ValueError("RETRY_ATTEMPTS must be non-negative")
    except ValueError as e:
        raise ConfigurationError(f"Invalid RETRY_ATTEMPTS: {e}")
    
    try:
        retry_delay = float(os.getenv('RETRY_DELAY', '1.0'))
        if retry_delay < 0:
            raise ValueError("RETRY_DELAY must be non-negative")
    except ValueError as e:
        raise ConfigurationError(f"Invalid RETRY_DELAY: {e}")
    
    # Validate log level
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if log_level not in valid_levels:
        raise ConfigurationError(f"Invalid LOG_LEVEL: {log_level}. Must be one of {valid_levels}")
    
    # Validate API URL format
    if not askracha_api_url.startswith(('http://', 'https://')):
        raise ConfigurationError("ASKRACHA_API_URL must start with http:// or https://")
    
    logger.info("Configuration loaded successfully")
    logger.debug(f"API URL: {askracha_api_url}")
    logger.debug(f"API Timeout: {api_timeout}s")
    logger.debug(f"Max Response Length: {max_response_length}")
    logger.debug(f"Retry Attempts: {retry_attempts}")
    logger.debug(f"Retry Delay: {retry_delay}s")
    
    return BotConfig(
        discord_token=discord_token,
        askracha_api_url=askracha_api_url,
        api_timeout=api_timeout,
        max_response_length=max_response_length,
        log_level=log_level,
        retry_attempts=retry_attempts,
        retry_delay=retry_delay
    )


def validate_startup_config() -> None:
    """
    Validate configuration at startup and log any issues.
    
    Raises:
        ConfigurationError: If configuration validation fails
    """
    try:
        config = load_config()
        logger.info("✅ Configuration validation passed")
        return config
    except ConfigurationError as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during configuration validation: {e}")
        raise ConfigurationError(f"Unexpected configuration error: {e}")