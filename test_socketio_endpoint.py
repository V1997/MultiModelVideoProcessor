#!/usr/bin/env python3
"""
Test Socket.IO endpoint accessibility
"""

import requests
import socketio

def test_socketio_endpoint(port=8002):
    """Test if Socket.IO endpoint is accessible"""
    base_url = f"http://localhost:{port}"
    
    print(f"🔌 Testing Socket.IO endpoint at {base_url}")
    
    # Test basic HTTP endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Basic HTTP: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Basic HTTP error: {e}")
    
    # Test Socket.IO handshake endpoint
    try:
        handshake_url = f"{base_url}/socket.io/?transport=polling&EIO=4"
        response = requests.get(handshake_url)
        print(f"✅ Socket.IO handshake: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response preview: {response.text[:100]}...")
        else:
            print(f"   Error response: {response.text}")
    except Exception as e:
        print(f"❌ Socket.IO handshake error: {e}")
    
    # Test Socket.IO client connection
    try:
        sio = socketio.SimpleClient()
        sio.connect(base_url, wait_timeout=5)
        print("✅ Socket.IO client connected successfully")
        sio.disconnect()
    except Exception as e:
        print(f"❌ Socket.IO client connection error: {e}")

if __name__ == "__main__":
    test_socketio_endpoint(8002)  # Test minimal server
    print("\n" + "="*50 + "\n")
    test_socketio_endpoint(8000)  # Test main server (when running)
