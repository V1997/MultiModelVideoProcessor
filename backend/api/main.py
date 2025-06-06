from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import uuid
import logging
from pathlib import Path
from typing import List, Optional
import shutil

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.models import get_db, create_tables, Video, TranscriptChunk, VideoFrame
from backend.video_processor.processor import VideoProcessor, is_supported_format
from backend.transcript_handler.handler import TranscriptHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MultiModel Video Processor API",
    description="API for processing videos with AI-powered analysis, embeddings, and RAG - Phase 2",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
video_processor = VideoProcessor()
transcript_handler = TranscriptHandler()

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()
    logger.info("Database tables created")

# Pydantic models for API
from pydantic import BaseModel

class VideoUploadResponse(BaseModel):
    video_id: int
    filename: str
    status: str
    message: str

class VideoProcessingStatus(BaseModel):
    video_id: int
    processed: bool
    transcript_generated: bool
    frames_extracted: bool
    status: str

class YouTubeProcessRequest(BaseModel):
    url: str
    use_whisper: bool = False
    whisper_model: str = "base"

# Phase 2 imports for embeddings and RAG
try:
    from backend.embedding_engine.engine import get_embedding_engine
    from backend.embedding_engine.rag import get_rag_system
    PHASE2_AVAILABLE = True
except ImportError:
    PHASE2_AVAILABLE = False
    logger.warning("Phase 2 components not available. Install requirements for embedding and RAG features.")

# Phase 2 Pydantic models
class EmbeddingRequest(BaseModel):
    video_ids: List[int]

class EmbeddingStatus(BaseModel):
    video_id: int
    text_embeddings_count: int
    frame_embeddings_count: int
    status: str

class SearchRequest(BaseModel):
    query: str
    video_ids: Optional[List[int]] = None
    search_type: str = "both"  # "text", "frame", or "both"
    max_results: int = 10

class SearchResult(BaseModel):
    query: str
    results: List[dict]
    total_results: int

class RAGRequest(BaseModel):
    query: str
    video_ids: Optional[List[int]] = None
    search_type: str = "both"
    max_results: int = 10

class RAGResponse(BaseModel):
    query: str
    response: str
    context: List[dict]
    video_ids: List[int]

class VideoSummaryResponse(BaseModel):
    video_id: int
    video_filename: str
    duration: float
    summary: str
    transcript_chunks: int
    frames_extracted: int

# API Routes

@app.get("/")
async def root():
    return {
        "message": "MultiModel Video Processor API - Phase 2", 
        "status": "running",
        "features": {
            "phase_1": ["video_upload", "transcript_generation", "frame_extraction", "youtube_processing"],
            "phase_2": ["vector_embeddings", "semantic_search", "multimodal_rag", "video_summarization"] if PHASE2_AVAILABLE else ["not_available"]
        },
        "version": "2.0.0"
    }

@app.get("/favicon.ico")
async def favicon():
    """Return a simple favicon to prevent 404 errors"""
    return Response(status_code=204)  # No Content - browser will use default

