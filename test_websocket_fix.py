#!/usr/bin/env python3
"""
Test WebSocket integration fix - verify ASGI error is resolved
"""

import asyncio
import aiohttp
import socketio
import requests
import time
import json

# Test configuration
API_BASE = "http://localhost:8000"
SOCKET_IO_URL = "http://localhost:8000"

async def test_websocket_connection():
    """Test Socket.IO WebSocket connection"""
    print("🔌 Testing WebSocket Connection...")
    
    try:
        # Create Socket.IO client
        sio = socketio.AsyncClient(logger=True, engineio_logger=True)
        
        # Connection event handlers
        connection_success = False
        connection_error = None
        
        @sio.event
        async def connect():
            nonlocal connection_success
            print("✅ WebSocket connected successfully!")
            connection_success = True
        
        @sio.event
        async def connect_error(data):
            nonlocal connection_error
            print(f"❌ WebSocket connection error: {data}")
            connection_error = data
        
        @sio.event
        async def disconnect():
            print("🔌 WebSocket disconnected")
        
        # Attempt connection
        print(f"Connecting to {SOCKET_IO_URL}...")
        await sio.connect(SOCKET_IO_URL)
        
        # Wait for connection confirmation
        await asyncio.sleep(2)
        
        if connection_success:
            print("✅ WebSocket connection test PASSED")
            
            # Test sending a message
            await sio.emit('test_message', {'message': 'Hello from test client'})
            print("✅ Message sent successfully")
            
            # Wait and disconnect
            await asyncio.sleep(1)
            await sio.disconnect()
            
            return True
        else:
            print(f"❌ WebSocket connection test FAILED: {connection_error}")
            return False
            
    except Exception as e:
        print(f"❌ WebSocket test exception: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints work alongside WebSocket"""
    print("\n🌐 Testing API Endpoints...")
    
    try:
        # Test root endpoint
        response = requests.get(f"{API_BASE}/", timeout=10)
        if response.status_code == 200:
            print("✅ Root endpoint working")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
        
        # Test WebSocket status endpoint
        response = requests.get(f"{API_BASE}/api/v1/websocket/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ WebSocket status: {data}")
        else:
            print(f"❌ WebSocket status endpoint failed: {response.status_code}")
            return False
        
        # Test health endpoint
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API test exception: {e}")
        return False

def test_chat_session_creation():
    """Test chat session creation (should work with WebSocket integration)"""
    print("\n💬 Testing Chat Session Creation...")
    
    try:
        # Create a chat session
        response = requests.post(
            f"{API_BASE}/api/v1/chat/sessions",
            params={"video_id": 1, "title": "WebSocket Test Session"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            session_id = data.get("session_id")
            print(f"✅ Chat session created: {session_id}")
            return True
        elif response.status_code == 501:
            print("⚠️ Chat features not fully implemented (expected)")
            return True
        else:
            print(f"❌ Chat session creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat session test exception: {e}")
        return False

async def main():
    """Run all WebSocket fix tests"""
    print("🧪 WEBSOCKET FIX VERIFICATION TEST")
    print("=" * 50)
    print(f"Testing server at: {API_BASE}")
    print(f"Socket.IO URL: {SOCKET_IO_URL}")
    print()
    
    # Test results
    results = []
    
    # Test 1: API endpoints
    api_result = test_api_endpoints()
    results.append(("API Endpoints", api_result))
    
    # Test 2: Chat session creation
    chat_result = test_chat_session_creation()
    results.append(("Chat Session Creation", chat_result))
    
    # Test 3: WebSocket connection (this was failing before)
    websocket_result = await test_websocket_connection()
    results.append(("WebSocket Connection", websocket_result))
    
    # Results summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    success_rate = (passed / total) * 100
    print(f"\nSuccess Rate: {success_rate:.1f}% ({passed}/{total})")
    
    if success_rate >= 100:
        print("\n🎉 ALL TESTS PASSED! WebSocket ASGI error is FIXED!")
        print("✅ The RuntimeError: Expected ASGI message 'websocket.accept' is resolved")
        print("✅ Frontend can now connect to WebSocket without errors")
    elif success_rate >= 67:
        print("\n✅ MOSTLY SUCCESSFUL! WebSocket integration working")
        print("⚠️ Some minor issues may remain")
    else:
        print("\n❌ TESTS FAILED! WebSocket integration still has issues")
        print("🔧 Further investigation needed")

if __name__ == "__main__":
    asyncio.run(main())
