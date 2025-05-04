import os
import sys
import time
import hashlib
import re
from functools import lru_cache
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
from contextlib import asynccontextmanager
import logging

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.recommendation_engine import RecommendationEngine

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize recommendation engine at startup."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    app.state.engine = RecommendationEngine(data_dir=data_dir)
    
    # Preload with a warmup query
    print("Warming up recommendation engine with initial query...")
    try:
        app.state.engine.recommend("Java developer", top_k=3)
        print("Recommendation engine warmup complete")
    except Exception as e:
        print(f"Warmup error: {e}")
    
    yield
    
    print("Shutting down recommendation engine...")

# Initialize the app
app = FastAPI(
    title="SHL Assessment Recommendation API",
    description="API for recommending SHL assessments based on natural language queries.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Streamlit app URL(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Input model for recommendation request
class QueryInput(BaseModel):
    query: str
    max_results: Optional[int] = 10

# Output models for API response
class AssessmentResponse(BaseModel):
    url: str
    adaptive_support: str
    description: str
    duration: Union[int, str]
    remote_support: str
    test_type: List[str]
    name: str

class RecommendationResponse(BaseModel):
    recommended_assessments: List[AssessmentResponse]

# Cache for recommendation results
recommendations_cache = {}
CACHE_TTL = 3600 

def hash_query(query: str) -> str:
    """Create a hash of the query string for caching."""
    return hashlib.md5(query.encode('utf-8')).hexdigest()

def parse_duration(duration_str: str) -> int:
    """Parse duration string to minutes as integer."""
    if not duration_str or duration_str == "Not specified":
        return 0
    
    match = re.search(r'(\d+)', duration_str)
    if match:
        return int(match.group(1))
    return 0

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if not hasattr(app.state, 'engine') or app.state.engine is None or not hasattr(app.state.engine, 'catalog') or not app.state.engine.catalog:
        return {"status": "error"}
    return {"status": "healthy"}

@lru_cache(maxsize=100)
def get_cached_recommendations(query: str, max_results: int) -> List[Dict[str, Any]]:
    """Get recommendations with caching."""
    return app.state.engine.recommend(query, top_k=max_results)

@app.post("/recommend", response_model=RecommendationResponse)
async def recommend(query_input: QueryInput):
    """
    Recommend SHL assessments based on the query.
    
    Args:
        query_input: QueryInput object containing query and optional max_results
        
    Returns:
        RecommendationResponse with list of recommended assessments
    """
    try:
        if not hasattr(app.state, 'engine') or app.state.engine is None:
            raise HTTPException(status_code=500, detail="Recommendation engine not initialized")
        
        query = query_input.query
        max_results = query_input.max_results
        
        # Log request
        print(f"Processing recommendation request: '{query[:50]}...' (max_results={max_results})")
        start_time = time.time()
        
        # Create a cache key from query hash and max_results
        cache_key = f"{hash_query(query)}_{max_results}"
        
        # Check if we have a cached result and if it's still valid
        if cache_key in recommendations_cache:
            cached_result, timestamp = recommendations_cache[cache_key]
            if time.time() - timestamp < CACHE_TTL:
                print(f"Returning cached result for query: {query[:30]}... (took {time.time() - start_time:.2f}s)")
                return RecommendationResponse(recommended_assessments=cached_result)
        
        # Not in cache or expired, get new recommendations
        recommendations = get_cached_recommendations(query, max_results)
        
        # Convert to response format
        formatted_recommendations = []
        for rec in recommendations:
            try:
                assessment = AssessmentResponse(
                    url=rec["url"],
                    adaptive_support=rec["adaptive_support"],
                    description=rec.get("description", "No description available"),
                    duration=parse_duration(rec["duration"]),
                    remote_support=rec["remote_support"],
                    test_type=[rec["type"]],
                    name=rec["name"]
                )
                formatted_recommendations.append(assessment)
            except Exception as e:
                print(f"Error formatting recommendation: {e}")
                print(f"Recommendation data: {rec}")
        
        # Cache the result
        recommendations_cache[cache_key] = (formatted_recommendations, time.time())
        
        # Return the response
        print(f"Recommendation completed in {time.time() - start_time:.2f}s, returning {len(formatted_recommendations)} results")
        return RecommendationResponse(recommended_assessments=formatted_recommendations)
    except Exception as e:
        print(f"Error in recommendation endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
