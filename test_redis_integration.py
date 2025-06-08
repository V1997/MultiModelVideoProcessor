#!/usr/bin/env python3
"""
Test script for Redis integration with background tasks
"""

import os
import sys
import asyncio
import time
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

API_BASE = "http://localhost:8000"

async def test_redis_health():
    """Test Redis health endpoints"""
    print("\n🔍 Testing Redis Health...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test overall health
            response = await client.get(f"{API_BASE}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check: {data}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
            
            # Test Redis status
            response = await client.get(f"{API_BASE}/redis/status")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Redis status: Connected")
                print(f"   Memory: {data.get('memory', {}).get('used_memory_human', 'unknown')}")
                print(f"   Cache keys: {data.get('cache_db_keys', 0)}")
            else:
                print(f"❌ Redis status failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Health tests failed: {e}")

async def test_cache_operations():
    """Test Redis cache operations"""
    print("\n💾 Testing Cache Operations...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Clear cache
            response = await client.post(f"{API_BASE}/redis/cache/clear")
            if response.status_code == 200:
                print("✅ Cache cleared successfully")
            else:
                print(f"❌ Cache clear failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Cache operations failed: {e}")

async def test_task_management():
    """Test task creation and monitoring"""
    print("\n⚙️ Testing Task Management...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Get active tasks
            response = await client.get(f"{API_BASE}/tasks/active")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Active tasks retrieved: {len(data.get('active_tasks', {}))}")
            else:
                print(f"❌ Active tasks failed: {response.status_code}")
                
            # Test task status for a dummy task
            dummy_task_id = "test-task-123"
            response = await client.get(f"{API_BASE}/task/{dummy_task_id}")
            print(f"📊 Task status check (dummy): {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Status: {data.get('status', 'unknown')}")
                
        except Exception as e:
            print(f"❌ Task management tests failed: {e}")

async def test_video_upload_task():
    """Test video upload with task management"""
    print("\n🎥 Testing Video Upload with Tasks...")
    
    # Create a small test video file
    test_video_path = project_root / "test_video.mp4"
    
    if not test_video_path.exists():
        print("⚠️  No test video found, skipping upload test")
        print("   Create a small test.mp4 file to test uploads")
        return
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            with open(test_video_path, "rb") as f:
                files = {"file": ("test_video.mp4", f, "video/mp4")}
                response = await client.post(f"{API_BASE}/upload-video", files=files)
                
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("task_id")
                print(f"✅ Video upload initiated: Task {task_id}")
                
                # Monitor task progress
                if task_id and task_id != "fallback":
                    await monitor_task(client, task_id)
                else:
                    print("   Using fallback mode (no Redis)")
                    
            else:
                print(f"❌ Video upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Video upload test failed: {e}")

async def test_youtube_processing_task():
    """Test YouTube processing with task management"""
    print("\n📺 Testing YouTube Processing with Tasks...")
    
    # Use a short, public video for testing
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll (classic test video)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            payload = {
                "url": test_url,
                "use_whisper": False,
                "whisper_model": "base"
            }
            response = await client.post(f"{API_BASE}/process-youtube", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("task_id")
                print(f"✅ YouTube processing initiated: Task {task_id}")
                
                # Monitor task progress
                if task_id and task_id != "fallback":
                    await monitor_task(client, task_id, max_wait=120)
                else:
                    print("   Using fallback mode (no Redis)")
                    
            else:
                print(f"❌ YouTube processing failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ YouTube processing test failed: {e}")

async def monitor_task(client, task_id, max_wait=60):
    """Monitor a task until completion"""
    print(f"   Monitoring task {task_id}...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = await client.get(f"{API_BASE}/task/{task_id}")
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                
                if status == "pending":
                    print("   Status: Pending...")
                elif status == "processing":
                    progress = data.get("progress", {})
                    if progress:
                        print(f"   Status: Processing - {progress}")
                    else:
                        print("   Status: Processing...")
                elif status == "completed":
                    result = data.get("result", {})
                    print(f"   ✅ Task completed: {result}")
                    break
                elif status == "failed":
                    error = data.get("error", "Unknown error")
                    print(f"   ❌ Task failed: {error}")
                    break
                else:
                    print(f"   Status: {status}")
                    
            await asyncio.sleep(3)  # Check every 3 seconds
            
        except Exception as e:
            print(f"   ⚠️  Error monitoring task: {e}")
            break
    else:
        print("   ⏰ Task monitoring timeout")

async def main():
    """Run all Redis integration tests"""
    print("🧪 Redis Integration Test Suite")
    print("=" * 50)
    
    try:
        await test_redis_health()
        await test_cache_operations()
        await test_task_management()
        
        print("\n" + "=" * 50)
        print("🚀 Background Task Tests (requires workers)")
        
        # Check if we should run background task tests
        print("\n⚠️  The following tests require Celery workers to be running.")
        print("   Start workers with: python start_celery_worker.py")
        
        user_input = input("\nRun background task tests? [y/N]: ").strip().lower()
        if user_input in ['y', 'yes']:
            await test_video_upload_task()
            await test_youtube_processing_task()
        else:
            print("Skipping background task tests")
        
        print("\n✅ Redis integration tests completed!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")

if __name__ == '__main__':
    asyncio.run(main())
