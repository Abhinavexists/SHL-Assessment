#!/bin/bash
set -e

echo "Starting SHL Assessment API server deployment"

# Create necessary directories
mkdir -p app/data/chroma_db

# Check for ChromaDB data
if [ ! -d "app/data/chroma_db" ] || [ -z "$(ls -A app/data/chroma_db)" ]; then
    echo "ChromaDB not found or empty. Rebuilding..."
    python app/scripts/rebuild_chroma.py
else
    echo "Using existing ChromaDB."
fi

# Set up environment variables
export PYTHONPATH=$PWD

# Start the FastAPI server
echo "Starting API server on port 8000..."
uvicorn app.api.main:app --host 0.0.0.0 --port 8000

echo "API server started successfully!"
echo "FastAPI running on http://localhost:8000"
echo "To test: curl http://localhost:8000/health" 