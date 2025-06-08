#!/usr/bin/env python3
"""
Critical Video ID Integration Test
Tests that the TaskResponse video_id fix is working properly
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_server_connection():
    """Test basic server connectivity"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and responsive")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def test_task_response_structure():
    """Test that TaskResponse includes video_id field"""
    print("\n🔧 TESTING CRITICAL VIDEO_ID FIX")
    print("=" * 50)
    
    try:        # Test YouTube processing endpoint
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        processing_data = {
            "url": test_url,
            "use_whisper": False,
            "whisper_model": "base"
        }
        
        print(f"🔍 Testing YouTube processing with URL: {test_url}")
        response = requests.post(
            f"{BASE_URL}/process-youtube",
            json=processing_data,
            timeout=30
        )
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            task_response = response.json()
            print(f"📦 Response Data: {json.dumps(task_response, indent=2)}")
            
            # Check TaskResponse structure
            required_fields = ["task_id", "status", "message", "video_id", "chunks_processed", "total_chunks", "progress"]
            
            print("\n🔍 Checking TaskResponse structure:")
            for field in required_fields:
                if field in task_response:
                    value = task_response[field]
                    print(f"  ✅ {field}: {value} ({type(value).__name__})")
                else:
                    print(f"  ❌ {field}: MISSING")
            
            # Critical test: Check video_id
            video_id = task_response.get("video_id")
            print(f"\n🎯 CRITICAL TEST - video_id value: {video_id}")
            
            if video_id is None:
                print("❌ CRITICAL BUG: video_id is None/undefined!")
                print("   This will cause frontend chat session creation to fail with 422 error")
                return False
            elif isinstance(video_id, int) and video_id > 0:
                print(f"✅ SUCCESS: video_id = {video_id} (valid integer)")
                
                # Test chat session creation with this video_id
                print(f"\n🧪 Testing chat session creation with video_id = {video_id}")
                try:
                    chat_response = requests.post(
                        f"{BASE_URL}/api/v1/chat/sessions",
                        params={"video_id": video_id},
                        timeout=10
                    )
                    print(f"📡 Chat Session Response Status: {chat_response.status_code}")
                    
                    if chat_response.status_code == 200:
                        session_data = chat_response.json()
                        session_id = session_data.get("session_id")
                        print(f"✅ SUCCESS: Chat session created with ID: {session_id}")
                        print("🎉 The video_id fix is working correctly!")
                        return True
                    else:
                        print(f"❌ FAIL: Chat session creation failed with status {chat_response.status_code}")
                        print(f"Response: {chat_response.text[:300]}")
                        return False
                        
                except Exception as e:
                    print(f"❌ FAIL: Exception during chat session creation: {e}")
                    return False
            else:
                print(f"❌ FAIL: video_id = {video_id} (invalid type or value)")
                return False
                
        else:
            print(f"❌ FAIL: YouTube processing failed with status {response.status_code}")
            print(f"Response: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Exception during YouTube processing: {e}")
        return False

def main():
    print("🔧 CRITICAL VIDEO_ID INTEGRATION TEST")
    print("=" * 60)
    print("Testing the fix for video_id=undefined issue")
    print("=" * 60)
    
    # Test server connection
    if not test_server_connection():
        print("\nPlease ensure the backend server is running:")
        print("  uvicorn backend.api.main:app --reload --port 8000")
        sys.exit(1)
    
    # Test video_id integration
    success = test_task_response_structure()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULT")
    print("=" * 60)
    
    if success:
        print("🎉 SUCCESS: The video_id fix is working correctly!")
        print("✅ TaskResponse now includes video_id field")
        print("✅ Chat session creation works with proper video_id")
        print("✅ Frontend should no longer receive video_id=undefined")
        sys.exit(0)
    else:
        print("❌ FAILURE: The video_id fix is not working properly")
        print("⚠️  Frontend will still receive video_id=undefined")
        print("⚠️  Chat session creation will fail with 422 errors")
        sys.exit(1)

if __name__ == "__main__":
    main()
