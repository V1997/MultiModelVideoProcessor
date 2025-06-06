import whisper
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from typing import List, Dict, Optional, Tuple
import logging
import re
import os
from pathlib import Path

# Add OpenAI import
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class TranscriptHandler:
    def __init__(self):
        self.whisper_model = None
        self.supported_youtube_domains = ['youtube.com', 'youtu.be', 'm.youtube.com']
        
        # Initialize OpenAI client if available
        self.openai_client = None
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                logger.info("OpenAI Whisper API initialized")
            else:
                logger.warning("OPENAI_API_KEY not found, will use local Whisper only")
        else:
            logger.warning("OpenAI package not installed, will use local Whisper only")
    
    def _load_whisper_model(self, model_size: str = "base"):
        """Load Whisper model lazily"""
        if self.whisper_model is None:
            logger.info(f"Loading Whisper model: {model_size}")
            self.whisper_model = whisper.load_model(model_size)
        return self.whisper_model
    
    def is_youtube_url(self, url: str) -> bool:
        """Check if URL is a YouTube URL"""
        return any(domain in url.lower() for domain in self.supported_youtube_domains)
    
    def extract_youtube_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/watch\?.*v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_youtube_transcript(self, video_url: str) -> Tuple[List[Dict], Dict]:
        """Get transcript from YouTube video"""
        try:
            video_id = self.extract_youtube_video_id(video_url)
            if not video_id:
                raise ValueError("Could not extract video ID from YouTube URL")
            
            logger.info(f"Extracting transcript for YouTube video ID: {video_id}")
            
            # Get transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Format transcript chunks
            transcript_chunks = []
            for entry in transcript_list:
                transcript_chunks.append({
                    "text": entry['text'],
                    "start_time": entry['start'],
                    "end_time": entry['start'] + entry['duration'],
                    "confidence": 1.0  # YouTube transcripts don't provide confidence scores
                })
            
            # Get video metadata using yt-dlp
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extractflat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                metadata = {
                    "duration": info.get('duration', 0),
                    "title": info.get('title', ''),
                    "description": info.get('description', ''),
                    "uploader": info.get('uploader', ''),
                    "view_count": info.get('view_count', 0),
                    "upload_date": info.get('upload_date', ''),
                    "width": info.get('width', 0),
                    "height": info.get('height', 0),
                    "fps": info.get('fps', 0),
                }
            
            logger.info(f"Successfully extracted transcript with {len(transcript_chunks)} chunks")
            return transcript_chunks, metadata
            
        except Exception as e:
            logger.error(f"Error extracting YouTube transcript: {str(e)}")
            raise
    
    def transcribe_audio_file(self, audio_path: str, model_size: str = "base", prefer_openai: bool = True) -> List[Dict]:
        """Transcribe audio file using OpenAI API or local Whisper"""
        try:
            # Try OpenAI API first if available and preferred
            if prefer_openai and self.openai_client:
                try:
                    return self._transcribe_with_openai_api(audio_path)
                except Exception as e:
                    logger.warning(f"OpenAI API failed, falling back to local Whisper: {str(e)}")
            
            # Fall back to local Whisper
            model = self._load_whisper_model(model_size)
            
            logger.info(f"Transcribing audio file with local Whisper: {audio_path}")
            result = model.transcribe(audio_path)
            
            # Format transcript chunks
            transcript_chunks = []
            for segment in result['segments']:
                transcript_chunks.append({
                    "text": segment['text'].strip(),
                    "start_time": segment['start'],
                    "end_time": segment['end'],
                    "confidence": segment.get('confidence', 0.0)
                })
            
            logger.info(f"Successfully transcribed audio with local Whisper: {len(transcript_chunks)} segments")
            return transcript_chunks
            
        except Exception as e:
            logger.error(f"Error transcribing audio file: {str(e)}")
            raise
    
    def transcribe_video_file(self, video_path: str, model_size: str = "base", prefer_openai: bool = True) -> List[Dict]:
        """Transcribe video file using OpenAI API or local Whisper"""
        try:
            # Whisper can handle video files directly
            return self.transcribe_audio_file(video_path, model_size, prefer_openai)
            
        except Exception as e:
            logger.error(f"Error transcribing video file: {str(e)}")
            raise
    
    def download_youtube_audio(self, video_url: str, output_dir: str = "./temp") -> str:
        """Download audio from YouTube video for transcription"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            video_id = self.extract_youtube_video_id(video_url)
            audio_filename = f"youtube_audio_{video_id}.%(ext)s"
            audio_filepath = output_path / audio_filename
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(audio_filepath),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            # Find the downloaded file (extension might change)
            downloaded_files = list(output_path.glob(f"youtube_audio_{video_id}.*"))
            if not downloaded_files:
                raise FileNotFoundError("Could not find downloaded audio file")
            
            return str(downloaded_files[0])
            
        except Exception as e:
            logger.error(f"Error downloading YouTube audio: {str(e)}")
            raise
    
    def process_youtube_video(self, video_url: str, use_whisper: bool = False, model_size: str = "base") -> Tuple[List[Dict], Dict]:
        """Process YouTube video - get transcript and metadata"""
        try:
            if not use_whisper:
                # Try to get existing transcript first
                try:
                    return self.get_youtube_transcript(video_url)
                except Exception as e:
                    logger.warning(f"Could not get YouTube transcript, falling back to Whisper: {str(e)}")
                    use_whisper = True
            
            if use_whisper:
                # Download audio and transcribe with Whisper
                audio_path = self.download_youtube_audio(video_url)
                
                try:
                    transcript_chunks = self.transcribe_audio_file(audio_path, model_size)
                    
                    # Get metadata
                    ydl_opts = {'quiet': True, 'no_warnings': True}
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(video_url, download=False)
                        metadata = {
                            "duration": info.get('duration', 0),
                            "title": info.get('title', ''),
                            "description": info.get('description', ''),
                            "uploader": info.get('uploader', ''),
                            "view_count": info.get('view_count', 0),
                            "upload_date": info.get('upload_date', ''),
                            "width": info.get('width', 0),
                            "height": info.get('height', 0),
                            "fps": info.get('fps', 0),
                        }
                    
                    return transcript_chunks, metadata
                    
                finally:
                    # Clean up downloaded audio file
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
            
        except Exception as e:
            logger.error(f"Error processing YouTube video: {str(e)}")
            raise
    
    def chunk_transcript_intelligently(self, transcript_chunks: List[Dict], max_chunk_size: int = 500) -> List[Dict]:
        """Combine transcript segments into intelligent chunks"""
        try:
            if not transcript_chunks:
                return []
            
            intelligent_chunks = []
            current_chunk = {
                "text": "",
                "start_time": transcript_chunks[0]["start_time"],
                "end_time": transcript_chunks[0]["end_time"],
                "confidence": 0.0
            }
            
            confidence_sum = 0.0
            segment_count = 0
            
            for segment in transcript_chunks:
                # Check if adding this segment would exceed max size
                potential_text = current_chunk["text"] + " " + segment["text"] if current_chunk["text"] else segment["text"]
                
                if len(potential_text) > max_chunk_size and current_chunk["text"]:
                    # Finalize current chunk
                    current_chunk["confidence"] = confidence_sum / segment_count if segment_count > 0 else 0.0
                    intelligent_chunks.append(current_chunk.copy())
                    
                    # Start new chunk
                    current_chunk = {
                        "text": segment["text"],
                        "start_time": segment["start_time"],
                        "end_time": segment["end_time"],
                        "confidence": segment["confidence"]
                    }
                    confidence_sum = segment["confidence"]
                    segment_count = 1
                else:
                    # Add to current chunk
                    current_chunk["text"] = potential_text
                    current_chunk["end_time"] = segment["end_time"]
                    confidence_sum += segment["confidence"]
                    segment_count += 1
            
            # Add final chunk
            if current_chunk["text"]:
                current_chunk["confidence"] = confidence_sum / segment_count if segment_count > 0 else 0.0
                intelligent_chunks.append(current_chunk)
            
            logger.info(f"Combined {len(transcript_chunks)} segments into {len(intelligent_chunks)} intelligent chunks")
            return intelligent_chunks
            
        except Exception as e:
            logger.error(f"Error chunking transcript: {str(e)}")
            raise
    
    def _transcribe_with_openai_api(self, audio_path: str) -> List[Dict]:
        """Transcribe audio using OpenAI Whisper API"""
        if not self.openai_client:
            raise ValueError("OpenAI API not available")
        
        try:
            logger.info(f"Transcribing with OpenAI Whisper API: {audio_path}")
            
            with open(audio_path, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            # Convert OpenAI response to our format
            transcript_chunks = []
            for segment in transcript.segments:
                transcript_chunks.append({
                    "text": segment["text"].strip(),
                    "start_time": segment["start"],
                    "end_time": segment["end"],
                    "confidence": 1.0  # OpenAI doesn't provide confidence scores
                })
            
            logger.info(f"OpenAI API transcription completed: {len(transcript_chunks)} segments")
            return transcript_chunks
            
        except Exception as e:
            logger.error(f"OpenAI API transcription failed: {str(e)}")
            raise
