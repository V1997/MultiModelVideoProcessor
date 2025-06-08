from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import uuid
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import shutil
from dotenv import load_dotenv

import sys
from pathlib import Path

# Load environment variables
load_dotenv()

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.models import get_db, create_tables, Video, TranscriptChunk, VideoFrame
from backend.video_processor.processor import VideoProcessor, is_supported_format
from backend.transcript_handler.handler import TranscriptHandler
from backend.services.redis_service import get_redis_service, is_redis_available
from backend.services.celery_app import celery_app
from backend.services.websocket_service import get_websocket_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MultiModel Video Processor API",
    description="API for processing videos with AI-powered analysis, embeddings, and RAG - Phase 3-5 with Redis",
    version="3.0.0"
)

# Initialize WebSocket service
websocket_service = get_websocket_service()
sio = websocket_service.get_app()

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

# Initialize Redis service
redis_service = None
redis_available = False

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    global redis_service, redis_available
    
    create_tables()
    logger.info("Database tables created")
    
    # Initialize Redis
    try:
        redis_available = is_redis_available()
        if redis_available:
            redis_service = get_redis_service()
            logger.info("Redis service initialized successfully")
        else:
            logger.warning("Redis not available - running without caching")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        redis_available = False

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

class YouTubeSearchRequest(BaseModel):
    query: str
    max_results: int = 10
    duration: Optional[str] = None  # short, medium, long
    order: str = "relevance"  # relevance, date, rating, viewCount

class YouTubeVideoInfo(BaseModel):
    video_id: str
    title: str
    description: str
    thumbnail_url: str
    duration: str
    view_count: int
    published_at: str
    channel_title: str
    url: str

class EmbeddingRequest(BaseModel):
    video_id: int
    chunk_size: int = 1000
    overlap: int = 200

class EmbeddingStatus(BaseModel):
    video_id: int
    status: str

class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: Optional[dict] = None
    result: Optional[dict] = None
    error: Optional[str] = None

class ConversationStartRequest(BaseModel):
    video_id: int

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    video_id: Optional[int] = None
    chunks_processed: int
    total_chunks: int
    progress: float

class SearchResult(BaseModel):
    video_id: int
    chunk_text: str
    timestamp: Optional[float]
    similarity_score: float

class SearchRequest(BaseModel):
    query: str
    video_id: Optional[int] = None
    top_k: int = 5

class RAGRequest(BaseModel):
    query: str
    video_id: int
    include_visual: bool = False

class ChatSessionCreate(BaseModel):
    video_id: str
    title: Optional[str] = None

class ChatMessageRequest(BaseModel):
    message: str

class VisualSearchRequest(BaseModel):
    video_id: int
    query: str
    confidence_threshold: float = 0.3

class RAGResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[str]
    timestamp_citations: List[dict]

class VideoSummaryResponse(BaseModel):
    video_id: int
    summary: str
    key_topics: List[str]
    duration_summary: str

class ChatSessionResponse(BaseModel):
    session_id: str
    video_id: str
    status: str

class ChatMessageResponse(BaseModel):
    message_id: str
    response: str
    confidence: float
    timestamp_citations: List[dict]

class VisualSearchResponse(BaseModel):
    video_id: str
    results: List[dict]
    total_matches: int

class TopicSegmentResponse(BaseModel):
    video_id: str
    segments: List[dict]
    total_segments: int

class ContentOutlineResponse(BaseModel):
    video_id: str
    outline: dict
    chapters: List[dict]

# Phase 2 imports for embeddings and RAG
try:
    from backend.embedding_engine.engine import get_embedding_engine
    from backend.embedding_engine.rag import get_rag_system
    PHASE2_AVAILABLE = True
except ImportError:
    PHASE2_AVAILABLE = False
    logger.warning("Phase 2 components not available. Install requirements for embedding and RAG features.")

# =============================================================================
# PHASE 3-5 API ENDPOINTS: Chat, Visual Search, Content Segmentation
# =============================================================================

try:
    from backend.conversation.manager import ConversationManager
    from backend.visual_search.engine import VisualSearchEngine
    from backend.content_analysis.segmentation import ContentSegmentationEngine
    from backend.embedding_engine.rag import get_rag_system
    PHASE3_TO_5_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Phase 3-5 features not available: {e}")
    PHASE3_TO_5_AVAILABLE = False

