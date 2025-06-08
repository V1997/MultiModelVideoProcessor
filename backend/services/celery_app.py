# Celery Configuration for MultiModelVideo
# Uses Redis as message broker and result backend

import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Create Celery app
celery_app = Celery("multimodel_video")

# Redis configuration
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
broker_url = redis_url.replace("/0", "/1")  # Use DB 1 for broker
result_backend = redis_url.replace("/0", "/2")  # Use DB 2 for results

# Configure Celery
celery_app.conf.update(
    broker_url=broker_url,
    result_backend=result_backend,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'video.process': {'queue': 'video'},
        'transcript.generate': {'queue': 'transcript'},
        'embeddings.generate': {'queue': 'embeddings'},
        'visual.analyze': {'queue': 'visual'},
    },
    
    # Worker configuration
    worker_concurrency=4,
    worker_max_tasks_per_child=100,
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    
    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Task settings
    task_annotations={
        '*': {'rate_limit': '10/s'}
    }
)

# Auto-discover tasks from backend modules
celery_app.autodiscover_tasks([
    'backend.video_processor',
    'backend.transcript_handler', 
    'backend.embedding_engine',
    'backend.visual_search',
    'backend.content_analysis'
])

# Task definitions
@celery_app.task(name='video.process', bind=True)
def process_video_task(self, video_id: int, video_path: str):
    """Background task to process uploaded video"""
    from backend.api.main import process_video_background
    import asyncio
    
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'Starting video processing'})
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(process_video_background(video_id, video_path))
        loop.close()
        
        return {'status': 'completed', 'video_id': video_id}
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

@celery_app.task(name='youtube.process', bind=True)
def process_youtube_task(self, video_id: int, video_url: str, use_whisper: bool = False, model_size: str = "base"):
    """Background task to process YouTube video"""
    from backend.api.main import process_youtube_background
    import asyncio
    
    try:
        self.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'Starting YouTube processing'})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(process_youtube_background(video_id, video_url, use_whisper, model_size))
        loop.close()
        
        return {'status': 'completed', 'video_id': video_id}
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

@celery_app.task(name='embeddings.generate', bind=True)
def generate_embeddings_task(self, video_id: int):
    """Background task to generate embeddings"""
    from backend.api.main import generate_embeddings_background
    import asyncio
    
    try:
        self.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'Generating embeddings'})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(generate_embeddings_background(video_id))
        loop.close()
        
        return {'status': 'completed', 'video_id': video_id}
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

@celery_app.task(name='visual.analyze', bind=True)
def analyze_visual_content_task(self, video_id: int, confidence_threshold: float = 0.5):
    """Background task to analyze visual content"""
    from backend.api.main import process_visual_content_background
    import asyncio
    
    try:
        self.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'Analyzing visual content'})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(process_visual_content_background(video_id, confidence_threshold))
        loop.close()
        
        return {'status': 'completed', 'video_id': video_id}
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

# Task monitoring
@celery_app.task(name='health.check')
def health_check_task():
    """Health check task"""
    import redis
    try:
        # Test Redis connection
        r = redis.from_url(redis_url)
        r.ping()
        return {'status': 'healthy', 'redis': 'connected'}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}

if __name__ == '__main__':
    celery_app.start()
