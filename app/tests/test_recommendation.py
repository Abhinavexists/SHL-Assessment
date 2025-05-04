#!/usr/bin/env python3
"""Test the recommendation engine directly."""

import os
import sys
import json
from app.models.recommendation_engine import RecommendationEngine

def main():
    """Test the recommendation engine."""
    print("Testing recommendation engine...")
    
    # Path to the data directory
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "data")
    
    # Create the recommendation engine
    try:
        engine = RecommendationEngine(data_dir=data_dir)
        print(f"Loaded catalog with {len(engine.catalog)} assessments")
        
        # Test queries
        test_queries = [
            "Java developer tests under 40 minutes",
            "Python and SQL developer",
            "Leadership assessment for senior executives",
            "Administrative assistant test under 30 minutes",
            "QA engineer with selenium experience"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            print("=" * 80)
            
            constraints = engine.extract_constraints(query)
            print(f"Extracted constraints: {constraints}")
            
            results = engine.recommend(query, top_k=3)
            print(f"Got {len(results)} results")
            
            for i, rec in enumerate(results, 1):
                print(f"{i}. {rec['name']} ({rec['type']}, {rec['duration']})")
                print(f"   URL: {rec['url']}")
                if 'description' in rec:
                    description = rec['description'][:100] + "..." if len(rec['description']) > 100 else rec['description']
                    print(f"   Description: {description}")
                print(f"   Remote: {rec['remote_support']}, Adaptive: {rec['adaptive_support']}")
                print()
            
        print("\nRecommendation engine test completed!")
        return True
    except Exception as e:
        print(f"Error testing recommendation engine: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if main():
        print("Success! The recommendation engine is working correctly.")
    else:
        print("Failed to test recommendation engine.")
        sys.exit(1) 