# Initialize Phase 3-5 components
conversation_manager = None
visual_search_engine = None
content_segmentation_engine = None

@app.on_event("startup")
async def initialize_phase3_to_5():
    """Initialize Phase 3-5 components"""
    global conversation_manager, visual_search_engine, content_segmentation_engine
    
    if PHASE3_TO_5_AVAILABLE:
        try:
            # Initialize RAG system
            openai_api_key = os.getenv("OPENAI_API_KEY")
            rag_system = await get_rag_system(openai_api_key)
            # Initialize components
            conversation_manager = ConversationManager(rag_system, websocket_service)
            visual_search_engine = VisualSearchEngine()
            content_segmentation_engine = ContentSegmentationEngine()
            
            logger.info("Phase 3-5 components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Phase 3-5 components: {e}")

# Chat Session Endpoints
@app.post("/api/v1/chat/sessions")
async def create_chat_session(video_id: int, title: Optional[str] = None, db: Session = Depends(get_db)):
    """Create a new chat session for a video"""
    if not PHASE3_TO_5_AVAILABLE or not conversation_manager:
        raise HTTPException(status_code=501, detail="Chat features not available")
    
    try:
        session = conversation_manager.create_session(db, video_id, title)
        return {
            "session_id": session.session_id,
            "video_id": session.video_id,
            "title": session.title,
            "created_at": session.created_at
        }
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/chat/sessions/{session_id}")
async def get_chat_session(session_id: str, db: Session = Depends(get_db)):
    """Get chat session details"""
    if not PHASE3_TO_5_AVAILABLE or not conversation_manager:
        raise HTTPException(status_code=501, detail="Chat features not available")
    
    try:
        session = conversation_manager.get_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session.session_id,
            "video_id": session.video_id,
            "title": session.title,
            "created_at": session.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat/sessions/{session_id}/messages")
