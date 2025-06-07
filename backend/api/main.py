from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import uuid
import logging
from pathlib import Path
from typing import List, Optional
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
    session_id: str
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
            conversation_manager = ConversationManager(rag_system)
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
async def get_navigation_data(video_id: int, db: Session = Depends(get_db)):
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
        "message": "MultiModel Video Processor API - Phase 3-5", 
        "status": "running",
        "features": {
            "phase_1": ["video_upload", "transcript_generation", "frame_extraction", "youtube_processing"],
            "phase_2": ["vector_embeddings", "semantic_search", "multimodal_rag", "video_summarization"] if PHASE2_AVAILABLE else ["not_available"],
            "phase_3": ["conversational_interface", "context_aware_chat", "timestamp_citations"] if PHASE3_TO_5_AVAILABLE else ["not_available"],
            "phase_4": ["visual_search", "object_detection", "scene_classification"] if PHASE3_TO_5_AVAILABLE else ["not_available"],
            "phase_5": ["content_segmentation", "auto_outlines", "navigation_events"] if PHASE3_TO_5_AVAILABLE else ["not_available"]
        },
        "version": "3.0.0"
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

# ===============================
# PHASE 3-5: ADVANCED FEATURES API ENDPOINTS
# ===============================

@app.post("/api/v1/conversation/start", response_model=dict)
async def start_conversation(video_id: int, db: Session = Depends(get_db)):
    """Start a new conversation session for a video"""
    if not PHASE3_TO_5_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 3-5 features not available")
    
    try:
        # Initialize conversation manager
        if conversation_manager is None:
            raise HTTPException(status_code=500, detail="Conversation manager not available")
        
        # Start a new session
        session_id = conversation_manager.start_session(video_id)
        
        return {"session_id": session_id, "status": "started"}
        
    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/conversation/{session_id}/ask", response_model=dict)
async def ask_question(session_id: str, request: dict):
    """Ask a question in the conversation"""
    if not PHASE3_TO_5_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 3-5 features not available")
    
    try:
        if conversation_manager is None:
            raise HTTPException(status_code=500, detail="Conversation manager not available")
        
        # Process the question
        response = conversation_manager.process_question(session_id, request["question"])
        
        return {"response": response}
        
    except Exception as e:
        logger.error(f"Error in conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/visual-search", response_model=dict)
async def visual_search(request: dict):
    """Perform visual search for a video"""
    if not PHASE3_TO_5_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 3-5 features not available")
    
    try:
        if visual_search_engine is None:
            raise HTTPException(status_code=500, detail="Visual search engine not available")
        
        # Perform the visual search
        results = visual_search_engine.search(request["image_path"], request.get("top_k", 5))
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Error in visual search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/content-navigation", response_model=dict)
async def content_navigation(request: dict):
    """Navigate and segment video content"""
    if not PHASE3_TO_5_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 3-5 features not available")
    
    try:
        if content_segmentation_engine is None:
            raise HTTPException(status_code=500, detail="Content segmentation engine not available")
        
        # Segment the content
        segments = content_segmentation_engine.segment(request["video_id"], request.get("threshold", 0.5))
        
        return {"segments": segments}
        
    except Exception as e:
        logger.error(f"Error in content navigation: {e}")
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
# PHASE 3: CONVERSATIONAL INTERFACE API ENDPOINTS
# ===============================

