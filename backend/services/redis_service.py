# Redis Service for MultiModelVideo
# Provides Redis connection, caching, session storage, and queue management

import redis
import json
import pickle
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class RedisService:
    """Redis service for caching, session storage, and background tasks"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client = None
        self._session_client = None  # Database 1 for sessions
        self._cache_client = None    # Database 2 for caching
        
    @property
    def client(self) -> redis.Redis:
        """Get main Redis client"""
        if self._client is None:
            try:
                self._client = redis.from_url(self.redis_url)
                # Test connection
                self._client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return self._client
    
    @property
    def session_client(self) -> redis.Redis:
        """Get Redis client for session storage (DB 1)"""
        if self._session_client is None:
            try:
                base_url = self.redis_url.rsplit('/', 1)[0]
                session_url = f"{base_url}/1"
                self._session_client = redis.from_url(session_url)
                self._session_client.ping()
                logger.info("Redis session client established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis session DB: {e}")
                raise
        return self._session_client
    
    @property
    def cache_client(self) -> redis.Redis:
        """Get Redis client for caching (DB 2)"""
        if self._cache_client is None:
            try:
                base_url = self.redis_url.rsplit('/', 1)[0]
                cache_url = f"{base_url}/2"
                self._cache_client = redis.from_url(cache_url)
                self._cache_client.ping()
                logger.info("Redis cache client established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis cache DB: {e}")
                raise
        return self._cache_client
    
    # ========================================
    # CACHING METHODS
    # ========================================
    
    def cache_set(self, key: str, value: Any, expire_seconds: int = 3600) -> bool:
        """Cache a value with expiration"""
        try:
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = pickle.dumps(value)
            
            return self.cache_client.setex(
                f"cache:{key}", 
                expire_seconds, 
                serialized_value
            )
        except Exception as e:
            logger.error(f"Failed to cache {key}: {e}")
            return False
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        try:
            value = self.cache_client.get(f"cache:{key}")
            if value is None:
                return None
            
            # Try JSON first, then pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return pickle.loads(value)
        except Exception as e:
            logger.error(f"Failed to get cached {key}: {e}")
            return None
    
    def cache_delete(self, key: str) -> bool:
        """Delete cached value"""
        try:
            return bool(self.cache_client.delete(f"cache:{key}"))
        except Exception as e:
            logger.error(f"Failed to delete cached {key}: {e}")
            return False
    
    def cache_exists(self, key: str) -> bool:
        """Check if cache key exists"""
        try:
            return bool(self.cache_client.exists(f"cache:{key}"))
        except Exception as e:
            logger.error(f"Failed to check cache existence {key}: {e}")
            return False
    
    # ========================================
    # SESSION STORAGE METHODS
    # ========================================
    
    def session_create(self, session_id: str, session_data: Dict, expire_hours: int = 24) -> bool:
        """Create/update session in Redis"""
        try:
            session_key = f"session:{session_id}"
            session_data['created_at'] = datetime.utcnow().isoformat()
            session_data['last_accessed'] = datetime.utcnow().isoformat()
            
            return self.session_client.setex(
                session_key,
                expire_hours * 3600,
                json.dumps(session_data)
            )
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {e}")
            return False
    
    def session_get(self, session_id: str) -> Optional[Dict]:
        """Get session data from Redis"""
        try:
            session_key = f"session:{session_id}"
            data = self.session_client.get(session_key)
            if data is None:
                return None
            
            session_data = json.loads(data)
            
            # Update last accessed time
            session_data['last_accessed'] = datetime.utcnow().isoformat()
            self.session_client.setex(
                session_key,
                24 * 3600,  # Reset expiration to 24 hours
                json.dumps(session_data)
            )
            
            return session_data
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    def session_update(self, session_id: str, updates: Dict) -> bool:
        """Update session data"""
        try:
            session_data = self.session_get(session_id)
            if session_data is None:
                return False
            
            session_data.update(updates)
            session_data['last_accessed'] = datetime.utcnow().isoformat()
            
            return self.session_client.setex(
                f"session:{session_id}",
                24 * 3600,
                json.dumps(session_data)
            )
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False
    
    def session_delete(self, session_id: str) -> bool:
        """Delete session from Redis"""
        try:
            return bool(self.session_client.delete(f"session:{session_id}"))
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def session_extend(self, session_id: str, hours: int = 24) -> bool:
        """Extend session expiration"""
        try:
            return bool(self.session_client.expire(f"session:{session_id}", hours * 3600))
        except Exception as e:
            logger.error(f"Failed to extend session {session_id}: {e}")
            return False
    
    # ========================================
    # CHAT MESSAGE CACHING
    # ========================================
    
    def chat_cache_messages(self, session_id: str, messages: List[Dict], expire_hours: int = 48) -> bool:
        """Cache chat messages for quick retrieval"""
        try:
            key = f"chat_messages:{session_id}"
            return self.cache_client.setex(
                key,
                expire_hours * 3600,
                json.dumps(messages)
            )
        except Exception as e:
            logger.error(f"Failed to cache chat messages for {session_id}: {e}")
            return False
    
    def chat_get_cached_messages(self, session_id: str) -> Optional[List[Dict]]:
        """Get cached chat messages"""
        try:
            key = f"chat_messages:{session_id}"
            data = self.cache_client.get(key)
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            logger.error(f"Failed to get cached chat messages for {session_id}: {e}")
            return None
    
    def chat_add_message(self, session_id: str, message: Dict) -> bool:
        """Add a single message to cached chat"""
        try:
            messages = self.chat_get_cached_messages(session_id) or []
            messages.append(message)
            return self.chat_cache_messages(session_id, messages)
        except Exception as e:
            logger.error(f"Failed to add message to chat cache {session_id}: {e}")
            return False
    
    # ========================================
    # VIDEO ANALYSIS CACHING
    # ========================================
    
    def cache_video_analysis(self, video_id: int, analysis_type: str, data: Dict, expire_hours: int = 168) -> bool:
        """Cache video analysis results (default 7 days)"""
        key = f"video_analysis:{video_id}:{analysis_type}"
        return self.cache_set(key, data, expire_hours * 3600)
    
    def get_cached_video_analysis(self, video_id: int, analysis_type: str) -> Optional[Dict]:
        """Get cached video analysis"""
        key = f"video_analysis:{video_id}:{analysis_type}"
        return self.cache_get(key)
    
    # ========================================
    # HEALTH CHECK AND UTILITIES
    # ========================================
    
    def health_check(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            # Test main client
            start_time = datetime.utcnow()
            self.client.ping()
            main_latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Test session client
            start_time = datetime.utcnow()
            self.session_client.ping()
            session_latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Test cache client
            start_time = datetime.utcnow()
            self.cache_client.ping()
            cache_latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Get Redis info
            info = self.client.info()
            
            return {
                "status": "healthy",
                "latency": {
                    "main": f"{main_latency:.2f}ms",
                    "sessions": f"{session_latency:.2f}ms",
                    "cache": f"{cache_latency:.2f}ms"
                },
                "memory_usage": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def clear_all_cache(self) -> bool:
        """Clear all cached data (keep sessions)"""
        try:
            return bool(self.cache_client.flushdb())
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    def clear_expired_sessions(self) -> int:
        """Clear expired sessions (manual cleanup)"""
        try:
            # Redis automatically handles TTL, but we can manually scan for cleanup
            pattern = "session:*"
            keys = self.session_client.keys(pattern)
            expired_count = 0
            
            for key in keys:
                ttl = self.session_client.ttl(key)
                if ttl == -1:  # No expiration set
                    # Set default expiration for sessions without TTL
                    self.session_client.expire(key, 24 * 3600)
                elif ttl == -2:  # Key doesn't exist (expired)
                    expired_count += 1
            
            return expired_count
        except Exception as e:
            logger.error(f"Failed to clear expired sessions: {e}")
            return 0
    
    def get_redis_stats(self) -> dict:
        """Get Redis statistics and information"""
        try:
            info = self.client.info()
            
            # Count keys in different databases
            sessions_db_keys = len(self.session_client.keys("*"))
            cache_db_keys = len(self.cache_client.keys("*"))
            
            return {
                "connected": True,
                "version": info.get("redis_version", "unknown"),
                "memory": {
                    "used_memory": info.get("used_memory", 0),
                    "used_memory_human": info.get("used_memory_human", "0B"),
                    "used_memory_peak": info.get("used_memory_peak", 0),
                    "used_memory_peak_human": info.get("used_memory_peak_human", "0B")
                },
                "stats": {
                    "total_connections_received": info.get("total_connections_received", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0),
                    "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
                    "connected_clients": info.get("connected_clients", 0)
                },
                "sessions_db_keys": sessions_db_keys,
                "cache_db_keys": cache_db_keys,
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get Redis stats: {e}")
            return {
                "connected": False,
                "error": str(e),
                "sessions_db_keys": 0,
                "cache_db_keys": 0
            }

# Global Redis service instance
redis_service = None

def get_redis_service() -> RedisService:
    """Get or create Redis service instance"""
    global redis_service
    if redis_service is None:
        redis_service = RedisService()
    return redis_service

def is_redis_available() -> bool:
    """Check if Redis is available"""
    try:
        service = get_redis_service()
        service.client.ping()
        return True
    except Exception:
        return False