async def send_chat_message(session_id: str, request: ChatMessageRequest, db: Session = Depends(get_db)):
    """Send a message to a chat session"""
    if not PHASE3_TO_5_AVAILABLE or not conversation_manager:
        raise HTTPException(status_code=501, detail="Chat features not available")
    
    try:
        session = conversation_manager.get_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Generate response using conversation manager
        response_data = await conversation_manager.generate_enhanced_response(
            db, session_id, request.message, session.video_id
        )
        
        return {
            "message_id": response_data.get('message_id'),
            "response": response_data.get('response'),
            "timestamp_citations": response_data.get('timestamp_citations', []),
            "frame_references": response_data.get('frame_references', []),
            "confidence": response_data.get('confidence', 0.0)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Visual Search Endpoints
@app.post("/api/v1/visual-search/detect-objects")
async def detect_objects_endpoint(video_id: int, frame_path: str, confidence_threshold: float = 0.5, db: Session = Depends(get_db)):
    """Detect objects in a video frame"""
    if not PHASE3_TO_5_AVAILABLE or not visual_search_engine:
        raise HTTPException(status_code=501, detail="Visual search features not available")
    
    try:
        results = visual_search_engine.detect_objects_in_frame(frame_path, confidence_threshold)
        return {"objects": results, "frame_path": frame_path}
    except Exception as e:
        logger.error(f"Error detecting objects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/visual-search/search/{video_id}")
async def visual_search_endpoint(video_id: int, request: VisualSearchRequest, db: Session = Depends(get_db)):
    """Search for visual content using natural language"""
    if not PHASE3_TO_5_AVAILABLE or not visual_search_engine:
        raise HTTPException(status_code=501, detail="Visual search features not available")
    
    try:
        results = visual_search_engine.search_visual_content(db, video_id, request.query)
        return {"query": request.query, "results": results}
    except Exception as e:
        logger.error(f"Error in visual search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Content Segmentation Endpoints
@app.post("/api/v1/content/analyze-topics")
async def analyze_topics_endpoint(video_id: int, db: Session = Depends(get_db)):
    """Analyze video transcript to identify topic segments"""
    if not PHASE3_TO_5_AVAILABLE or not content_segmentation_engine:
        raise HTTPException(status_code=501, detail="Content analysis features not available")
    
    try:
        results = content_segmentation_engine.analyze_transcript_topics(db, video_id)
        return {"video_id": video_id, "topics": results}
    except Exception as e:
        logger.error(f"Error analyzing topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/content/generate-outline")
async def generate_outline_endpoint(video_id: int, db: Session = Depends(get_db)):
    """Generate content outline for video navigation"""
    if not PHASE3_TO_5_AVAILABLE or not content_segmentation_engine:
        raise HTTPException(status_code=501, detail="Content analysis features not available")
    
    try:
        outline = content_segmentation_engine.generate_content_outline(db, video_id)
        return {"video_id": video_id, "outline": outline}
    except Exception as e:
        logger.error(f"Error generating outline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/content/navigation/{video_id}")
async def get_navigation_data_api(video_id: int, db: Session = Depends(get_db)):
    """Get navigation data for video player"""
    if not PHASE3_TO_5_AVAILABLE or not content_segmentation_engine:
        raise HTTPException(status_code=501, detail="Content analysis features not available")
    
    try:
        nav_data = content_segmentation_engine.get_video_navigation_data(db, video_id)
        return nav_data
    except Exception as e:
        logger.error(f"Error getting navigation data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {
        "message": "MultiModel Video Processor API - Phase 3-5 with Redis", 
        "status": "running",
        "redis_available": redis_available,
        "features": {
            "phase_1": ["video_upload", "transcript_generation", "frame_extraction", "youtube_processing"],
            "phase_2": ["vector_embeddings", "semantic_search", "multimodal_rag", "video_summarization"] if PHASE2_AVAILABLE else ["not_available"],
            "phase_3": ["conversational_interface", "context_aware_chat", "timestamp_citations"] if PHASE3_TO_5_AVAILABLE else ["not_available"],
            "phase_4": ["visual_search", "object_detection", "scene_classification"] if PHASE3_TO_5_AVAILABLE else ["not_available"],
            "phase_5": ["content_segmentation", "auto_outlines", "navigation_events"] if PHASE3_TO_5_AVAILABLE else ["not_available"],
            "caching": ["session_storage", "response_caching", "video_analysis_cache"] if redis_available else ["not_available"]
        },
        "version": "3.0.0"
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check including Redis"""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "healthy",
            "redis": "not_available"
        }
    }
    
    # Check Redis health
    if redis_available and redis_service:
        try:
            redis_health = redis_service.health_check()
            health_data["services"]["redis"] = redis_health["status"]
            health_data["redis_details"] = redis_health
        except Exception as e:
            health_data["services"]["redis"] = "unhealthy"
            health_data["redis_error"] = str(e)
    
    return health_data

@app.get("/redis/status")
async def redis_status():
    """Detailed Redis status and statistics"""
    if not redis_available:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        return redis_service.health_check()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis health check failed: {str(e)}")

@app.post("/redis/cache/clear")
async def clear_redis_cache():
    """Clear all Redis cache (keep sessions)"""
    if not redis_available:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        success = redis_service.clear_all_cache()
        if success:
            return {"message": "Cache cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@app.get("/favicon.ico")
async def favicon():
    """Return a simple favicon to prevent 404 errors"""
    return Response(status_code=204)  # No Content - browser will use default

@app.post("/upload-video", response_model=TaskResponse)
async def upload_video(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Upload and process a video file"""
    try:
        # Validate file format
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
        
        # Schedule Celery background processing
        if redis_available:
            task = celery_app.send_task('video.process', args=[db_video.id, processed_path])
            
            # Broadcast processing start status via WebSocket
            try:
                await websocket_service.broadcast_processing_status(
                    db_video.id, 
                    {
                        "status": "started",
                        "progress": 0,
                        "message": f"Video processing started for {file.filename}",
                        "task_id": task.id
                    }
                )
            except Exception as ws_error:
                logger.warning(f"Failed to broadcast WebSocket status: {ws_error}")
            
            # Clean up temp file
            if os.path.exists(temp_full_path):
                os.remove(temp_full_path)
                
            return TaskResponse(
                task_id=task.id,
                status="processing",
                message=f"Video uploaded successfully. Processing started with task ID: {task.id}",
                video_id=db_video.id,
                chunks_processed=0,
                total_chunks=0,
                progress=0.0
            )
        else:
            # Fallback to FastAPI BackgroundTasks if Redis not available
            background_tasks.add_task(process_video_background, db_video.id, processed_path)
            
            # Clean up temp file
            if os.path.exists(temp_full_path):
                os.remove(temp_full_path)
                
            return TaskResponse(
                task_id="fallback",
                status="processing",
                message="Video uploaded successfully. Processing started in background (fallback mode).",
                video_id=db_video.id,
                chunks_processed=0,
                total_chunks=0,
                progress=0.0
            )
        
    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}")
        # Clean up temp file if it exists
        if 'temp_full_path' in locals() and os.path.exists(temp_full_path):
            os.remove(temp_full_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-youtube", response_model=TaskResponse)
async def process_youtube_video(
    request: YouTubeProcessRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
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
        
        # Check if video already exists
        filename = f"youtube_{video_id}"
        existing_video = db.query(Video).filter(Video.filename == filename).first()
        
        if existing_video:
            # Video already exists, return existing video info
            return TaskResponse(
                task_id=f"existing_{existing_video.id}",
                status="completed" if existing_video.processed else "processing",
                message=f"Video already exists with ID: {existing_video.id}",
                video_id=existing_video.id,
                chunks_processed=1 if existing_video.transcript_generated else 0,
                total_chunks=1,
                progress=1.0 if existing_video.processed else 0.5
            )
        
        # Create database record for new video
        db_video = Video(
            filename=filename,
            original_filename=filename,
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
        
        # Schedule Celery background processing
        if redis_available:
            task = celery_app.send_task('youtube.process', args=[
                db_video.id, request.url, request.use_whisper, request.whisper_model
            ])
            
            # Broadcast processing start status via WebSocket
            try:
                await websocket_service.broadcast_processing_status(
                    db_video.id, 
                    {
                        "status": "started",
                        "progress": 0,
                        "message": f"YouTube video processing started for {request.url}",
                        "task_id": task.id
                    }
                )
            except Exception as ws_error:
                logger.warning(f"Failed to broadcast WebSocket status: {ws_error}")
            
            return TaskResponse(
                task_id=task.id,
                status="processing",
                message=f"YouTube processing started with task ID: {task.id}",
                video_id=db_video.id,
                chunks_processed=0,
                total_chunks=0,
                progress=0.0
            )
        else:
            # Fallback to FastAPI BackgroundTasks if Redis not available
            background_tasks.add_task(
                process_youtube_background, 
                db_video.id,
                request.url, 
                request.use_whisper, 
                request.whisper_model
            )
            
            return TaskResponse(
                task_id="fallback",
                status="processing",
                message="YouTube video processing started in background (fallback mode).",
                video_id=db_video.id,
                chunks_processed=0,
                total_chunks=0,
                progress=0.0
            )
        
    except Exception as e:
        logger.error(f"Error processing YouTube video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/youtube/search")
async def search_youtube_videos(request: YouTubeSearchRequest):
    """Search YouTube videos using the YouTube Data API"""
    try:
        from backend.youtube_search.service import YouTubeSearchService
        
        search_service = YouTubeSearchService()
        results = search_service.search_videos(
            query=request.query,
            max_results=request.max_results,
            duration=request.duration,
            order=request.order
        )
        
        return {
            "query": request.query,
            "total_results": len(results),
            "videos": [YouTubeVideoInfo(**video) for video in results]
        }
        
    except Exception as e:
        logger.error(f"Error searching YouTube videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/youtube/info")
async def get_youtube_video_info(url: str):
    """Get information about a specific YouTube video"""
    try:
        from backend.youtube_search.service import YouTubeSearchService
        
        search_service = YouTubeSearchService()
        video_info = search_service.get_video_info(url)
        
        if not video_info:
            raise HTTPException(status_code=404, detail="Video not found or invalid URL")
        
        return YouTubeVideoInfo(**video_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting YouTube video info: {e}")
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
    """Get transcript for a video with Redis caching"""
    try:
        # Check Redis cache first
        if redis_available and redis_service:
            cached_transcript = redis_service.get_cached_video_analysis(video_id, "transcript")
            if cached_transcript:
                logger.info(f"Retrieved transcript for video {video_id} from Redis cache")
                return cached_transcript
        
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        transcript_chunks = db.query(TranscriptChunk).filter(
            TranscriptChunk.video_id == video_id
        ).order_by(TranscriptChunk.start_time).all()
        
        transcript_data = {
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
        
        # Cache in Redis for 24 hours
        if redis_available and redis_service and transcript_chunks:
            redis_service.cache_video_analysis(video_id, "transcript", transcript_data, expire_hours=24)
            logger.info(f"Cached transcript for video {video_id} in Redis")
        
        return transcript_data
        
    except Exception as e:
        logger.error(f"Error getting transcript: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video/{video_id}/frames")
async def get_video_frames(video_id: int, db: Session = Depends(get_db)):
    """Get extracted frames for a video with Redis caching"""
    try:
        # Check Redis cache first
        if redis_available and redis_service:
            cached_frames = redis_service.get_cached_video_analysis(video_id, "frames")
            if cached_frames:
                logger.info(f"Retrieved frames for video {video_id} from Redis cache")
                return cached_frames
        
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        frames = db.query(VideoFrame).filter(
            VideoFrame.video_id == video_id
        ).order_by(VideoFrame.timestamp).all()
        
        frames_data = {
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
        
        # Cache in Redis for 24 hours
        if redis_available and redis_service and frames:
            redis_service.cache_video_analysis(video_id, "frames", frames_data, expire_hours=24)
            logger.info(f"Cached frames for video {video_id} in Redis")
        
        return frames_data
        
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

@app.post("/api/v1/embeddings/generate", response_model=TaskResponse)
async def generate_embeddings(
    request: EmbeddingRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Generate embeddings for video content"""
    if not PHASE2_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 2 features not available. Install embedding requirements.")
    
    try:
        # Validate video ID
        video = db.query(Video).filter(Video.id == request.video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail=f"Video {request.video_id} not found")
        
        # Start Celery background embedding generation
        if redis_available:
            task = celery_app.send_task('embeddings.generate', args=[request.video_id])
            
            return TaskResponse(
                task_id=task.id,
                status="processing",
                message=f"Embedding generation started with task ID: {task.id}",
                video_id=request.video_id,
                chunks_processed=0,
                total_chunks=0,
                progress=0.0
            )
        else:
            # Fallback to FastAPI BackgroundTasks if Redis not available
            background_tasks.add_task(generate_embeddings_background, request.video_id)
            
            return TaskResponse(
                task_id="fallback",
                status="processing",
                message="Embedding generation started in background (fallback mode).",
                video_id=request.video_id,
                chunks_processed=0,
                total_chunks=0,
                progress=0.0
            )
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
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

# ===============================
# TASK STATUS MANAGEMENT
# ===============================

@app.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get the status of a background task"""
    if not redis_available:
        raise HTTPException(status_code=503, detail="Redis not available - cannot check task status")
    
    try:
        # Get task result from Celery
        result = celery_app.AsyncResult(task_id)
        
        if result.state == 'PENDING':
            response = {
                "task_id": task_id,
                "status": "pending",
                "progress": None,
                "result": None,
                "error": None
            }
        elif result.state == 'PROGRESS':
            response = {
                "task_id": task_id,
                "status": "processing",
                "progress": result.info,
                "result": None,
                "error": None
            }
        elif result.state == 'SUCCESS':
            response = {
                "task_id": task_id,
                "status": "completed",
                "progress": None,
                "result": result.result,
                "error": None
            }
        else:  # FAILURE
            response = {
                "task_id": task_id,
                "status": "failed",
                "progress": None,
                "result": None,
                "error": str(result.info)
            }
        
        return TaskStatus(**response)
        
    except Exception as e:
        logger.error(f"Error checking task status: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking task status: {str(e)}")

# WebSocket status endpoints for debugging
@app.get("/api/v1/websocket/status")
async def websocket_status():
    """Get WebSocket service status"""
    return {
        "connected_clients": websocket_service.get_connected_clients_count(),
        "socket_io_initialized": sio is not None,
        "service_status": "running"
    }

@app.get("/api/v1/websocket/connections")
async def websocket_connections():
    """Get active WebSocket connections"""
    return {
        "active_connections": websocket_service.get_connected_clients_count(),
        "session_rooms": len(websocket_service.session_rooms),        "service_initialized": True    }

# Create Socket.IO ASGI app that wraps the FastAPI app (must be after all routes)
import socketio
socket_app = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path="socket.io")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)  # Run socket_app instead of app