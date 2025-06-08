#!/usr/bin/env python3
"""
Minimal Socket.IO test to verify mounting works
"""

import socketio
from fastapi import FastAPI
import uvicorn

# Create FastAPI app
app = FastAPI()

# Create Socket.IO server
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    async_mode='asgi'
)

# Basic event handler
@sio.event
async def connect(sid, environ, auth):
    print(f"Client {sid} connected")
    await sio.emit('message', {'data': 'Welcome!'}, room=sid)

@sio.event
async def disconnect(sid):
    print(f"Client {sid} disconnected")

# Create Socket.IO ASGI app that wraps the FastAPI app
socket_app = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path="socket.io")

# Basic route
@app.get("/")
async def root():
    return {"message": "Test server with Socket.IO"}

if __name__ == "__main__":
    # Run the socket_app instead of app
    uvicorn.run(socket_app, host="0.0.0.0", port=8002)
