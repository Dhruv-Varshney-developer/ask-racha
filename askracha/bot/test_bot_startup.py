#!/usr/bin/env python3
"""
Test bot startup and configuration validation.
"""
import asyncio
import sys
import os
from unittest.mock import patch, MagicMock

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import BotConfig, load_config, ConfigurationError
from api_client import APIClient
from message_processor import MessageProcessor
from bot import DiscordBot


async def test_configuration_loading():
    """Test configuration loading and validation."""
    print("Testing configuration loading...")
    
    # Test with environment variables
    test_env = {
        'DISCORD_TOKEN': 'test_token_123',
        'ASKRACHA_API_URL': 'http://localhost:5000',
        'API_TIMEOUT': '15',
        'MAX_RESPONSE_LENGTH': '1800',
        'LOG_LEVEL': 'DEBUG',
        'RETRY_ATTEMPTS': '2',
        'RETRY_DELAY': '0.5'
    }
    
    with patch.dict(os.environ, test_env):
        config = load_config()
        
        assert config.discord_token == 'test_token_123'
        assert config.askracha_api_url == 'http://localhost:5000'
        assert config.api_timeout == 15
        assert config.max_response_length == 1800
        assert config.log_level == 'DEBUG'
        assert config.retry_attempts == 2
        assert config.retry_delay == 0.5
    
    print("✅ Configuration loading test passed")


async def test_bot_component_integration():
    """Test that all bot components work together."""
    print("Testing bot component integration...")
    
    # Create configuration
    config = BotConfig(
        discord_token="test_token",
        askracha_api_url="http://localhost:5000",
        api_timeout=10,
        max_response_length=2000,
        log_level="INFO",
        retry_attempts=3,
        retry_delay=1.0
    )
    
    # Create components
    api_client = APIClient(
        api_url=config.askracha_api_url,
        timeout=config.api_timeout,
        retry_attempts=config.retry_attempts,
        retry_delay=config.retry_delay
    )
    
    message_processor = MessageProcessor(
        max_response_length=config.max_response_length
    )
    
    # Test that components can be created and configured
    assert api_client.api_url == "http://localhost:5000"
    assert api_client.timeout == 10
    assert message_processor.max_response_length == 2000
    
    # Clean up
    await api_client.close()
    
    print("✅ Bot component integration test passed")


async def test_error_handling():
    """Test error handling scenarios."""
    print("Testing error handling...")
    
    # Test missing Discord token
    with patch.dict(os.environ, {}, clear=True):
        try:
            load_config()
            assert False, "Should have raised ConfigurationError"
        except ConfigurationError as e:
            assert "DISCORD_TOKEN" in str(e)
    
    # Test invalid API timeout
    with patch.dict(os.environ, {'DISCORD_TOKEN': 'test', 'API_TIMEOUT': 'invalid'}):
        try:
            load_config()
            assert False, "Should have raised ConfigurationError"
        except ConfigurationError as e:
            assert "API_TIMEOUT" in str(e)
    
    print("✅ Error handling test passed")


async def test_graceful_error_responses():
    """Test that bot provides graceful error responses."""
    print("Testing graceful error responses...")
    
    # Create a minimal bot instance for testing
    config = BotConfig(
        discord_token="test_token",
        askracha_api_url="http://localhost:5000",
        api_timeout=10,
        max_response_length=2000,
        log_level="INFO",
        retry_attempts=3,
        retry_delay=1.0
    )
    
    api_client = APIClient(
        api_url=config.askracha_api_url,
        timeout=config.api_timeout,
        retry_attempts=config.retry_attempts,
        retry_delay=config.retry_delay
    )
    
    message_processor = MessageProcessor(
        max_response_length=config.max_response_length
    )
    
    # Create bot instance (without actually initializing Discord connection)
    bot = DiscordBot.__new__(DiscordBot)
    bot.config = config
    bot.api_client = api_client
    bot.message_processor = message_processor
    
    # Test error response categorization
    timeout_response = bot._get_error_response("Request timeout")
    assert "taking longer than usual" in timeout_response
    assert "⏱️" in timeout_response
    
    connection_response = bot._get_error_response("Connection failed")
    assert "trouble connecting" in connection_response
    assert "🔧" in connection_response
    
    rate_limit_response = bot._get_error_response("Rate limit exceeded")
    assert "lot of questions" in rate_limit_response
    assert "🚦" in rate_limit_response
    
    # Clean up
    await api_client.close()
    
    print("✅ Graceful error responses test passed")


async def main():
    """Run all startup tests."""
    print("🚀 Running Discord Bot Startup Tests")
    print("=" * 50)
    
    try:
        await test_configuration_loading()
        await test_bot_component_integration()
        await test_error_handling()
        await test_graceful_error_responses()
        
        print("=" * 50)
        print("🎉 All startup tests passed!")
        print("✅ Discord bot is ready for deployment!")
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)