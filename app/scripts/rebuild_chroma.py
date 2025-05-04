#!/usr/bin/env python3
"""Rebuild the ChromaDB collection for SHL assessments."""

import os
import sys
import shutil
from app.models.recommendation_engine import RecommendationEngine

def main():
    """Rebuild the ChromaDB collection."""
    print("Rebuilding ChromaDB collection...")
    
    # Path to the data directory
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "data")
    
    # Path to the ChromaDB directory
    chroma_dir = os.path.join(data_dir, "chroma_db")
    
    # Delete existing ChromaDB directory if it exists
    if os.path.exists(chroma_dir):
        print(f"Deleting existing ChromaDB directory: {chroma_dir}")
        try:
            shutil.rmtree(chroma_dir)
            print("Directory deleted successfully")
        except Exception as e:
            print(f"Error deleting directory: {e}")
            return False
    
    # Create the recommendation engine (will create a new ChromaDB)
    try:
        engine = RecommendationEngine(data_dir=data_dir)
        print(f"Loaded catalog with {len(engine.catalog)} assessments")
        
        # Create a new database
        engine.create_db()
        
        # Test a query
        print("\nTesting a query...")
        results = engine.recommend("Java developer", top_k=3)
        print(f"Got {len(results)} results")
        
        for i, rec in enumerate(results, 1):
            print(f"{i}. {rec['name']} ({rec['type']})")
        
        print("\nChromaDB collection rebuilt successfully!")
        return True
    except Exception as e:
        print(f"Error rebuilding ChromaDB collection: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if main():
        print("Success! You can now start the API server.")
    else:
        print("Failed to rebuild ChromaDB collection.")
        sys.exit(1) 