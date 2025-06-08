#!/usr/bin/env python3
"""
Script to monitor Redis and Celery status
"""

import os
import sys
from pathlib import Path
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.services.redis_service import is_redis_available, get_redis_service
from backend.services.celery_app import celery_app

async def check_api_health():
    """Check API health endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                print("✅ API Health Check: OK")
                print(f"   Database: {'✅' if data.get('database') == 'connected' else '❌'}")
                print(f"   Redis: {'✅' if data.get('redis') == 'connected' else '❌'}")
                return True
            else:
                print(f"❌ API Health Check: Failed (Status: {response.status_code})")
                return False
    except Exception as e:
        print(f"❌ API Health Check: Failed ({str(e)})")
        return False

def check_redis():
    """Check Redis connection"""
    try:
        if is_redis_available():
            redis_service = get_redis_service()
            stats = redis_service.get_redis_stats()
            print("✅ Redis: Connected")
            print(f"   Memory: {stats.get('used_memory_human', 'unknown')}")
            print(f"   Sessions DB: {stats.get('sessions_db_keys', 0)} keys")
            print(f"   Cache DB: {stats.get('cache_db_keys', 0)} keys")
            return True
        else:
            print("❌ Redis: Not available")
            return False
    except Exception as e:
        print(f"❌ Redis: Failed ({str(e)})")
        return False

def check_celery():
    """Check Celery worker status"""
    try:
        # Check if workers are active
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print(f"✅ Celery: {len(active_workers)} worker(s) active")
            for worker, tasks in active_workers.items():
                print(f"   Worker {worker}: {len(tasks)} active task(s)")
        else:
            print("⚠️  Celery: No active workers found")
            
        # Check registered tasks
        registered = inspect.registered()
        if registered:
            worker_name = list(registered.keys())[0]
            tasks = registered[worker_name]
            print(f"   Registered tasks: {len(tasks)}")
            for task in sorted(tasks):
                if task.startswith(('video.', 'youtube.', 'embeddings.', 'visual.')):
                    print(f"     • {task}")
        
        return bool(active_workers)
    except Exception as e:
        print(f"❌ Celery: Failed ({str(e)})")
        return False

async def main():
    """Main monitoring function"""
    print("🔍 MultiModelVideo System Status Check")
    print("=" * 50)
    
    # Check individual components
    redis_ok = check_redis()
    print()
    
    celery_ok = check_celery()
    print()
    
    api_ok = await check_api_health()
    print()
    
    # Overall status
    print("📊 Overall Status:")
    if redis_ok and celery_ok and api_ok:
        print("✅ All systems operational")
        exit_code = 0
    elif api_ok:
        print("⚠️  API running but background services may be limited")
        exit_code = 1
    else:
        print("❌ System issues detected")
        exit_code = 2
    
    print("\n💡 Tips:")
    if not redis_ok:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        print(f"   • Start Redis server (configured: {redis_url})")
    if not celery_ok:
        print("   • Start Celery worker: python start_celery_worker.py")
    if not api_ok:
        print("   • Start API server: uvicorn backend.api.main:app --reload")
    
    return exit_code

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