@app.post("/upload-video", response_model=VideoUploadResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a video file"""
    try:        # Validate file format
        if not is_supported_format(file.filename):
            supported_formats = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'm4v']
            raise HTTPException(status_code=400, detail=f"Unsupported file format. Supported formats: {', '.join(supported_formats)}")
        
        # Create temporary file
        temp_file_path = f"temp_{uuid.uuid4()}_{file.filename}"
        temp_full_path = video_processor.upload_dir / temp_file_path
        
        # Save uploaded file
        with open(temp_full_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate video file
        if not video_processor.validate_video_file(str(temp_full_path)):
            os.remove(temp_full_path)
            raise HTTPException(status_code=400, detail="Invalid video file")
        
        # Process video file
        processed_path, metadata = video_processor.process_uploaded_file(
            str(temp_full_path), file.filename
        )
        
        # Create database record
        db_video = Video(
            filename=Path(processed_path).name,
            original_filename=file.filename,
            file_path=processed_path,
            duration=metadata["duration"],
            width=metadata["width"],
            height=metadata["height"],
            fps=metadata["fps"],
            file_size=metadata["file_size"]
        )
        
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        
        # Schedule background processing
        background_tasks.add_task(process_video_background, db_video.id, processed_path)
        
        # Clean up temp file
        if os.path.exists(temp_full_path):
            os.remove(temp_full_path)
        
        return VideoUploadResponse(
            video_id=db_video.id,
            filename=db_video.filename,
            status="uploaded",
            message="Video uploaded successfully. Processing started in background."
        )
        
    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}")
        # Clean up temp file if it exists
        if 'temp_full_path' in locals() and os.path.exists(temp_full_path):
            os.remove(temp_full_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-youtube", response_model=VideoUploadResponse)
async def process_youtube_video(
    background_tasks: BackgroundTasks,
    request: YouTubeProcessRequest,
    db: Session = Depends(get_db)
):
    """Process a YouTube video URL"""
    try:
        if not transcript_handler.is_youtube_url(request.url):
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
        # Extract video ID for filename
        video_id = transcript_handler.extract_youtube_video_id(request.url)
        if not video_id:
            raise HTTPException(status_code=400, detail="Could not extract video ID from URL")
        
        # Create database record
        db_video = Video(
            filename=f"youtube_{video_id}",
            original_filename=f"youtube_{video_id}",
            file_path="",  # YouTube videos don't have local file paths
            video_url=request.url,
            duration=0,  # Will be updated after processing
            width=0,
            height=0,
            fps=0,
            file_size=0
        )
        
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        
        # Schedule background processing
        background_tasks.add_task(
            process_youtube_background, 
            db_video.id, 
            request.url, 
            request.use_whisper, 
            request.whisper_model
        )
        
        return VideoUploadResponse(
            video_id=db_video.id,
            filename=db_video.filename,
            status="processing",
            message="YouTube video processing started in background."
        )
        
    except Exception as e:
        logger.error(f"Error processing YouTube video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video/{video_id}/status", response_model=VideoProcessingStatus)
async def get_video_status(video_id: int, db: Session = Depends(get_db)):
    """Get processing status of a video"""
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        status = "processing"
        if video.processed and video.transcript_generated and video.frames_extracted:
            status = "completed"
        elif video.processed:
            status = "partially_completed"
        
        return VideoProcessingStatus(
            video_id=video.id,
            processed=video.processed,
            transcript_generated=video.transcript_generated,
            frames_extracted=video.frames_extracted,
            status=status
        )
        
    except Exception as e:
        logger.error(f"Error getting video status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video/{video_id}/transcript")
async def get_video_transcript(video_id: int, db: Session = Depends(get_db)):
    """Get transcript for a video"""
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        transcript_chunks = db.query(TranscriptChunk).filter(
            TranscriptChunk.video_id == video_id
        ).order_by(TranscriptChunk.start_time).all()
        
        return {
            "video_id": video_id,
            "video_filename": video.filename,
            "transcript_chunks": [
                {
                    "id": chunk.id,
                    "text": chunk.text,
                    "start_time": chunk.start_time,
                    "end_time": chunk.end_time,
                    "confidence": chunk.confidence
                }
                for chunk in transcript_chunks
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting transcript: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video/{video_id}/frames")
async def get_video_frames(video_id: int, db: Session = Depends(get_db)):
    """Get extracted frames for a video"""
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        frames = db.query(VideoFrame).filter(
            VideoFrame.video_id == video_id
        ).order_by(VideoFrame.timestamp).all()
        
        return {
            "video_id": video_id,
            "video_filename": video.filename,
            "frames": [
                {
                    "id": frame.id,
                    "frame_path": frame.frame_path,
                    "timestamp": frame.timestamp,
                    "frame_number": frame.frame_number,
                    "width": frame.width,
                    "height": frame.height
                }
                for frame in frames
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting frames: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/videos")
async def list_videos(db: Session = Depends(get_db)):
    """List all videos"""
    try:
        videos = db.query(Video).all()
        return {
            "videos": [
                {
                    "id": video.id,
                    "filename": video.filename,
                    "original_filename": video.original_filename,
                    "duration": video.duration,
                    "created_at": video.created_at.isoformat(),
                    "processed": video.processed,
                    "transcript_generated": video.transcript_generated,
                    "frames_extracted": video.frames_extracted
                }
                for video in videos
            ]
        }
    except Exception as e:
        logger.error(f"Error listing videos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ===============================
# PHASE 2: VECTOR EMBEDDINGS & RAG API ENDPOINTS
# ===============================

@app.post("/api/v1/embeddings/generate", response_model=List[EmbeddingStatus])
async def generate_embeddings(
    request: EmbeddingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate embeddings for video content"""
    if not PHASE2_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 2 features not available. Install embedding requirements.")
    
    try:
        # Validate video IDs
        valid_videos = []
        for video_id in request.video_ids:
            video = db.query(Video).filter(Video.id == video_id).first()
            if video:
                valid_videos.append(video_id)
            else:
                logger.warning(f"Video {video_id} not found")
        
        if not valid_videos:
            raise HTTPException(status_code=400, detail="No valid video IDs provided")
        
        # Start background embedding generation
        for video_id in valid_videos:
            background_tasks.add_task(generate_embeddings_background, video_id)
        
        # Return initial status
        results = []
        for video_id in valid_videos:
            results.append(EmbeddingStatus(
                video_id=video_id,
                text_embeddings_count=0,
                frame_embeddings_count=0,
                status="processing"
            ))
        
        return results
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/embeddings/status/{video_id}", response_model=EmbeddingStatus)
async def get_embedding_status(video_id: int, db: Session = Depends(get_db)):
    """Get embedding generation status for a video"""
    if not PHASE2_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 2 features not available")
    
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Count existing embeddings (this is a simplified check)
        transcript_count = db.query(TranscriptChunk).filter(TranscriptChunk.video_id == video_id).count()
        frame_count = db.query(VideoFrame).filter(VideoFrame.video_id == video_id).count()
        
        return EmbeddingStatus(
            video_id=video_id,
            text_embeddings_count=transcript_count,
            frame_embeddings_count=frame_count,
            status="completed" if transcript_count > 0 or frame_count > 0 else "pending"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting embedding status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/search/semantic", response_model=SearchResult)
async def semantic_search(request: SearchRequest):
    """Perform semantic search across video content"""
    if not PHASE2_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 2 features not available")
    
    try:
        embedding_engine = await get_embedding_engine()
        
        # Generate query embedding
        query_embedding = await embedding_engine.generate_text_embeddings([request.query])
        
        # Search for similar content
        results = await embedding_engine.search_similar_content(
            query_embedding[0],
            content_type=request.search_type,
            limit=request.max_results,
            video_id=request.video_ids[0] if request.video_ids and len(request.video_ids) == 1 else None
        )
        
        return SearchResult(
            query=request.query,
            results=results,
            total_results=len(results)
        )
        
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/query/multimodal", response_model=RAGResponse)
async def multimodal_query(request: RAGRequest):
    """Ask questions about video content using RAG"""
    if not PHASE2_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 2 features not available")
    
    try:
        # Get OpenAI API key from environment
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        rag_system = await get_rag_system(openai_api_key)
        
        # Process the query
        result = await rag_system.process_query(
            query=request.query,
            video_ids=request.video_ids,
            search_type=request.search_type,
            max_results=request.max_results
        )
        
        return RAGResponse(
            query=result["query"],
            response=result["response"],
            context=result["context"],
            video_ids=result["video_ids"]
        )
        
    except Exception as e:
        logger.error(f"Error in multimodal query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/video/{video_id}/summary", response_model=VideoSummaryResponse)
async def get_video_summary(video_id: int, db: Session = Depends(get_db)):
    """Generate a comprehensive summary of a video"""
    if not PHASE2_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 2 features not available")
    
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Get OpenAI API key from environment
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        rag_system = await get_rag_system(openai_api_key)
        
        # Generate summary
        summary_result = await rag_system.summarize_video(video_id)
        
        return VideoSummaryResponse(**summary_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating video summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/similarity/find/{video_id}")
async def find_similar_videos(video_id: int, limit: int = 5, db: Session = Depends(get_db)):
    """Find videos similar to the given video"""
    if not PHASE2_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 2 features not available")
    
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # This is a placeholder for video-to-video similarity
        # In full implementation, you would:
        # 1. Get the average embedding for the video
        # 2. Search for similar videos using that embedding
        # 3. Return ranked results
        
        return {
            "video_id": video_id,
            "similar_videos": [],
            "message": "Video similarity feature coming soon"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background processing functions
async def process_video_background(video_id: int, video_path: str):
    """Background task to process uploaded video"""
    db = next(get_db())
    try:
        logger.info(f"Starting background processing for video {video_id}")
        
        # Generate transcript
        transcript_chunks = transcript_handler.transcribe_video_file(video_path)
        
        # Save transcript chunks to database
        for chunk in transcript_chunks:
            db_chunk = TranscriptChunk(
                video_id=video_id,
                text=chunk["text"],
                start_time=chunk["start_time"],
                end_time=chunk["end_time"],
                confidence=chunk["confidence"]
            )
            db.add(db_chunk)
        
        # Extract frames
        frames_data = video_processor.extract_frames(video_path, video_id, fps=1.0)
        
        # Save frame data to database
        for frame_data in frames_data:
            db_frame = VideoFrame(
                video_id=video_id,
                frame_path=frame_data["frame_path"],
                timestamp=frame_data["timestamp"],
                frame_number=frame_data["frame_number"],
                width=frame_data["width"],
                height=frame_data["height"]
            )
            db.add(db_frame)
        
        # Update video status
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.processed = True
            video.transcript_generated = True
            video.frames_extracted = True
        
        db.commit()
        logger.info(f"Successfully processed video {video_id}")
        
    except Exception as e:
        logger.error(f"Error in background processing for video {video_id}: {str(e)}")
        # Update video with error status
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.processed = False
        db.commit()
    finally:
        db.close()

async def process_youtube_background(video_id: int, video_url: str, use_whisper: bool = False, model_size: str = "base"):
    """Background task to process YouTube video"""
    db = next(get_db())
    try:
        logger.info(f"Starting background processing for YouTube video {video_id}")
        
        # Get transcript and metadata
        transcript_chunks, metadata = transcript_handler.process_youtube_video(
            video_url, use_whisper, model_size
        )
        
        # Update video metadata
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.duration = metadata.get("duration", 0)
            video.width = metadata.get("width", 0)
            video.height = metadata.get("height", 0)
            video.fps = metadata.get("fps", 0)
        
        # Save transcript chunks to database
        for chunk in transcript_chunks:
            db_chunk = TranscriptChunk(
                video_id=video_id,
                text=chunk["text"],
                start_time=chunk["start_time"],
                end_time=chunk["end_time"],
                confidence=chunk["confidence"]
            )
            db.add(db_chunk)
        
        # Update video status
        if video:
            video.processed = True
            video.transcript_generated = True
            video.frames_extracted = False  # YouTube videos don't extract frames in Phase 1
        
        db.commit()
        logger.info(f"Successfully processed YouTube video {video_id}")
        
    except Exception as e:
        logger.error(f"Error in background processing for YouTube video {video_id}: {str(e)}")
        # Update video with error status
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.processed = False
        db.commit()
    finally:
        db.close()

# Background task for embedding generation
async def generate_embeddings_background(video_id: int):
    """Background task to generate embeddings for a video"""
    try:
        embedding_engine = await get_embedding_engine()
        await embedding_engine.process_video_embeddings(video_id)
        logger.info(f"Completed embedding generation for video {video_id}")
        
    except Exception as e:
        logger.error(f"Error in background embedding generation for video {video_id}: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
