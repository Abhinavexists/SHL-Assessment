import os
import json
import re
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import time

class RecommendationEngine:
    def __init__(self, data_dir: str = None):
        """Initialize the recommendation engine."""
        self.data_dir = data_dir
        self.catalog_path = os.path.join(data_dir, "shl_catalog.json")
        
        # ChromaDB setup
        self.chroma_path = os.path.join(data_dir, "chroma_db")
        
        print("Loading sentence transformer model...")
        start_time = time.time()
        # Load the model
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # Warm up the model with a simple input
        self.model.encode(["This is a warmup sentence to initialize the model"])
        print(f"Model loaded in {time.time() - start_time:.2f} seconds")
        
        # Cache for embeddings to avoid recomputing
        self.embedding_cache = {}
        
        # Load or create catalog and DB
        self.load_catalog()
        self.load_or_create_db()
        
        # Precompute embeddings for common terms
        self._precompute_common_embeddings()
    
    def load_catalog(self):
        """Load the catalog of assessments."""
        try:
            with open(self.catalog_path, 'r') as f:
                self.catalog = json.load(f)
            print(f"Loaded catalog with {len(self.catalog)} assessments.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading catalog: {e}")
            self.catalog = []
    
    def load_or_create_db(self):
        """Load existing ChromaDB or create a new one if it doesn't exist."""
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.chroma_path)
        
        try:
            self.collection = self.client.get_collection("shl_assessments")
            print("Loaded existing ChromaDB collection.")
        except Exception as e:
            # Collection doesn't exist, create it
            print(f"Collection not found: {e}")
            print("Creating new ChromaDB collection...")
            self.create_db()
    
    def _precompute_common_embeddings(self):
        """Precompute embeddings for common terms to speed up queries."""
        common_terms = [
            "java developer", "python developer", "javascript developer",
            "software engineer", "data scientist", "leadership", 
            "cognitive assessment", "personality assessment",
            "technical", "remote", "adaptive", "problem solving",
            "communication skills", "collaboration", "teamwork",
            "sales", "customer service", "SQL", "database", "QA engineer",
            "testing", "selenium", "automation", "front-end", "CSS", "HTML",
            "administrative", "financial", "bank", "entry level"
        ]
        
        print("Precomputing embeddings for common terms...")
        start_time = time.time()
        for term in common_terms:
            # Store in cache
            self.embedding_cache[term] = self.model.encode(term)
        print(f"Precomputed {len(common_terms)} embeddings in {time.time() - start_time:.2f} seconds")
    
    def create_db(self):
        """Create a new ChromaDB collection for the assessments."""
        class SentenceTransformerEmbedding:
            def __init__(self, model, cache=None):
                self.model = model
                self.cache = cache or {}
            
            def __call__(self, input):
                if isinstance(input, list):
                    result = []
                    for text in input:
                        if text in self.cache:
                            result.append(self.cache[text].tolist())
                        else:
                            embedding = self.model.encode(text)
                            self.cache[text] = embedding
                            result.append(embedding.tolist())
                    return result
                else:
                    if input in self.cache:
                        return self.cache[input].tolist()
                    embedding = self.model.encode(input)
                    self.cache[input] = embedding
                    return embedding.tolist()
        
        try:
            if hasattr(self, 'collection'):
                self.client.delete_collection("shl_assessments")
                print("Deleted existing collection to create a fresh one.")
        except Exception as e:
            print(f"Error deleting collection: {e}")
        
        print("Creating ChromaDB collection with cached embeddings...")
        self.collection = self.client.create_collection(
            name="shl_assessments",
            embedding_function=SentenceTransformerEmbedding(self.model, self.embedding_cache)
        )
        
        if not self.catalog:
            print("Catalog is empty. Created empty ChromaDB collection.")
            return
        
        texts = []
        ids = []
        metadatas = []
        
        for i, assessment in enumerate(self.catalog):
            # Create a rich text representation for better semantic matching
            skills = ""
            if assessment.get("type", "") == "Technical":
                # Extract likely skills from the name and description
                for skill in ["Java", "Python", "JavaScript", "SQL", "HTML", "CSS", "Selenium"]:
                    if skill.lower() in assessment.get("name", "").lower() or skill.lower() in assessment.get("description", "").lower():
                        skills += f" {skill}"
            
            # Enhanced text representation with skill tags and metadata
            text = f"{assessment.get('name', '')}. {assessment.get('description', '')} Type: {assessment.get('type', '')}. Skills:{skills} Remote: {assessment.get('remote_support', '')} Adaptive: {assessment.get('adaptive_support', '')} Duration: {assessment.get('duration', '')}."
            texts.append(text)
            ids.append(str(i))
            
            # Ensure no None values in metadata
            metadatas.append({
                "name": assessment.get('name', '') or '',
                "url": assessment.get('url', '') or '',
                "remote_support": assessment.get('remote_support', 'No') or 'No',
                "adaptive_support": assessment.get('adaptive_support', 'No') or 'No',
                "duration": assessment.get('duration', 'Not specified') or 'Not specified',
                "type": assessment.get('type', 'General') or 'General',
                "description": assessment.get('description', '') or ''
            })
        
        # Add documents to the collection
        print("Adding assessments to ChromaDB collection...")
        chunk_size = 10  # Process in smaller batches to avoid memory issues
        for i in range(0, len(texts), chunk_size):
            end = min(i + chunk_size, len(texts))
            print(f"Adding batch {i//chunk_size + 1}/{(len(texts) + chunk_size - 1)//chunk_size}")
            self.collection.add(
                documents=texts[i:end],
                ids=ids[i:end],
                metadatas=metadatas[i:end]
            )
        
        print(f"Added {len(texts)} assessments to ChromaDB collection.")
    
    def parse_duration(self, duration_str: str) -> Optional[int]:
        """Parse duration string to get minutes as integer."""
        if not duration_str or duration_str == "Not specified":
            return None
        
        match = re.search(r'(\d+)', duration_str)
        if match:
            return int(match.group(1))
        return None
    
    def extract_constraints(self, query: str) -> Dict[str, Any]:
        """Extract constraints from the query."""
        constraints = {}
        
        # Parse duration constraints
        duration_pattern = re.search(r'(\d+)\s*min|\b(\d+)\s*minutes|\bunder\s*(\d+)|less\s*than\s*(\d+)|maximum\s*of\s*(\d+)|maximum\s*(\d+)|max\s*(\d+)|(\d+)\s*mins', query.lower())
        if duration_pattern:
            # Find the first non-None group
            for group in duration_pattern.groups():
                if group is not None:
                    constraints['max_duration'] = int(group)
                    break
        
        # Check for remote testing requirement
        if "remote" in query.lower():
            constraints['remote_support'] = "Yes"
        
        # Check for adaptive testing requirement
        if any(term in query.lower() for term in ["adaptive", "irt", "adaptive testing"]):
            constraints['adaptive_support'] = "Yes"
        
        # Extract skills/technologies
        skills = []
        tech_skills = [
            "java", "python", "javascript", "js", "c#", "c++", "typescript", 
            "sql", "r", "ruby", "php", "golang", "scala", "swift", "selenium",
            "html", "css", "html5", "css3", "react", "angular", "vue", "qa",
            "testing", "front-end", "database", "agile"
        ]
        
        for skill in tech_skills:
            if re.search(r'\b' + skill + r'\b', query.lower()):
                skills.append(skill)
        
        # Extract other skills and competencies
        if "problem solving" in query.lower() or "problem-solving" in query.lower():
            skills.append("problem-solving")
        
        if "verbal" in query.lower():
            skills.append("verbal reasoning")
        
        if "numerical" in query.lower():
            skills.append("numerical reasoning")
        
        if "analytical" in query.lower():
            skills.append("analytical")
        
        if skills:
            constraints['skills'] = skills
        
        # Detect test types
        test_types = []
        
        if any(term in query.lower() for term in ["programming", "coding", "developer", "engineer", "software"]):
            test_types.append("Technical")
        
        if any(term in query.lower() for term in ["cognitive", "reasoning", "thinking", "problem solving"]):
            test_types.append("Cognitive")
        
        if any(term in query.lower() for term in ["personality", "behavior", "trait", "character"]):
            test_types.append("Personality/Behavioral")
        
        if any(term in query.lower() for term in ["leadership", "management", "executive"]):
            test_types.append("Leadership")
        
        if any(term in query.lower() for term in ["sales", "customer service", "support"]):
            test_types.append("Role-specific")
        
        # Parse role information
        roles = []
        if "sales" in query.lower():
            roles.append("sales")
        
        if "administrative" in query.lower() or "admin" in query.lower():
            roles.append("administrative")
        
        if "bank" in query.lower() or "financial" in query.lower():
            roles.append("financial")
        
        if "entry" in query.lower() or "entry-level" in query.lower():
            roles.append("entry level")
        
        if roles:
            constraints['roles'] = roles
        
        if test_types:
            constraints['test_types'] = test_types
        
        return constraints
    
    def filter_by_constraints(self, candidates: List[Dict[str, Any]], constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter candidates by constraints."""
        filtered = candidates.copy()
        
        # Filter conditions
        if 'max_duration' in constraints:
            max_duration = constraints['max_duration']
            filtered = [
                candidate for candidate in filtered
                if (self.parse_duration(candidate['duration']) is None or 
                    self.parse_duration(candidate['duration']) <= max_duration)
            ]
        
        if 'remote_support' in constraints:
            filtered = [
                candidate for candidate in filtered
                if candidate['remote_support'] == constraints['remote_support']
            ]
        
        if 'adaptive_support' in constraints:
            filtered = [
                candidate for candidate in filtered
                if candidate['adaptive_support'] == constraints['adaptive_support']
            ]
        
        if 'test_types' in constraints:
            # Keep candidates that match any of the requested test types
            filtered = [
                candidate for candidate in filtered
                if any(candidate['type'] == test_type for test_type in constraints['test_types'])
            ]
        
        # If we have specific roles requested, prioritize assessments that match those roles
        if 'roles' in constraints:
            role_relevance = []
            for candidate in filtered:
                relevance = 0
                for role in constraints['roles']:
                    if 'name' in candidate and role.lower() in candidate['name'].lower():
                        relevance += 1
                    if 'description' in candidate and role.lower() in candidate['description'].lower():
                        relevance += 1
                role_relevance.append((candidate, relevance))
            
            # Sort by relevance but don't filter out completely
            role_relevance.sort(key=lambda x: x[1], reverse=True)
            filtered = [item[0] for item in role_relevance]
        
        # If we have specific skills requested, prioritize assessments that match those skills
        if 'skills' in constraints:
            skill_relevance = []
            for candidate in filtered:
                relevance = 0
                for skill in constraints['skills']:
                    if 'name' in candidate and skill.lower() in candidate['name'].lower():
                        relevance += 1
                    if 'description' in candidate and skill.lower() in candidate['description'].lower():
                        relevance += 1
                skill_relevance.append((candidate, relevance))
            
            # Sort by relevance but don't filter out completely
            skill_relevance.sort(key=lambda x: x[1], reverse=True)
            filtered = [item[0] for item in skill_relevance]
        
        return filtered
    
    def recommend(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Recommend assessments based on a query.
        
        Args:
            query: Natural language query or job description
            top_k: Number of recommendations to return
            
        Returns:
            List of recommended assessments
        """
        start_time = time.time()
        
        if not self.catalog or not hasattr(self, 'collection'):
            print("Recommendation failed: No catalog or collection available")
            return []
        
        constraints = self.extract_constraints(query)
        print(f"Extracted constraints: {constraints}")
        
        if self.collection.count() == 0:
            print("Collection is empty")
            return []
            
        # Query ChromaDB for similar assessments
        try:
            # Get at least 3x the requested number to ensure enough candidates after filtering
            k = min(top_k * 5, len(self.catalog))
            print(f"Querying ChromaDB for top {k} matches")
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )
            
            if not results["ids"] or len(results["ids"][0]) == 0:
                print("No results from ChromaDB query")
                return []
            
            # Get candidate assessments from results
            candidates = []
            for idx, metadata in zip(results["ids"][0], results["metadatas"][0]):
                assessment = {
                    "name": metadata["name"],
                    "url": metadata["url"],
                    "remote_support": metadata["remote_support"],
                    "adaptive_support": metadata["adaptive_support"],
                    "duration": metadata["duration"],
                    "type": metadata["type"],
                    "description": metadata.get("description", "")
                }
                candidates.append(assessment)
            
            print(f"Found {len(candidates)} initial candidates")
            
            # Filter by constraints
            filtered_candidates = self.filter_by_constraints(candidates, constraints)
            print(f"After filtering: {len(filtered_candidates)} candidates")
            
            # Limit to top_k
            result = filtered_candidates[:top_k]
            
            elapsed = time.time() - start_time
            print(f"Recommendation completed in {elapsed:.2f} seconds, returning {len(result)} results")
            
            return result
            
        except Exception as e:
            print(f"Error in recommendation: {e}")
            import traceback
            traceback.print_exc()
            return []

def main():
    """Test the recommendation engine."""
    engine = RecommendationEngine()
    
    test_queries = [
        "I am hiring for Java developers who can also collaborate effectively with my business teams. Looking for an assessment(s) that can be completed in 40 minutes.",
        "Looking for a Python and SQL assessment for data science roles",
        "Need a leadership assessment for senior executives"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        recommendations = engine.recommend(query, top_k=3)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec['name']} ({rec['type']}, {rec['duration']})")

if __name__ == "__main__":
    main() 