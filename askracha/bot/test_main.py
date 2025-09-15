"""
Test script to verify main.py startup without running indefinitely.
"""
import os
import sys
import asyncio
from pathlib import Path

# Add bot directory to path
bot_dir = Path(__file__).parent
sys.path.insert(0, str(bot_dir))

async def test_startup():
    """Test the main startup sequence."""
    print("🧪 Testing main startup sequence...")
    
    try:
        # Set required environment variable
        os.environ['DISCORD_TOKEN'] = 'test_token_for_startup'
        
        # Import and test configuration loading
        from config import validate_startup_config
        from logger import setup_logging
        
        print("1. Testing configuration validation...")
        config = validate_startup_config()
        print("✅ Configuration validation passed")
        
        print("2. Testing logging setup...")
        bot_logger = setup_logging(config.log_level)
        print("✅ Logging setup completed")
        
        print("3. Testing main imports...")
        import main
        print("✅ Main module imports successfully")
        
        print("\n🎉 Startup sequence test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_startup())
    sys.exit(0 if result else 1)