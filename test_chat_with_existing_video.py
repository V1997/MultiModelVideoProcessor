#!/usr/bin/env python3
"""
Test complete chat workflow using existing video data
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
EXISTING_VIDEO_ID = 2  # Use video that already has transcript chunks and frames

def test_complete_chat_workflow():
    """Test the complete chat workflow using existing video"""
    
    print("🚀 Testing Complete Chat Workflow with Existing Video")
    print("=" * 55)
    
    # Step 1: Test server health
    print("\n1. Testing server health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Server healthy - Database: {health_data['services']['database']}, Redis: {health_data['services']['redis']}")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return
      # Step 2: Create chat session
    print(f"\n2. Creating chat session for video ID {EXISTING_VIDEO_ID}...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/sessions",
            params={"video_id": EXISTING_VIDEO_ID, "title": "Test Chat Session"},
            timeout=30
        )
        
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data["session_id"]
            print(f"✅ Chat session created: {session_id[:8]}...")
        else:
            print(f"❌ Failed to create chat session: {response.status_code}")
            print(f"Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Chat session creation error: {e}")
        return
      # Step 3: Send test message
    print(f"\n3. Sending test message to session...")
    try:
        message_data = {
            "message": "What is this video about?"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/sessions/{session_id}/messages",
            json=message_data,
            timeout=60
        )
        
        if response.status_code == 200:
            chat_response = response.json()
            print(f"✅ Chat message sent successfully!")
            print(f"   Response: {chat_response.get('response', 'No response')[:100]}...")
            print(f"   Confidence: {chat_response.get('confidence', 0):.2f}")
            print(f"   Citations: {len(chat_response.get('timestamp_citations', []))}")
            print(f"   Frame refs: {len(chat_response.get('frame_references', []))}")
        else:
            print(f"❌ Failed to send chat message: {response.status_code}")
            print(f"Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Chat message error: {e}")
        return
    
    # Step 4: Send follow-up message
    print(f"\n4. Sending follow-up message...")
    try:
        follow_up_data = {
            "message": "Can you tell me more about the main topics discussed?"
        }
          response = requests.post(
            f"{BASE_URL}/api/v1/chat/sessions/{session_id}/messages",
            json=follow_up_data,
            timeout=60
        )
        
        if response.status_code == 200:
            chat_response = response.json()
            print(f"✅ Follow-up message sent successfully!")
            print(f"   Response: {chat_response.get('response', 'No response')[:100]}...")
            print(f"   Confidence: {chat_response.get('confidence', 0):.2f}")
        else:
            print(f"❌ Failed to send follow-up message: {response.status_code}")
            print(f"Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Follow-up message error: {e}")
        return
    
    # Step 5: Get session history
    print(f"\n5. Retrieving session history...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/chat/sessions/{session_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            session_info = response.json()
            print(f"✅ Session info retrieved!")
            print(f"   Video ID: {session_info.get('video_id')}")
            print(f"   Title: {session_info.get('title')}")
            print(f"   Created: {session_info.get('created_at')}")
        else:
            print(f"❌ Failed to get session info: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Session info error: {e}")
    
    print(f"\n🎉 Chat workflow test completed successfully!")
    print(f"   Session ID: {session_id}")
    print(f"   Video ID: {EXISTING_VIDEO_ID}")

if __name__ == "__main__":
    test_complete_chat_workflow()
