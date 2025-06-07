"""
Configuration settings for Phase 3-5 features
"""

import os
from typing import Dict, Any
from pydantic import BaseSettings, Field

class Phase3To5Config(BaseSettings):
    """Configuration for Phase 3-5 features"""
    
    # Phase 3: Conversational Interface
    conversation_context_window: int = Field(default=10, description="Number of messages to keep in context")
    conversation_max_response_tokens: int = Field(default=1000, description="Maximum tokens in AI response")
    conversation_temperature: float = Field(default=0.7, description="AI response creativity temperature")
    timestamp_citation_threshold: float = Field(default=0.7, description="Minimum confidence for timestamp citations")
    
    # Phase 4: Visual Search Engine
    object_detection_confidence_threshold: float = Field(default=0.5, description="Minimum confidence for object detection")
    scene_classification_top_k: int = Field(default=5, description="Number of top scene classifications to return")
    visual_search_cache_ttl: int = Field(default=3600, description="Visual search cache TTL in seconds")
    
    # Phase 5: Navigation & User Interface
    content_segmentation_min_segment_length: int = Field(default=30, description="Minimum segment length in seconds")
    content_segmentation_similarity_threshold: float = Field(default=0.3, description="Similarity threshold for topic changes")
    outline_max_depth: int = Field(default=3, description="Maximum outline hierarchy depth")
    navigation_event_batch_size: int = Field(default=100, description="Batch size for navigation event processing")
    
    # Performance settings
    enable_background_processing: bool = Field(default=True, description="Enable background task processing")
    max_concurrent_tasks: int = Field(default=5, description="Maximum concurrent background tasks")
    task_timeout_seconds: int = Field(default=300, description="Task timeout in seconds")
    
    # API settings
    api_rate_limit_per_minute: int = Field(default=100, description="API rate limit per minute per user")
    enable_request_logging: bool = Field(default=True, description="Enable detailed request logging")
    
    # Model settings
    openai_model: str = Field(default="gpt-3.5-turbo", description="OpenAI model for conversational interface")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Sentence transformer model for embeddings")
    visual_model: str = Field(default="yolov8n", description="YOLO model for object detection")
    
    # File storage
    visual_search_cache_dir: str = Field(default="./cache/visual_search", description="Visual search cache directory")
    conversation_logs_dir: str = Field(default="./logs/conversations", description="Conversation logs directory")
    
    class Config:
        env_prefix = "PHASE3TO5_"
        case_sensitive = False

# Global configuration instance
config = Phase3To5Config()

def get_config() -> Phase3To5Config:
    """Get the global configuration instance"""
    return config

def update_config(**kwargs) -> None:
    """Update configuration values"""
    global config
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f"Unknown configuration key: {key}")

# Configuration validation
def validate_config() -> Dict[str, Any]:
    """Validate current configuration and return any issues"""
    issues = []
    
    # Validate thresholds
    if not 0.0 <= config.timestamp_citation_threshold <= 1.0:
        issues.append("timestamp_citation_threshold must be between 0.0 and 1.0")
    
    if not 0.0 <= config.object_detection_confidence_threshold <= 1.0:
        issues.append("object_detection_confidence_threshold must be between 0.0 and 1.0")
    
    if not 0.0 <= config.content_segmentation_similarity_threshold <= 1.0:
        issues.append("content_segmentation_similarity_threshold must be between 0.0 and 1.0")
    
    # Validate positive integers
    positive_int_fields = [
        "conversation_context_window",
        "conversation_max_response_tokens", 
        "scene_classification_top_k",
        "visual_search_cache_ttl",
        "content_segmentation_min_segment_length",
        "outline_max_depth",
        "navigation_event_batch_size",
        "max_concurrent_tasks",
        "task_timeout_seconds",
        "api_rate_limit_per_minute"
    ]
    
    for field in positive_int_fields:
        value = getattr(config, field)
        if not isinstance(value, int) or value <= 0:
            issues.append(f"{field} must be a positive integer")
    
    # Validate temperature
    if not 0.0 <= config.conversation_temperature <= 2.0:
        issues.append("conversation_temperature must be between 0.0 and 2.0")
    
    # Check directories exist or can be created
    dirs_to_check = [config.visual_search_cache_dir, config.conversation_logs_dir]
    for dir_path in dirs_to_check:
        try:
            os.makedirs(dir_path, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create directory {dir_path}: {str(e)}")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "config": config.dict()
    }

# Initialize directories on import
try:
    os.makedirs(config.visual_search_cache_dir, exist_ok=True)
    os.makedirs(config.conversation_logs_dir, exist_ok=True)
except Exception:
    pass  # Will be caught in validation
