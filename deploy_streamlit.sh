#!/bin/bash
set -e

echo "Starting SHL Assessment Streamlit app deployment"

# Set up environment variables
export PYTHONPATH=$PWD

# Check if API_URL is provided
if [ -z "$API_URL" ]; then
    echo "Warning: API_URL environment variable not set."
    echo "Using default API URL (http://localhost:8000)"
    export API_URL="http://localhost:8000"
else
    echo "Using API URL: $API_URL"
fi

# Test API connection
echo "Testing connection to API..."
if curl -s -f "$API_URL/health" > /dev/null; then
    echo "✅ API connection successful"
else
    echo "⚠️ Warning: Cannot connect to API at $API_URL"
    echo "Streamlit app will still start, but recommendations may not work"
fi

# Start the Streamlit app
echo "Starting Streamlit app on port 8501..."
streamlit run app/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0

echo "Streamlit app started successfully!"
echo "Streamlit running on http://localhost:8501" 