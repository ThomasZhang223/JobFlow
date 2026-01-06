#!/bin/bash
# Start script for FastAPI on Render

# Install dependencies
pip install -r requirements.txt

# Start the API server using FastAPI CLI
fastapi run app/main.py --host 0.0.0.0 --port ${PORT:-8000}
