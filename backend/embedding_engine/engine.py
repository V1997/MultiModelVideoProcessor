"""
Vector Embedding Engine for MultiModel Video Processor
Handles generation and storage of embeddings for frames and text
"""

import os
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import pickle

# Core ML libraries
try:
    from sentence_transformers import SentenceTransformer
    from transformers import CLIPProcessor, CLIPModel
    import torch
    from PIL import Image
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("ML libraries not available. Install requirements for Phase 2.")

# Vector database
try:
    import lancedb
    LANCEDB_AVAILABLE = True
except ImportError:
    LANCEDB_AVAILABLE = False
    logging.warning("LanceDB not available. Install lancedb for vector storage.")

from ..database.models import Video, TranscriptChunk, VideoFrame, SessionLocal

class EmbeddingEngine:
    """
    Main engine for generating and managing embeddings
    """
    
    def __init__(self, 
                 text_model_name: str = "all-MiniLM-L6-v2",
                 vision_model_name: str = "openai/clip-vit-base-patch32",
                 vector_db_path: str = "./vector_db"):
        
        self.text_model_name = text_model_name
        self.vision_model_name = vision_model_name
        self.vector_db_path = Path(vector_db_path)
        self.vector_db_path.mkdir(exist_ok=True)
        
        # Initialize models
        self.text_model = None
        self.vision_model = None
        self.vision_processor = None
        
        # Vector database connection
        self.db = None
        
        # Thread pool for CPU-intensive tasks
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize all models and databases"""
        try:
            await self._load_models()
            await self._setup_vector_db()
            self.logger.info("Embedding engine initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize embedding engine: {e}")
            raise
    
    async def _load_models(self):
        """Load text and vision models"""
        if not ML_AVAILABLE:
            raise ImportError("ML libraries required for embedding engine")
        
        self.logger.info("Loading text embedding model...")
        loop = asyncio.get_event_loop()
        
        # Load text model in thread pool
        self.text_model = await loop.run_in_executor(
            self.executor, 
            SentenceTransformer, 
            self.text_model_name
        )
        
        self.logger.info("Loading vision embedding model...")
        # Load vision model in thread pool
        def load_vision_models():
            model = CLIPModel.from_pretrained(self.vision_model_name)
            processor = CLIPProcessor.from_pretrained(self.vision_model_name)
            return model, processor
        
        self.vision_model, self.vision_processor = await loop.run_in_executor(
            self.executor, load_vision_models
        )
        
        self.logger.info("All models loaded successfully")
    
    async def _setup_vector_db(self):
        """Setup LanceDB vector database"""
        if not LANCEDB_AVAILABLE:
            self.logger.warning("LanceDB not available, using file-based storage")
            return
        
        try:
            self.db = lancedb.connect(str(self.vector_db_path))
            self.logger.info("LanceDB connected successfully")
        except Exception as e:
            self.logger.error(f"Failed to connect to LanceDB: {e}")
            self.db = None
    
    async def generate_text_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for text chunks"""
        if not self.text_model:
            raise ValueError("Text model not initialized")
        
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            self.executor,
            self.text_model.encode,
            texts
        )
        
        return embeddings
    
    async def generate_frame_embeddings(self, image_paths: List[str]) -> np.ndarray:
        """Generate embeddings for video frames"""
        if not self.vision_model or not self.vision_processor:
            raise ValueError("Vision model not initialized")
        
        def process_images(paths):
            images = []
            for path in paths:
                try:
                    if os.path.exists(path):
                        image = Image.open(path).convert('RGB')
                        images.append(image)
                    else:
                        self.logger.warning(f"Image not found: {path}")
                except Exception as e:
                    self.logger.error(f"Error loading image {path}: {e}")
            
            if not images:
                return np.array([])
            
            # Process images and get embeddings
            inputs = self.vision_processor(images=images, return_tensors="pt", padding=True)
            
            with torch.no_grad():
                image_features = self.vision_model.get_image_features(**inputs)
                # Normalize embeddings
                image_features = image_features / image_features.norm(dim=1, keepdim=True)
            
            return image_features.cpu().numpy()
        
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(self.executor, process_images, image_paths)
        
        return embeddings
    
    async def store_text_embeddings(self, video_id: int, transcript_chunks: List[Dict], embeddings: np.ndarray):
        """Store text embeddings in vector database"""
        if self.db is None:
            # Fallback to file storage
            return await self._store_embeddings_file(f"text_{video_id}", transcript_chunks, embeddings)
        
        try:
            # Prepare data for LanceDB
            data = []
            for i, (chunk, embedding) in enumerate(zip(transcript_chunks, embeddings)):
                data.append({
                    "id": f"text_{video_id}_{i}",
                    "video_id": video_id,
                    "chunk_id": chunk.get("id"),
                    "text": chunk.get("text", ""),
                    "start_time": chunk.get("start_time", 0.0),
                    "end_time": chunk.get("end_time", 0.0),
                    "type": "text",
                    "embedding": embedding.tolist()
                })
            
            # Create or get table
            table_name = "text_embeddings"
            if table_name not in self.db.table_names():
                table = self.db.create_table(table_name, data)
            else:
                table = self.db.open_table(table_name)
                table.add(data)
            
            self.logger.info(f"Stored {len(data)} text embeddings for video {video_id}")
            
        except Exception as e:
            self.logger.error(f"Error storing text embeddings: {e}")
            # Fallback to file storage
            await self._store_embeddings_file(f"text_{video_id}", transcript_chunks, embeddings)
    
    async def store_frame_embeddings(self, video_id: int, frames: List[Dict], embeddings: np.ndarray):
        """Store frame embeddings in vector database"""
        if self.db is None:
            return await self._store_embeddings_file(f"frames_{video_id}", frames, embeddings)
        
        try:
            data = []
            for i, (frame, embedding) in enumerate(zip(frames, embeddings)):
                data.append({
                    "id": f"frame_{video_id}_{i}",
                    "video_id": video_id,
                    "frame_id": frame.get("id"),
                    "frame_path": frame.get("frame_path", ""),
                    "timestamp": frame.get("timestamp", 0.0),
                    "frame_number": frame.get("frame_number", 0),
                    "type": "frame",
                    "embedding": embedding.tolist()
                })
            
            table_name = "frame_embeddings"
            if table_name not in self.db.table_names():
                table = self.db.create_table(table_name, data)
            else:
                table = self.db.open_table(table_name)
                table.add(data)
            
            self.logger.info(f"Stored {len(data)} frame embeddings for video {video_id}")
            
        except Exception as e:
            self.logger.error(f"Error storing frame embeddings: {e}")
            await self._store_embeddings_file(f"frames_{video_id}", frames, embeddings)
    
    async def _store_embeddings_file(self, prefix: str, items: List[Dict], embeddings: np.ndarray):
        """Fallback: Store embeddings as pickle files"""
        file_path = self.vector_db_path / f"{prefix}_embeddings.pkl"
        
        data = {
            "items": items,
            "embeddings": embeddings,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        def save_pickle():
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, save_pickle)
        
        self.logger.info(f"Stored embeddings to file: {file_path}")
    
    async def search_similar_content(self, 
                                   query_embedding: np.ndarray, 
                                   content_type: str = "both",
                                   limit: int = 10,
                                   video_id: Optional[int] = None) -> List[Dict]:
        """
        Search for similar content using embeddings
        
        Args:
            query_embedding: The query embedding vector
            content_type: "text", "frame", or "both"
            limit: Maximum number of results
            video_id: Limit search to specific video (optional)
        """
        if self.db is None:
            return await self._search_similar_file(query_embedding, content_type, limit, video_id)
        
        results = []
        
        try:
            if content_type in ["text", "both"]:
                text_results = await self._search_table("text_embeddings", query_embedding, limit, video_id)
                results.extend(text_results)
            
            if content_type in ["frame", "both"]:
                frame_results = await self._search_table("frame_embeddings", query_embedding, limit, video_id)
                results.extend(frame_results)
            
            # Sort by similarity score
            results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"Error in similarity search: {e}")
            return []
    
    async def _search_table(self, table_name: str, query_embedding: np.ndarray, limit: int, video_id: Optional[int]) -> List[Dict]:
        """Search specific table for similar embeddings"""
        if table_name not in self.db.table_names():
            return []
        
        table = self.db.open_table(table_name)
        
        # Perform vector search
        results = table.search(query_embedding.tolist()).limit(limit).to_list()
        
        # Filter by video_id if specified
        if video_id:
            results = [r for r in results if r.get("video_id") == video_id]
        
        return results
    
    async def _search_similar_file(self, query_embedding: np.ndarray, content_type: str, limit: int, video_id: Optional[int]) -> List[Dict]:
        """Fallback: Search embeddings from pickle files"""
        results = []
        
        # This is a simplified implementation for file-based storage
        # In production, you'd want a more sophisticated indexing system
        
        embedding_files = list(self.vector_db_path.glob("*_embeddings.pkl"))
        
        for file_path in embedding_files:
            try:
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                
                embeddings = data["embeddings"]
                items = data["items"]
                
                # Calculate similarities
                similarities = np.dot(embeddings, query_embedding.flatten())
                
                # Get top results
                top_indices = np.argsort(similarities)[::-1][:limit]
                
                for idx in top_indices:
                    if similarities[idx] > 0.5:  # Similarity threshold
                        result = items[idx].copy()
                        result["similarity"] = float(similarities[idx])
                        results.append(result)
                        
            except Exception as e:
                self.logger.error(f"Error reading embedding file {file_path}: {e}")
        
        # Sort and limit results
        results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        return results[:limit]
    
    async def process_video_embeddings(self, video_id: int):
        """Process all embeddings for a video"""
        try:
            db = SessionLocal()
            
            # Get video data
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                raise ValueError(f"Video {video_id} not found")
            
            # Process text embeddings
            transcript_chunks = db.query(TranscriptChunk).filter(TranscriptChunk.video_id == video_id).all()
            if transcript_chunks:
                texts = [chunk.text for chunk in transcript_chunks]
                text_embeddings = await self.generate_text_embeddings(texts)
                
                chunk_data = [
                    {
                        "id": chunk.id,
                        "text": chunk.text,
                        "start_time": chunk.start_time,
                        "end_time": chunk.end_time
                    }
                    for chunk in transcript_chunks
                ]
                
                await self.store_text_embeddings(video_id, chunk_data, text_embeddings)
            
            # Process frame embeddings
            frames = db.query(VideoFrame).filter(VideoFrame.video_id == video_id).all()
            if frames:
                frame_paths = [frame.frame_path for frame in frames if os.path.exists(frame.frame_path)]
                if frame_paths:
                    frame_embeddings = await self.generate_frame_embeddings(frame_paths)
                    
                    frame_data = [
                        {
                            "id": frame.id,
                            "frame_path": frame.frame_path,
                            "timestamp": frame.timestamp,
                            "frame_number": frame.frame_number
                        }
                        for frame in frames if os.path.exists(frame.frame_path)
                    ]
                    
                    await self.store_frame_embeddings(video_id, frame_data, frame_embeddings)
            
            self.logger.info(f"Completed embedding processing for video {video_id}")
            
        except Exception as e:
            self.logger.error(f"Error processing embeddings for video {video_id}: {e}")
            raise
        finally:
            db.close()

# Global embedding engine instance
embedding_engine = None

async def get_embedding_engine():
    """Get or create the global embedding engine instance"""
    global embedding_engine
    
    if embedding_engine is None:
        embedding_engine = EmbeddingEngine()
        await embedding_engine.initialize()
    
    return embedding_engine
