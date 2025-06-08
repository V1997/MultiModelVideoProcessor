#!/usr/bin/env python3
"""
Quick test for chat session creation fix
"""
import requests
import json

def test_chat_session_creation():
    """Test chat session creation with correct parameter format"""
    print('🗨️ Testing Chat Session Creation Fix...')
    
    # Use existing video ID from previous tests
    video_id = 23
    
    try:
        # Test with query parameters (correct format)
        response = requests.post(
            f'http://localhost:8000/api/v1/chat/sessions?video_id={video_id}&title=Fix Test Session',
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f'📡 Response Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'✅ SUCCESS: Chat session created!')
            print(f'📋 Session Data: {json.dumps(data, indent=2)}')
            return True
        else:
            print(f'❌ FAILED: HTTP {response.status_code}')
            print(f'📋 Response: {response.text[:300]}')
            return False
            
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')
        return False

if __name__ == '__main__':
    print('=' * 50)
    print('🔧 CHAT SESSION FIX TEST')
    print('=' * 50)
    success = test_chat_session_creation()
    print('=' * 50)
    print(f'🎯 Result: {"PASS" if success else "FAIL"}')
    print('=' * 50)
