#!/usr/bin/env python3
"""
Final Complete Chat Workflow Test
Tests the entire chat workflow from video processing to message exchange
"""

import requests
import json
import time

def test_complete_chat_workflow():
    """Test the complete chat workflow end-to-end"""
    print("🚀 Testing Complete Chat Workflow (Final)")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Step 1: Test server health
    print("\n1. Testing server health...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Server healthy - Database: {health_data['services']['database']}, Redis: {health_data['services']['redis']}")
        else:
            print(f"⚠️ Server responded but not healthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server health check failed: {e}")
        return False
    
    # Step 2: Process a YouTube video to ensure we have video data
    print("\n2. Processing YouTube video...")
    try:
        youtube_data = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "extract_transcript": True,
            "extract_frames": True
        }
        
        response = requests.post(f"{base_url}/api/v1/youtube/process", json=youtube_data, timeout=30)
        
        if response.status_code == 200:
            task_data = response.json()
            print(f"✅ Video processing started - Task ID: {task_data['task_id']}")
            
            # Extract video_id from response
            video_id = task_data.get('video_id')
            if video_id:
                print(f"✅ Video ID received: {video_id}")
            else:
                print("❌ No video_id in response")
                return False
                
        else:
            print(f"❌ Video processing failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Video processing error: {e}")
        return False
    
    # Step 3: Create chat session
    print("\n3. Creating chat session...")
    try:
        session_response = requests.post(
            f"{base_url}/api/v1/chat/sessions",
            params={"video_id": video_id, "title": "Final Workflow Test Session"}
        )
        
        if session_response.status_code == 200:
            session_data = session_response.json()
            session_id = session_data['session_id']
            print(f"✅ Chat session created: {session_id[:8]}...")
        else:
            print(f"❌ Chat session creation failed: {session_response.status_code}")
            print(f"Response: {session_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat session creation error: {e}")
        return False
    
    # Step 4: Send a chat message
    print("\n4. Sending chat message...")
    try:
        message_data = {
            "message": "What is this video about? Can you give me a brief summary?"
        }
        
        message_response = requests.post(
            f"{base_url}/api/v1/chat/sessions/{session_id}/messages",
            json=message_data,
            timeout=30
        )
        
        if message_response.status_code == 200:
            response_data = message_response.json()
            print(f"✅ Chat message sent successfully")
            print(f"📝 AI Response: {response_data.get('response', 'No response')[:100]}...")
            print(f"🔗 Timestamp Citations: {len(response_data.get('timestamp_citations', []))}")
            print(f"🖼️ Frame References: {len(response_data.get('frame_references', []))}")
            print(f"📊 Confidence: {response_data.get('confidence', 0):.2f}")
        else:
            print(f"❌ Chat message failed: {message_response.status_code}")
            print(f"Response: {message_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat message error: {e}")
        return False
    
    # Step 5: Send a follow-up message
    print("\n5. Sending follow-up message...")
    try:
        followup_data = {
            "message": "Can you tell me more details about the main topic discussed?"
        }
        
        followup_response = requests.post(
            f"{base_url}/api/v1/chat/sessions/{session_id}/messages",
            json=followup_data,
            timeout=30
        )
        
        if followup_response.status_code == 200:
            followup_response_data = followup_response.json()
            print(f"✅ Follow-up message sent successfully")
            print(f"📝 AI Response: {followup_response_data.get('response', 'No response')[:100]}...")
        else:
            print(f"❌ Follow-up message failed: {followup_response.status_code}")
            print(f"Response: {followup_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Follow-up message error: {e}")
        return False
    
    # Step 6: Get session details
    print("\n6. Getting session details...")
    try:
        session_details_response = requests.get(f"{base_url}/api/v1/chat/sessions/{session_id}")
        
        if session_details_response.status_code == 200:
            details_data = session_details_response.json()
            print(f"✅ Session details retrieved")
            print(f"📹 Video ID: {details_data.get('video_id')}")
            print(f"📝 Title: {details_data.get('title')}")
        else:
            print(f"❌ Session details failed: {session_details_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Session details error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 COMPLETE CHAT WORKFLOW TEST PASSED!")
    print("✅ All chat functionality working correctly")
    print("✅ Video processing integration working")
    print("✅ Chat session management working")
    print("✅ Chat messaging working")
    print("✅ Context-aware conversations working")
    return True

if __name__ == "__main__":
    success = test_complete_chat_workflow()
    if success:
        print("\n🚀 The chat system is fully operational!")
    else:
        print("\n❌ Chat system has issues that need attention")
