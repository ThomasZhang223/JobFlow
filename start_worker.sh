#!/bin/bash
# Start script for Celery Worker on Render

# Install dependencies
pip install -r requirements.txt

# Start Celery worker with single concurrency (free tier optimization)
celery -A worker.celery_app worker --loglevel=info --concurrency=1
