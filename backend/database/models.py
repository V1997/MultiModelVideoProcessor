from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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

class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, index=True)
    text = Column(Text)
    start_time = Column(Float)
    end_time = Column(Float)
    confidence = Column(Float, nullable=True)
    speaker = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class VideoFrame(Base):
    __tablename__ = "video_frames"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, index=True)
    frame_path = Column(String)
    timestamp = Column(Float)
    frame_number = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
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
