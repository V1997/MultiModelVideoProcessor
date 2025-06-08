#!/usr/bin/env python3
"""
Script to start Celery worker for background task processing
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.services.celery_app import celery_app

def main():
    """Start the Celery worker"""
    print("Starting Celery worker for MultiModelVideo...")
    print("Available task types:")
    print("  - video.process: Process uploaded videos")
    print("  - youtube.process: Process YouTube videos")
    print("  - embeddings.generate: Generate video embeddings")
    print("  - visual.analyze: Analyze visual content")
    print()
    
    # Start the worker
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',  # Adjust based on system resources
        '--queues=default,video,youtube,embeddings,visual',
    ])

if __name__ == '__main__':
    main()
