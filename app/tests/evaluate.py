import os
import json
import numpy as np
from typing import List, Dict, Any
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.recommendation_engine import RecommendationEngine

def load_eval_queries(data_dir: str) -> List[Dict[str, Any]]:
    """Load evaluation queries from the data directory."""
    eval_path = os.path.join(data_dir, "eval_queries.json")
    try:
        with open(eval_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading evaluation queries: {e}")
        return []

def precision_at_k(relevant_items: List[int], recommended_items: List[int], k: int) -> float:
    """Calculate precision@k."""
    # Ensure we only consider the first k items
    recommended_k = recommended_items[:k]
    relevant_count = sum(1 for item in recommended_k if item in relevant_items)
    return relevant_count / k if k > 0 else 0.0

def average_precision(relevant_items: List[int], recommended_items: List[int], k: int) -> float:
    """Calculate average precision."""
    hits = 0
    sum_precisions = 0.0
    
    for i, item in enumerate(recommended_items[:k], 1):
        if item in relevant_items:
            hits += 1
            precision_at_i = hits / i
            sum_precisions += precision_at_i
    
    return sum_precisions / len(relevant_items) if relevant_items else 0.0

def recall_at_k(relevant_items: List[int], recommended_items: List[int], k: int) -> float:
    """Calculate recall@k."""
    if not relevant_items:
        return 0.0
    
    recommended_k = recommended_items[:k]
    relevant_count = sum(1 for item in recommended_k if item in relevant_items)
    return relevant_count / len(relevant_items)

def is_assessment_relevant(assessment: Dict[str, Any], constraints: Dict[str, Any]) -> bool:
    """Check if an assessment is relevant based on constraints."""
    if 'max_duration' in constraints:
        duration_text = assessment.get('duration', 'Not specified')
        if duration_text != 'Not specified':
            try:
                duration = int(duration_text.split()[0])
                if duration > constraints['max_duration']:
                    return False
            except (ValueError, IndexError):
                pass
    
    if 'remote_support' in constraints:
        if assessment.get('remote_support') != constraints['remote_support']:
            return False
    
    if 'adaptive_support' in constraints:
        if assessment.get('adaptive_support') != constraints['adaptive_support']:
            return False
    
    if 'test_types' in constraints:
        if assessment.get('type') not in constraints['test_types']:
            return False
    
    # Check skills (this is more complex and would require text matching)
    # For simplicity, we'll consider an assessment relevant if it matches
    # the test type requirements
    
    return True

def evaluate_recommendations(engine: RecommendationEngine, eval_queries: List[Dict[str, Any]], k: int = 3) -> Dict[str, float]:
    """Evaluate the recommendation engine on a set of queries."""
    results = {
        "precision@k": [],
        "recall@k": [],
        "map@k": []
    }
    
    print(f"Evaluating on {len(eval_queries)} queries with k={k}")
    
    for query_data in eval_queries:
        query = query_data["query"]
        constraints = query_data["constraints"]
        
        recommendations = engine.recommend(query, top_k=10)
        
        # For evaluation, we'll consider all items in the catalog that match constraints as relevant
        relevant_items = [
            i for i, assessment in enumerate(engine.catalog)
            if is_assessment_relevant(assessment, constraints)
        ]
        
        recommended_indices = []
        for rec in recommendations:
            for i, assessment in enumerate(engine.catalog):
                if rec["name"] == assessment["name"]:
                    recommended_indices.append(i)
                    break
        
        prec = precision_at_k(relevant_items, recommended_indices, k)
        rec = recall_at_k(relevant_items, recommended_indices, k)
        ap = average_precision(relevant_items, recommended_indices, k)
        
        results["precision@k"].append(prec)
        results["recall@k"].append(rec)
        results["map@k"].append(ap)
        
        print(f"Query: {query}")
        print(f"  Precision@{k}: {prec:.4f}")
        print(f"  Recall@{k}: {rec:.4f}")
        print(f"  AP@{k}: {ap:.4f}")
        print(f"  # Relevant: {len(relevant_items)}")
        print(f"  # Recommended: {len(recommended_indices)}")
        print()
    
    mean_precision = np.mean(results["precision@k"])
    mean_recall = np.mean(results["recall@k"])
    mean_ap = np.mean(results["map@k"])
    
    print(f"Mean Precision@{k}: {mean_precision:.4f}")
    print(f"Mean Recall@{k}: {mean_recall:.4f}")
    print(f"MAP@{k}: {mean_ap:.4f}")
    
    return {
        f"precision@{k}": mean_precision,
        f"recall@{k}": mean_recall,
        f"map@{k}": mean_ap
    }

def main():
    """Run the evaluation."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    
    eval_queries = load_eval_queries(data_dir)
    if not eval_queries:
        print("No evaluation queries found. Exiting.")
        return
    
    engine = RecommendationEngine(data_dir=data_dir)
    results = evaluate_recommendations(engine, eval_queries, k=3)
    
    results_path = os.path.join(data_dir, "evaluation_results.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Evaluation results saved to {results_path}")

if __name__ == "__main__":
    main() 