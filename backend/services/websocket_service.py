# WebSocket Service for Real-time Communication
# Handles chat updates, processing status, and video analysis results

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import socketio
from fastapi import FastAPI
from backend.services.redis_service import get_redis_service, is_redis_available

logger = logging.getLogger(__name__)

class WebSocketService:
    """
    WebSocket service for real-time communication in MultiModelVideo.
    Handles chat updates, processing status, and video analysis results.
    """
    
    def __init__(self):
        # Create Socket.IO server with CORS support for ASGI
        self.sio = socketio.AsyncServer(
            cors_allowed_origins="*",
            logger=True,
            engineio_logger=True,
            async_mode='asgi'  # Use ASGI mode for FastAPI integration
        )
        
        # Connected clients tracking
        self.connected_clients: Dict[str, Dict[str, Any]] = {}
        self.session_rooms: Dict[str, List[str]] = {}  # session_id -> [client_ids]
        
        # Redis integration for persistence
        self.redis_available = is_redis_available()
        self.redis_service = get_redis_service() if self.redis_available else None
        
        # Setup event handlers
        self._setup_event_handlers()
        
        logger.info("WebSocket service initialized")
    
    def _setup_event_handlers(self):
        """Setup Socket.IO event handlers"""
        
        @self.sio.event
        async def connect(sid, environ, auth):
            """Handle client connection"""
            try:
                logger.info(f"Client {sid} connected")
                
                # Store client info
                self.connected_clients[sid] = {
                    'connected_at': datetime.utcnow().isoformat(),
                    'session_id': None,
                    'user_id': auth.get('user_id') if auth else f"anonymous_{sid[:8]}",
                    'video_id': None
                }
                
                # Send welcome message
                await self.sio.emit('connected', {
                    'message': 'Connected to MultiModelVideo WebSocket',
                    'client_id': sid,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                
                # Store connection in Redis if available
                if self.redis_service:
                    await self._store_connection_redis(sid)
                
                return True
                
            except Exception as e:
                logger.error(f"Error in connect handler: {e}")
                return False
        
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection"""
            try:
                logger.info(f"Client {sid} disconnected")
                
                # Remove from session rooms
                if sid in self.connected_clients:
                    session_id = self.connected_clients[sid].get('session_id')
                    if session_id and session_id in self.session_rooms:
                        if sid in self.session_rooms[session_id]:
                            self.session_rooms[session_id].remove(sid)
                        if not self.session_rooms[session_id]:
                            del self.session_rooms[session_id]
                
                # Remove client tracking
                if sid in self.connected_clients:
                    del self.connected_clients[sid]
                
                # Remove from Redis if available
                if self.redis_service:
                    await self._remove_connection_redis(sid)
                    
            except Exception as e:
                logger.error(f"Error in disconnect handler: {e}")
        
        @self.sio.event
        async def join_chat_session(sid, data):
            """Join a chat session room for real-time updates"""
            try:
                session_id = data.get('session_id')
                video_id = data.get('video_id')
                
                if not session_id:
                    await self.sio.emit('error', {
                        'message': 'session_id is required'
                    }, room=sid)
                    return
                
                # Update client info
                if sid in self.connected_clients:
                    self.connected_clients[sid]['session_id'] = session_id
                    self.connected_clients[sid]['video_id'] = video_id
                
                # Add to session room
                if session_id not in self.session_rooms:
                    self.session_rooms[session_id] = []
                
                if sid not in self.session_rooms[session_id]:
                    self.session_rooms[session_id].append(sid)
                
                # Join Socket.IO room
                await self.sio.enter_room(sid, f"chat_{session_id}")
                
                # Notify successful join
                await self.sio.emit('joined_chat_session', {
                    'session_id': session_id,
                    'video_id': video_id,
                    'message': 'Successfully joined chat session',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                
                logger.info(f"Client {sid} joined chat session {session_id}")
                
            except Exception as e:
                logger.error(f"Error joining chat session: {e}")
                await self.sio.emit('error', {
                    'message': f'Failed to join chat session: {str(e)}'
                }, room=sid)
        
        @self.sio.event
        async def leave_chat_session(sid, data):
            """Leave a chat session room"""
            try:
                session_id = data.get('session_id')
                
                if session_id:
                    # Remove from session room
                    if session_id in self.session_rooms and sid in self.session_rooms[session_id]:
                        self.session_rooms[session_id].remove(sid)
                        if not self.session_rooms[session_id]:
                            del self.session_rooms[session_id]
                    
                    # Leave Socket.IO room
                    await self.sio.leave_room(sid, f"chat_{session_id}")
                    
                    # Update client info
                    if sid in self.connected_clients:
                        self.connected_clients[sid]['session_id'] = None
                        self.connected_clients[sid]['video_id'] = None
                    
                    await self.sio.emit('left_chat_session', {
                        'session_id': session_id,
                        'message': 'Left chat session',
                        'timestamp': datetime.utcnow().isoformat()
                    }, room=sid)
                    
                    logger.info(f"Client {sid} left chat session {session_id}")
                
            except Exception as e:
                logger.error(f"Error leaving chat session: {e}")
        
        @self.sio.event
        async def subscribe_processing_status(sid, data):
            """Subscribe to video processing status updates"""
            try:
                video_id = data.get('video_id')
                task_id = data.get('task_id')
                
                if video_id:
                    await self.sio.enter_room(sid, f"video_{video_id}")
                    
                if task_id:
                    await self.sio.enter_room(sid, f"task_{task_id}")
                
                await self.sio.emit('subscribed_processing', {
                    'video_id': video_id,
                    'task_id': task_id,
                    'message': 'Subscribed to processing updates',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                
                logger.info(f"Client {sid} subscribed to processing status for video {video_id}")
                
            except Exception as e:
                logger.error(f"Error subscribing to processing status: {e}")
        
        @self.sio.event
        async def subscribe_visual_analysis(sid, data):
            """Subscribe to visual analysis results"""
            try:
                video_id = data.get('video_id')
                
                if video_id:
                    await self.sio.enter_room(sid, f"visual_{video_id}")
                    
                    await self.sio.emit('subscribed_visual', {
                        'video_id': video_id,
                        'message': 'Subscribed to visual analysis updates',
                        'timestamp': datetime.utcnow().isoformat()
                    }, room=sid)
                    
                    logger.info(f"Client {sid} subscribed to visual analysis for video {video_id}")
                
            except Exception as e:
                logger.error(f"Error subscribing to visual analysis: {e}")
    
    async def _store_connection_redis(self, sid: str):
        """Store connection info in Redis"""
        try:
            if self.redis_service:
                connection_data = self.connected_clients.get(sid, {})
                key = f"websocket:connection:{sid}"
                await asyncio.get_event_loop().run_in_executor(
                    None, 
                    self.redis_service.redis_client.hset,
                    key,
                    mapping=connection_data
                )
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.redis_service.redis_client.expire,
                    key,
                    3600  # 1 hour
                )
        except Exception as e:
            logger.error(f"Error storing connection in Redis: {e}")
    
    async def _remove_connection_redis(self, sid: str):
        """Remove connection info from Redis"""
        try:
            if self.redis_service:
                key = f"websocket:connection:{sid}"
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.redis_service.redis_client.delete,
                    key
                )
        except Exception as e:
            logger.error(f"Error removing connection from Redis: {e}")
    
    # ==========================================
    # BROADCAST METHODS FOR REAL-TIME UPDATES
    # ==========================================
    
    async def broadcast_chat_message(self, session_id: str, message_data: Dict[str, Any]):
        """Broadcast new chat message to all clients in session"""
        try:
            room = f"chat_{session_id}"
            
            await self.sio.emit('new_chat_message', {
                'session_id': session_id,
                'message': message_data.get('message'),
                'response': message_data.get('response'),
                'role': message_data.get('role'),
                'timestamp': message_data.get('timestamp', datetime.utcnow().isoformat()),
                'timestamp_citations': message_data.get('timestamp_citations', []),
                'confidence': message_data.get('confidence', 0.0)
            }, room=room)
            
            logger.info(f"Broadcasted chat message to session {session_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting chat message: {e}")
    
    async def broadcast_processing_status(self, video_id: int, status_data: Dict[str, Any]):
        """Broadcast video processing status updates"""
        try:
            room = f"video_{video_id}"
            
            await self.sio.emit('processing_status', {
                'video_id': video_id,
                'status': status_data.get('status'),
                'progress': status_data.get('progress', 0),
                'stage': status_data.get('stage'),
                'message': status_data.get('message'),
                'timestamp': datetime.utcnow().isoformat(),
                'estimated_time': status_data.get('estimated_time'),
                'error': status_data.get('error')
            }, room=room)
            
            # Also broadcast to task-specific room if task_id provided
            task_id = status_data.get('task_id')
            if task_id:
                await self.sio.emit('processing_status', {
                    'video_id': video_id,
                    'task_id': task_id,
                    'status': status_data.get('status'),
                    'progress': status_data.get('progress', 0),
                    'stage': status_data.get('stage'),
                    'message': status_data.get('message'),
                    'timestamp': datetime.utcnow().isoformat()
                }, room=f"task_{task_id}")
            
            logger.info(f"Broadcasted processing status for video {video_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting processing status: {e}")
    
    async def broadcast_visual_analysis_result(self, video_id: int, analysis_data: Dict[str, Any]):
        """Broadcast visual analysis results"""
        try:
            room = f"visual_{video_id}"
            
            await self.sio.emit('visual_analysis_result', {
                'video_id': video_id,
                'frame_timestamp': analysis_data.get('frame_timestamp'),
                'objects_detected': analysis_data.get('objects_detected', []),
                'scene_classification': analysis_data.get('scene_classification'),
                'confidence_scores': analysis_data.get('confidence_scores', {}),
                'frame_path': analysis_data.get('frame_path'),
                'analysis_type': analysis_data.get('analysis_type'),
                'timestamp': datetime.utcnow().isoformat()
            }, room=room)
            
            logger.info(f"Broadcasted visual analysis result for video {video_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting visual analysis result: {e}")
    
    async def broadcast_content_analysis_update(self, video_id: int, content_data: Dict[str, Any]):
        """Broadcast content analysis updates (topics, segments, outlines)"""
        try:
            room = f"video_{video_id}"
            
            await self.sio.emit('content_analysis_update', {
                'video_id': video_id,
                'analysis_type': content_data.get('type'),
                'topic_segments': content_data.get('topic_segments', []),
                'content_outline': content_data.get('content_outline'),
                'navigation_events': content_data.get('navigation_events', []),
                'timestamp': datetime.utcnow().isoformat()
            }, room=room)
            
            logger.info(f"Broadcasted content analysis update for video {video_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting content analysis update: {e}")
    
    # ==========================================    # ==========================================
    # UTILITY METHODS
    # ==========================================
    
    def get_connected_clients_count(self) -> int:
        """Get total number of connected clients"""
        return len(self.connected_clients)
    
    def get_session_clients_count(self, session_id: str) -> int:
        """Get number of clients in a specific session"""
        return len(self.session_rooms.get(session_id, []))
    
    def get_client_info(self, sid: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific client"""
        return self.connected_clients.get(sid)
    
    async def send_to_client(self, sid: str, event: str, data: Dict[str, Any]):
        """Send message to specific client"""
        try:
            await self.sio.emit(event, data, room=sid)
            logger.debug(f"Sent {event} to client {sid}")
        except Exception as e:
            logger.error(f"Error sending message to client {sid}: {e}")
    
    def get_app(self):
        """Get Socket.IO ASGI application for FastAPI integration"""
        # Return the Socket.IO server, not wrapped in ASGIApp
        # FastAPI will handle the integration
        return self.sio

# Global WebSocket service instance
websocket_service = WebSocketService()

def get_websocket_service() -> WebSocketService:
    """Get the global WebSocket service instance"""
    return websocket_service
