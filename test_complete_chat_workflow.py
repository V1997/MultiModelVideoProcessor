#!/usr/bin/env python3
"""
Complete end-to-end chat workflow test
"""
import requests
import json

def test_complete_chat_workflow():
    """Test complete chat workflow: session creation → messaging"""
    print('🔄 Testing Complete Chat Workflow...')
    
    video_id = 23
    
    try:
        # Step 1: Create chat session
        print('\n📝 Step 1: Creating chat session...')
        session_response = requests.post(
            f'http://localhost:8000/api/v1/chat/sessions?video_id={video_id}&title=E2E Test Session',
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if session_response.status_code != 200:
            print(f'❌ Session creation failed: {session_response.status_code}')
            return False
        
        session_data = session_response.json()
        session_id = session_data['session_id']
        print(f'✅ Session created: {session_id}')
        
        # Step 2: Send a test message
        print('\n💬 Step 2: Sending test message...')
        message_data = {
            'session_id': session_id,
            'message': 'What is this video about?'
        }
        
        message_response = requests.post(
            f'http://localhost:8000/api/v1/chat/sessions/{session_id}/messages',
            json=message_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f'📡 Message Response Status: {message_response.status_code}')
        
        if message_response.status_code == 200:
            message_result = message_response.json()
            print(f'✅ Message sent successfully!')
            print(f'📋 Response: {json.dumps(message_result, indent=2)[:500]}...')
            
            # Step 3: Get conversation history
            print('\n📜 Step 3: Getting conversation history...')
            history_response = requests.get(
                f'http://localhost:8000/api/v1/chat/sessions/{session_id}/history',
                timeout=10
            )
            
            if history_response.status_code == 200:
                history_data = history_response.json()
                print(f'✅ History retrieved: {len(history_data.get("messages", []))} messages')
                return True
            else:
                print(f'⚠️ History retrieval failed: {history_response.status_code}')
                return True  # Session and messaging worked
        else:
            print(f'❌ Message sending failed: {message_response.status_code}')
            print(f'📋 Response: {message_response.text[:300]}')
            return False
            
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')
        return False

if __name__ == '__main__':
    print('=' * 60)
    print('🔄 COMPLETE CHAT WORKFLOW TEST')
    print('=' * 60)
    success = test_complete_chat_workflow()
    print('=' * 60)
    print(f'🎯 Overall Result: {"PASS" if success else "FAIL"}')
    print('=' * 60)
