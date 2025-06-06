# MultiModel Video Processor - Phase 1

## Installation

### Prerequisites
- Python 3.8 or higher
- FFmpeg (for video processing)
- PostgreSQL (or use SQLite for development)

### Setup Instructions

1. **Clone the repository:**
```bash
git clone https://github.com/V1997/MultiModelVideoProcessor.git
cd MultiModelVideoProcessor
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Install FFmpeg:**
   - **Windows:** Download from https://ffmpeg.org/download.html
   - **macOS:** `brew install ffmpeg`
   - **Ubuntu:** `sudo apt update && sudo apt install ffmpeg`

6. **Set up the database:**
   - For PostgreSQL: Create a database and update DATABASE_URL in .env
   - For SQLite: The database will be created automatically

## Usage

### Starting the API Server

```bash
# From the project root directory
cd backend/api
python -m uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI)

### API Endpoints

#### 1. Upload Video File
```http
POST /upload-video
Content-Type: multipart/form-data

Parameters:
- file: Video file (mp4, avi, mov, mkv, webm)
```

#### 2. Process YouTube Video
```http
POST /process-youtube
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "use_whisper": false,
  "whisper_model": "base"
}
```

#### 3. Get Video Status
```http
GET /video/{video_id}/status
```

#### 4. Get Video Transcript
```http
GET /video/{video_id}/transcript
```

#### 5. Get Video Frames
```http
GET /video/{video_id}/frames
```

#### 6. List All Videos
```http
GET /videos
```

### Example Usage

1. **Upload a video file:**
```bash
curl -X POST "http://localhost:8000/upload-video" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_video.mp4"
```

2. **Process a YouTube video:**
```bash
curl -X POST "http://localhost:8000/process-youtube" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

3. **Check processing status:**
```bash
curl -X GET "http://localhost:8000/video/1/status"
```

## Features (Phase 1)

### ✅ Implemented
- **Video Upload & Processing**
  - Support for multiple video formats (MP4, AVI, MOV, MKV, WebM)
  - Video metadata extraction (duration, resolution, fps)
  - File validation and size limits

- **Transcript Generation**
  - YouTube Transcript API integration
  - Whisper integration for local video files
  - Intelligent transcript chunking
  - Timestamp synchronization

- **Frame Extraction**
  - Configurable frame extraction rate
  - Timestamp-aligned frame storage
  - Efficient frame processing with OpenCV

- **Database Storage**
  - Video metadata and status tracking
  - Transcript chunks with timestamps
  - Frame metadata storage

- **Background Processing**
  - Asynchronous video processing
  - Real-time status updates
  - Robust error handling

- **RESTful API**
  - FastAPI with automatic documentation
  - CORS support for frontend integration
  - Comprehensive error handling

### 🔄 Processing Flow

1. **Video Upload/URL Submission** → Validation & Metadata Extraction
2. **Background Processing** → Transcript Generation + Frame Extraction
3. **Database Storage** → Searchable chunks with timestamps
4. **API Access** → Retrieve processed data via REST endpoints

## Configuration

### Environment Variables (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/multimodal_video
REDIS_URL=redis://localhost:6379/0

# OpenAI (optional)
OPENAI_API_KEY=your_api_key_here

# File Storage
UPLOAD_DIR=./uploads
PROCESSED_DIR=./processed
FRAMES_DIR=./frames

# Processing Settings
FRAME_EXTRACTION_FPS=1
MAX_VIDEO_SIZE_MB=500
SUPPORTED_FORMATS=mp4,avi,mov,mkv,webm

# Development
DEBUG=True
LOG_LEVEL=INFO
```

## Project Structure

```
MultiModelVideoProcessor/
├── backend/
│   ├── api/
│   │   └── main.py              # FastAPI application
│   ├── database/
│   │   └── models.py            # SQLAlchemy models
│   ├── video_processor/
│   │   └── processor.py         # Video processing logic
│   ├── transcript_handler/
│   │   └── handler.py           # Transcript generation
│   └── embedding_engine/        # (Phase 2)
├── frontend/                    # (Future phases)
├── models/                      # (Future phases)
├── database/                    # (Future phases)
├── requirements.txt
├── .env.example
└── README.md
```

## Testing

### Manual Testing

1. **Test video upload:**
   - Upload various video formats
   - Check processing status
   - Verify transcript generation

2. **Test YouTube processing:**
   - Process different YouTube videos
   - Test both transcript API and Whisper fallback
   - Verify metadata extraction

3. **Test API endpoints:**
   - Use Swagger UI at `/docs`
   - Test error scenarios
   - Verify response formats

### Automated Testing (Coming in future phases)

```bash
pytest tests/
```

## Troubleshooting

### Common Issues

1. **FFmpeg not found:**
   - Ensure FFmpeg is installed and in PATH
   - Test with `ffmpeg -version`

2. **Database connection errors:**
   - Verify PostgreSQL is running
   - Check DATABASE_URL in .env
   - For SQLite, ensure write permissions

3. **Large video processing failures:**
   - Check disk space for uploads and frames
   - Adjust MAX_VIDEO_SIZE_MB
   - Monitor memory usage for Whisper

4. **YouTube processing issues:**
   - Some videos may not have transcripts
   - Age-restricted videos might fail
   - Use Whisper fallback for problematic videos

### Logs

Check logs for detailed error information:
```bash
tail -f /var/log/multimodel-video.log
```

## Next Steps (Phase 2)

- Multimodal RAG implementation with CLIP embeddings
- Vector database integration (LanceDB/Milvus)
- Advanced search capabilities
- Basic chat interface

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
