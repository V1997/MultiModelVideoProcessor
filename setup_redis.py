#!/usr/bin/env python3
"""
Setup script for Redis integration
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def check_redis_url():
    """Check if Redis URL is configured"""
    load_dotenv()
    redis_url = os.getenv('REDIS_URL')
    
    if not redis_url:
        print("❌ REDIS_URL not found in .env file")
        print("\n💡 Add this to your .env file:")
        print("REDIS_URL=redis://localhost:6379")
        return False
    
    print(f"✅ Redis URL configured: {redis_url}")
    return True

def check_redis_connection():
    """Test Redis connection"""
    try:
        import redis
        load_dotenv()
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        r = redis.from_url(redis_url)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except ImportError:
        print("❌ Redis package not installed")
        print("   Run: pip install redis")
        return False
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("\n💡 Make sure Redis is running:")
        print("   Windows: Download from https://github.com/microsoftarchive/redis/releases")
        print("   Linux/Mac: sudo apt install redis-server / brew install redis")
        return False

def check_celery():
    """Check if Celery is available"""
    try:
        import celery
        print("✅ Celery package available")
        return True
    except ImportError:
        print("❌ Celery package not installed")
        print("   Run: pip install celery")
        return False

def install_requirements():
    """Install required packages"""
    print("\n📦 Installing Redis integration requirements...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "redis", "celery"
        ], check=True)
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def create_env_template():
    """Create .env template if it doesn't exist"""
    env_path = Path(".env")
    
    if env_path.exists():
        print("✅ .env file exists")
        return True
    
    print("📝 Creating .env template...")
    
    env_template = """# Database
DATABASE_URL=postgresql://username:password@localhost:5432/multimodelvideo

# Redis (for caching and background tasks)
REDIS_URL=redis://localhost:6379

# OpenAI API (optional, for advanced features)
OPENAI_API_KEY=your_openai_api_key_here

# YouTube API (optional, for video search)
YOUTUBE_API_KEY=your_youtube_api_key_here
"""
    
    try:
        env_path.write_text(env_template)
        print("✅ .env template created")
        print("⚠️  Please update the values in .env file")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env template: {e}")
        return False

def show_startup_instructions():
    """Show instructions for starting the system"""
    print("\n🚀 Startup Instructions:")
    print("=" * 40)
    print("1. Make sure Redis is running on your system")
    print("2. Start the Celery worker:")
    print("   python start_celery_worker.py")
    print("3. Start the API server:")
    print("   uvicorn backend.api.main:app --reload")
    print("4. Check system status:")
    print("   python check_system_status.py")
    print("5. Run integration tests:")
    print("   python test_redis_integration.py")

def main():
    """Main setup function"""
    print("🔧 Redis Integration Setup")
    print("=" * 30)
    
    # Check environment file
    env_ok = create_env_template()
    
    # Check Redis URL configuration
    redis_url_ok = check_redis_url()
    
    # Check and install requirements
    if not check_celery():
        install_ok = install_requirements()
        if not install_ok:
            print("\n❌ Setup failed - could not install requirements")
            return False
    
    # Check Redis connection
    redis_ok = check_redis_connection()
    
    # Summary
    print("\n📊 Setup Summary:")
    print(f"   Environment file: {'✅' if env_ok else '❌'}")
    print(f"   Redis URL config: {'✅' if redis_url_ok else '❌'}")
    print(f"   Redis connection: {'✅' if redis_ok else '❌'}")
    print(f"   Python packages: ✅")
    
    if redis_url_ok and redis_ok:
        print("\n🎉 Redis integration setup complete!")
        show_startup_instructions()
        return True
    else:
        print("\n⚠️  Setup incomplete - please address the issues above")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
