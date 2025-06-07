from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./multimodal_video.db")

Base = declarative_base()

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    original_filename = Column(String)
    file_path = Column(String)
    video_url = Column(String, nullable=True)  # For YouTube links
    duration = Column(Float)
    width = Column(Integer)
    height = Column(Integer)
    fps = Column(Float)
    file_size = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    transcript_generated = Column(Boolean, default=False)
    frames_extracted = Column(Boolean, default=False)
    
    # Relationships
    transcript_chunks = relationship("TranscriptChunk", back_populates="video")
    frames = relationship("VideoFrame", back_populates="video")
    chat_sessions = relationship("ChatSession", back_populates="video")
    detected_objects = relationship("ObjectDetection", back_populates="video")
    topic_segments = relationship("TopicSegment", back_populates="video")

class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey('videos.id'), index=True)
    text = Column(Text)
    start_time = Column(Float)
    end_time = Column(Float)
    confidence = Column(Float, nullable=True)
    speaker = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    video = relationship("Video", back_populates="transcript_chunks")

class VideoFrame(Base):
    __tablename__ = "video_frames"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey('videos.id'), index=True)
    frame_path = Column(String)
    timestamp = Column(Float)
    frame_number = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    video = relationship("Video", back_populates="frames")
    detected_objects = relationship("ObjectDetection", back_populates="frame")

# Phase 3: Conversational Interface Models

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey('videos.id'), index=True)
    session_id = Column(String, unique=True, index=True)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    video = relationship("Video", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    context = relationship("ConversationContext", back_populates="session", uselist=False)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('chat_sessions.id'), index=True)
    role = Column(String)  # 'user' or 'assistant'
    content = Column(Text)
    timestamp_references = Column(JSON, nullable=True)  # List of referenced timestamps
    frame_references = Column(JSON, nullable=True)  # List of referenced frame IDs
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class ConversationContext(Base):
    __tablename__ = "conversation_contexts"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('chat_sessions.id'), index=True)
    context_summary = Column(Text, nullable=True)
    key_topics = Column(JSON, nullable=True)  # List of discussed topics
    referenced_segments = Column(JSON, nullable=True)  # Transcript segments referenced
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="context")

# Phase 4: Visual Search Engine Models

class ObjectDetection(Base):
    __tablename__ = "object_detections"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey('videos.id'), index=True)
    frame_id = Column(Integer, ForeignKey('video_frames.id'), index=True)
    object_class = Column(String, index=True)
    confidence = Column(Float)
    bbox_x = Column(Float)  # Bounding box coordinates
    bbox_y = Column(Float)
    bbox_width = Column(Float)
    bbox_height = Column(Float)
    attributes = Column(JSON, nullable=True)  # Additional attributes like color, size
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    video = relationship("Video", back_populates="detected_objects")
    frame = relationship("VideoFrame", back_populates="detected_objects")

class SceneClassification(Base):
    __tablename__ = "scene_classifications"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey('videos.id'), index=True)
    start_time = Column(Float)
    end_time = Column(Float)
    scene_type = Column(String, index=True)
    confidence = Column(Float)
    description = Column(Text, nullable=True)
    features = Column(JSON, nullable=True)  # Scene features and attributes
    created_at = Column(DateTime, default=datetime.utcnow)

# Phase 5: Navigation & User Interface Models

class TopicSegment(Base):
    __tablename__ = "topic_segments"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey('videos.id'), index=True)
    start_time = Column(Float)
    end_time = Column(Float)
    topic_title = Column(String)
    topic_summary = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True)  # Key terms for this segment
    importance_score = Column(Float, nullable=True)
    parent_segment_id = Column(Integer, ForeignKey('topic_segments.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    video = relationship("Video", back_populates="topic_segments")
    children = relationship("TopicSegment", backref="parent", remote_side=[id])

class ContentOutline(Base):
    __tablename__ = "content_outlines"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey('videos.id'), index=True)
    outline_data = Column(JSON)  # Hierarchical outline structure
    generated_method = Column(String)  # How the outline was generated
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NavigationEvent(Base):
    __tablename__ = "navigation_events"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey('videos.id'), index=True)
    event_type = Column(String, index=True)  # 'topic_change', 'scene_change', 'speaker_change'
    timestamp = Column(Float)
    description = Column(String, nullable=True)
    event_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' to avoid conflict
    created_at = Column(DateTime, default=datetime.utcnow)

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