@app.post("/api/v1/chat/session", response_model=ChatSessionResponse)
async def create_chat_session(request: ChatSessionCreate, db: Session = Depends(get_db)):
    """Create a new chat session for a video"""
    if not PHASE3_TO_5_AVAILABLE or not conversation_manager:
        raise HTTPException(status_code=501, detail="Phase 3 conversational features not available")
    
    try:
        video = db.query(Video).filter(Video.id == request.video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        session = conversation_manager.create_session(db, request.video_id, request.title)
        
        return ChatSessionResponse(
            session_id=session.session_id,
            video_id=session.video_id,
            title=session.title,
            created_at=session.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat/message", response_model=ChatMessageResponse)
async def send_chat_message(request: ChatMessageRequest, db: Session = Depends(get_db)):
    """Send a message in a chat session and get AI response"""
    if not PHASE3_TO_5_AVAILABLE or not conversation_manager:
        raise HTTPException(status_code=501, detail="Phase 3 conversational features not available")
    
    try:
        session = conversation_manager.get_session(db, request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        response = await conversation_manager.generate_enhanced_response(
            db, request.session_id, request.message, session.video_id
        )
        
        return ChatMessageResponse(**response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/chat/session/{session_id}/history")
async def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    """Get complete chat session history"""
    if not PHASE3_TO_5_AVAILABLE or not conversation_manager:
        raise HTTPException(status_code=501, detail="Phase 3 conversational features not available")
    
    try:
        history = conversation_manager.get_session_history(db, session_id)
        if not history:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/chat/session/{session_id}")
async def close_chat_session(session_id: str, db: Session = Depends(get_db)):
    """Close a chat session"""
    if not PHASE3_TO_5_AVAILABLE or not conversation_manager:
        raise HTTPException(status_code=501, detail="Phase 3 conversational features not available")
    
    try:
        conversation_manager.close_session(db, session_id)
        return {"message": "Chat session closed successfully"}
        
    except Exception as e:
        logger.error(f"Error closing chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===============================
# PHASE 4: VISUAL SEARCH ENGINE API ENDPOINTS
# ===============================

@app.post("/api/v1/visual/process/{video_id}")
async def process_video_visual_content(
    video_id: int, 
    background_tasks: BackgroundTasks,
    confidence_threshold: float = 0.5,
    db: Session = Depends(get_db)
):
    """Process video frames for object detection and scene classification"""
    if not PHASE3_TO_5_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 4 visual search features not available")
    
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Start background processing
        background_tasks.add_task(
            process_visual_content_background, video_id, confidence_threshold
        )
        
        return {
            "video_id": video_id,
            "status": "processing",
            "message": "Visual content processing started in background"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting visual content processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/visual/search", response_model=VisualSearchResponse)
async def visual_search(request: VisualSearchRequest, db: Session = Depends(get_db)):
    """Search for visual content using natural language queries"""
    if not PHASE3_TO_5_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 4 visual search features not available")
    
    try:
        video = db.query(Video).filter(Video.id == request.video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        search_results = visual_search_engine.search_visual_content(
            db, request.video_id, request.query, request.confidence_threshold
        )
        
        # Format response to match VisualSearchResponse model
        formatted_response = {
            "video_id": str(request.video_id),
            "results": search_results.get("results", []),
            "total_matches": search_results.get("total_results", 0)
        }
        
        return VisualSearchResponse(**formatted_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in visual search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/visual/{video_id}/timeline")
async def get_visual_timeline(video_id: int, db: Session = Depends(get_db)):
    """Get visual timeline showing detected objects and scenes"""
    if not PHASE3_TO_5_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 4 visual search features not available")
    
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        timeline = visual_search_engine.get_visual_timeline(db, video_id)
        return timeline
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting visual timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/visual/{video_id}/statistics")
async def get_object_statistics(video_id: int, db: Session = Depends(get_db)):
    """Get statistics about detected objects in the video"""
    if not PHASE3_TO_5_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 4 visual search features not available")
    
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        stats = visual_search_engine.get_object_statistics(db, video_id)
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting object statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===============================
# PHASE 5: NAVIGATION & USER INTERFACE API ENDPOINTS
# ===============================

@app.post("/api/v1/content/analyze/{video_id}", response_model=TopicSegmentResponse)
async def analyze_video_content(video_id: int, db: Session = Depends(get_db)):
    """Analyze video content to create topic segments"""
    if not PHASE3_TO_5_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 5 content analysis features not available")
    
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        result = content_segmentation_engine.create_topic_segments(db, video_id)
        
        return TopicSegmentResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing video content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/content/outline/{video_id}", response_model=ContentOutlineResponse)
async def generate_content_outline(video_id: int, db: Session = Depends(get_db)):
    """Generate hierarchical content outline for the video"""
    if not PHASE3_TO_5_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 5 content analysis features not available")
    
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        result = content_segmentation_engine.generate_content_outline(db, video_id)
        
        return ContentOutlineResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating content outline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/navigation/events/{video_id}")
async def create_navigation_events(video_id: int, db: Session = Depends(get_db)):
    """Create navigation events for enhanced video navigation"""
    if not PHASE3_TO_5_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 5 navigation features not available")
    
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        result = content_segmentation_engine.create_navigation_events(db, video_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating navigation events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/navigation/{video_id}")
async def get_navigation_data(video_id: int, db: Session = Depends(get_db)):
    """Get comprehensive navigation data for a video"""
    if not PHASE3_TO_5_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phase 5 navigation features not available")
    
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        navigation_data = content_segmentation_engine.get_video_navigation_data(db, video_id)
        
        return navigation_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting navigation data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background processing functions for Phase 4
async def process_visual_content_background(video_id: int, confidence_threshold: float):
    """Background task to process visual content of a video"""
    db = next(get_db())
    try:
        logger.info(f"Starting visual content processing for video {video_id}")
        
        result = visual_search_engine.process_video_frames(db, video_id, confidence_threshold)
        
        logger.info(f"Completed visual content processing for video {video_id}: {result}")
        
    except Exception as e:
        logger.error(f"Error in visual content processing for video {video_id}: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
