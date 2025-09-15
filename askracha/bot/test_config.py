"""
Simple test script to verify configuration system.
Run with: python test_config.py
"""
import os
import sys
from pathlib import Path

# Add bot directory to path
bot_dir = Path(__file__).parent
sys.path.insert(0, str(bot_dir))

def test_config():
    """Test the configuration system."""
    print("🧪 Testing configuration system...")
    
    # Test missing required config
    print("\n1. Testing missing DISCORD_TOKEN...")
    try:
        from config import load_config, ConfigurationError
        
        # Clear any existing token
        if 'DISCORD_TOKEN' in os.environ:
            del os.environ['DISCORD_TOKEN']
        
        config = load_config()
        print("❌ Should have failed with missing token")
        return False
    except ConfigurationError as e:
        print(f"✅ Correctly caught missing token: {e}")
    
    # Test valid config
    print("\n2. Testing valid configuration...")
    try:
        os.environ['DISCORD_TOKEN'] = 'test_token_123'
        config = load_config()
        print(f"✅ Configuration loaded successfully")
        print(f"   - Discord Token: {'*' * len(config.discord_token)}")
        print(f"   - API URL: {config.askracha_api_url}")
        print(f"   - API Timeout: {config.api_timeout}s")
        print(f"   - Log Level: {config.log_level}")
        print(f"   - Retry Attempts: {config.retry_attempts}")
        print(f"   - Retry Delay: {config.retry_delay}s")
    except Exception as e:
        print(f"❌ Failed to load valid config: {e}")
        return False
    
    # Test invalid numeric values
    print("\n3. Testing invalid numeric values...")
    try:
        os.environ['API_TIMEOUT'] = 'invalid'
        config = load_config()
        print("❌ Should have failed with invalid timeout")
        return False
    except ConfigurationError as e:
        print(f"✅ Correctly caught invalid timeout: {e}")
    
    # Clean up
    os.environ['API_TIMEOUT'] = '10'  # Reset to valid value
    
    print("\n✅ All configuration tests passed!")
    return True


def test_logging():
    """Test the logging system."""
    print("\n🧪 Testing logging system...")
    
    try:
        from logger import setup_logging
        import logging
        
        # Set up logging
        bot_logger = setup_logging('INFO')
        logger = logging.getLogger('test')
        
        # Test different log levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        # Test structured logging
        from logger import BotLogger
        BotLogger.log_bot_event('test_event', test_param='test_value')
        
        print("✅ Logging system working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Running configuration and logging tests...\n")
    
    config_ok = test_config()
    logging_ok = test_logging()
    
    if config_ok and logging_ok:
        print("\n🎉 All tests passed! Configuration system is ready.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Please check the implementation.")
        sys.exit(1)