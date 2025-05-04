#!/bin/bash
set -e

# Create necessary directories
mkdir -p /app/app/data/chroma_db

# Set environment variables
export PYTHONPATH=/app

# Run scraper if catalog doesn't exist
if [ ! -f "/app/app/data/shl_catalog.json" ]; then
    echo "Catalog not found. Running scraper..."
    python -m app.scripts.scrape_catalog
else
    echo "Using existing catalog file."
fi

# Rebuild the ChromaDB collection
echo "Rebuilding vector database..."
python /app/rebuild_chroma.py

# Start the FastAPI backend in the background
echo "Starting FastAPI server..."
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Give the API time to start
sleep 5

# Start the Streamlit frontend
echo "Starting Streamlit UI..."
streamlit run app/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &
STREAMLIT_PID=$!

# Function to handle shutdown
function handle_shutdown {
    echo "Shutting down services..."
    kill -TERM $STREAMLIT_PID 2>/dev/null || true
    kill -TERM $API_PID 2>/dev/null || true
    exit 0
}

# Set up signal handler
trap handle_shutdown SIGTERM SIGINT

# Keep the container running
echo "Services started successfully!"
echo "FastAPI running on http://localhost:8000"
echo "Streamlit running on http://localhost:8501"
wait $API_PID $STREAMLIT_PID 