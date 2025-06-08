#!/usr/bin/env python3
"""
Quick test to validate video_id fix in TaskResponse
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_video_id_fix():
    """Test that video_id is now included in TaskResponse"""
    print("🔧 Testing Video ID Fix in TaskResponse")
    print("=" * 50)
    
    # Test 1: Check API health
    print("\n1. Testing API Health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is healthy")
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API is not responding: {e}")
        return False
    
    # Test 2: Process YouTube video and check for video_id in response
    print("\n2. Testing YouTube Processing with video_id...")
    try:
        payload = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "use_whisper": False,
            "whisper_model": "base"
        }
        
        response = requests.post(
            f"{BASE_URL}/process-youtube",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ YouTube processing response received")
            print(f"   Response data: {json.dumps(data, indent=2)}")
            
            # Check if video_id is present
            if "video_id" in data:
                print(f"✅ video_id found: {data['video_id']}")
                print("✅ FIX SUCCESSFUL! video_id is now included in TaskResponse")
                return True
            else:
                print("❌ video_id NOT found in response")
                print("❌ Fix failed - video_id still missing")
                return False
                
        else:
            print(f"❌ YouTube processing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing YouTube processing: {e}")
        return False

def test_chat_session_creation():
    """Test chat session creation with proper video_id"""
    print("\n3. Testing Chat Session Creation...")
    
    # First get a video_id by processing a video
    payload = {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "use_whisper": False,
        "whisper_model": "base"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/process-youtube", json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            video_id = data.get("video_id")
            
            if video_id:
                # Test chat session creation
                chat_response = requests.post(
                    f"{BASE_URL}/api/v1/chat/sessions",
                    params={"video_id": str(video_id), "title": "Test Chat"},
                    timeout=10
                )
                
                if chat_response.status_code == 200:
                    chat_data = chat_response.json()
                    print(f"✅ Chat session created successfully: {chat_data.get('session_id')}")
                    return True
                else:
                    print(f"❌ Chat session creation failed: {chat_response.status_code}")
                    print(f"   Response: {chat_response.text}")
                    return False
            else:
                print("❌ No video_id found in YouTube processing response")
                return False
        else:
            print(f"❌ YouTube processing failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing chat session creation: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTING VIDEO_ID FIX")
    print("=" * 50)
    
    success = test_video_id_fix()
    
    if success:
        # If video_id fix works, test the complete flow
        success = test_chat_session_creation()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED! Video ID fix is working correctly.")
        print("✅ Frontend should now work properly with YouTube processing.")
    else:
        print("❌ TESTS FAILED! There are still issues to resolve.")
    print("=" * 50)
