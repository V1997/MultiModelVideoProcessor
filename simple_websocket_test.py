#!/usr/bin/env python3
"""
Simple WebSocket Connection Test
"""

import asyncio
import socketio
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection():
    """Simple WebSocket connection test"""
    print("🔌 Testing WebSocket connection...")
    
    sio = socketio.AsyncClient()
    connected = False
    
    @sio.event
    async def connect():
        nonlocal connected
        print("✅ Connected to WebSocket server!")
        connected = True
        
    @sio.event
    async def disconnect():
        print("❌ Disconnected from WebSocket server")
        
    @sio.event
    async def connected(data):
        print(f"📨 Welcome message: {data}")
    
    try:
        print("Attempting to connect to http://localhost:8000...")
        await sio.connect('http://localhost:8000')
        
        # Wait a bit to see if connection is established
        await asyncio.sleep(2)
        
        if connected:
            print("✅ WebSocket connection successful!")
            
            # Test joining a chat session
            print("\n🏠 Testing chat session join...")
            await sio.emit('join_chat_session', {
                'session_id': 'test_session_123',
                'video_id': 1
            })
            
            await asyncio.sleep(2)
            
            print("✅ Chat session join test completed")
            
        else:
            print("❌ WebSocket connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    finally:
        if connected:
            await sio.disconnect()
    
    return connected

if __name__ == "__main__":
    try:
        result = asyncio.run(test_connection())
        if result:
            print("\n🎉 WebSocket integration test PASSED!")
            sys.exit(0)
        else:
            print("\n❌ WebSocket integration test FAILED!")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        sys.exit(1)
