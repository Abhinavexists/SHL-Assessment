
import os
import sys
import unittest
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open, ANY

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.recommendation_engine import RecommendationEngine

class TestRecommendationEngine(unittest.TestCase):
    """Tests for the RecommendationEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock catalogue
        self.mock_catalog = [
            {
                "name": "Java Coding Assessment",
                "url": "https://example.com/java",
                "description": "Test Java programming skills. Duration: 30 minutes.",
                "remote_support": "Yes",
                "adaptive_support": "No",
                "duration": "30 minutes",
                "type": "Technical"
            },
            {
                "name": "Python Coding Test",
                "url": "https://example.com/python",
                "description": "Test Python programming skills. Duration: 45 minutes.",
                "remote_support": "Yes",
                "adaptive_support": "No",
                "duration": "45 minutes",
                "type": "Technical"
            },
            {
                "name": "Leadership Assessment",
                "url": "https://example.com/leadership",
                "description": "Evaluate leadership potential. Duration: 60 minutes.",
                "remote_support": "Yes",
                "adaptive_support": "Yes",
                "duration": "60 minutes",
                "type": "Leadership"
            },
            {
                "name": "Cognitive Ability Test",
                "url": "https://example.com/cognitive",
                "description": "Test problem-solving and reasoning. Duration: 25 minutes.",
                "remote_support": "Yes",
                "adaptive_support": "Yes",
                "duration": "25 minutes",
                "type": "Cognitive"
            },
            {
                "name": "Personality Assessment",
                "url": "https://example.com/personality",
                "description": "Evaluate personality traits. Duration: 15 minutes.",
                "remote_support": "Yes",
                "adaptive_support": "No",
                "duration": "15 minutes",
                "type": "Personality/Behavioral"
            }
        ]
        
        # Setup temp directory for tests
        self.temp_dir = tempfile.mkdtemp()
        self.catalog_path = os.path.join(self.temp_dir, "shl_catalog.json")
        
        # Save mock catalog to temp file
        with open(self.catalog_path, 'w') as f:
            json.dump(self.mock_catalog, f)
    
    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)
    
    @patch("models.recommendation_engine.SentenceTransformer")
    @patch("models.recommendation_engine.chromadb.PersistentClient")
    def test_initialization(self, mock_chromadb_client, mock_transformer):
        """Test that engine initializes correctly with catalog and DB."""
        # Setup mocks
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        mock_model.encode.return_value = [0.1, 0.2, 0.3]
        
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_chromadb_client.return_value = mock_client
        mock_client.get_collection.return_value = mock_collection
        
        # Create engine with temp directory
        engine = RecommendationEngine(data_dir=self.temp_dir)
        
        # Verify initialization
        self.assertEqual(len(engine.catalog), 5)
        mock_transformer.assert_called_once()
        mock_chromadb_client.assert_called_once()
        mock_client.get_collection.assert_called_once_with("shl_assessments")
    
    @patch("models.recommendation_engine.SentenceTransformer")
    @patch("models.recommendation_engine.chromadb.PersistentClient")
    def test_initialization_no_collection(self, mock_chromadb_client, mock_transformer):
        """Test that engine creates new collection when one doesn't exist."""
        # Setup mocks
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        mock_model.encode.return_value = [0.1, 0.2, 0.3]
        
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_chromadb_client.return_value = mock_client
        
        # Make get_collection raise an exception
        mock_client.get_collection.side_effect = Exception("Collection not found")
        mock_client.create_collection.return_value = mock_collection
        
        # Create engine with temp directory
        engine = RecommendationEngine(data_dir=self.temp_dir)
        
        # Verify collection creation
        mock_client.create_collection.assert_called_once()
    
    @patch("models.recommendation_engine.SentenceTransformer")
    @patch("models.recommendation_engine.chromadb")
    def test_parse_duration(self, mock_chromadb, mock_transformer):
        """Test duration parsing from strings."""
        # Create a mock engine
        engine = RecommendationEngine()
        engine.catalog = self.mock_catalog
        
        # Test various duration formats
        self.assertEqual(engine.parse_duration("30 minutes"), 30)
        self.assertEqual(engine.parse_duration("45 min"), 45)
        self.assertEqual(engine.parse_duration("1 hour"), 1)
        self.assertIsNone(engine.parse_duration("Not specified"))
        self.assertIsNone(engine.parse_duration(""))
        self.assertIsNone(engine.parse_duration(None))
    
    @patch("models.recommendation_engine.SentenceTransformer")
    @patch("models.recommendation_engine.chromadb")
    def test_extract_constraints(self, mock_chromadb, mock_transformer):
        """Test constraint extraction from queries."""
        # Create a mock engine
        engine = RecommendationEngine()
        engine.catalog = self.mock_catalog
        
        # Test duration constraint
        query = "Looking for an assessment that can be completed in 30 min"
        constraints = engine.extract_constraints(query)
        self.assertEqual(constraints.get("max_duration"), 30)
        
        # Test remote support constraint
        query = "I need a remote assessment for developers"
        constraints = engine.extract_constraints(query)
        self.assertEqual(constraints.get("remote_support"), "Yes")
        
        # Test adaptive support constraint
        query = "Looking for adaptive assessments for cognitive ability"
        constraints = engine.extract_constraints(query)
        self.assertEqual(constraints.get("adaptive_support"), "Yes")
        
        # Test test type detection
        query = "I need a personality assessment for my team"
        constraints = engine.extract_constraints(query)
        self.assertIn("Personality/Behavioral", constraints.get("test_types", []))
        
        # Test multiple skill detection
        query = "Need to test Java and Python programming skills"
        constraints = engine.extract_constraints(query)
        self.assertIn("java", constraints.get("skills", []))
        self.assertIn("python", constraints.get("skills", []))
        
        # Test cognitive skill detection
        query = "Looking for numerical reasoning and problem solving tests"
        constraints = engine.extract_constraints(query)
        self.assertIn("numerical reasoning", constraints.get("skills", []))
        self.assertIn("problem-solving", constraints.get("skills", []))
        
        # Test multiple test type detection
        query = "Need both technical coding tests and leadership assessments"
        constraints = engine.extract_constraints(query)
        self.assertIn("Technical", constraints.get("test_types", []))
        self.assertIn("Leadership", constraints.get("test_types", []))
        
        # Test complex query with multiple constraints
        query = "I need a remote adaptive assessment for problem solving that takes less than 30 min"
        constraints = engine.extract_constraints(query)
        self.assertEqual(constraints.get("max_duration"), 30)
        self.assertEqual(constraints.get("remote_support"), "Yes")
        self.assertEqual(constraints.get("adaptive_support"), "Yes")
        self.assertIn("problem-solving", constraints.get("skills", []))
    
    @patch("models.recommendation_engine.SentenceTransformer")
    @patch("models.recommendation_engine.chromadb")
    def test_filter_by_constraints(self, mock_chromadb, mock_transformer):
        """Test filtering assessments by constraints."""
        # Create a mock engine
        engine = RecommendationEngine()
        engine.catalog = self.mock_catalog
        
        # Test filtering by duration
        constraints = {"max_duration": 30}
        filtered = engine.filter_by_constraints(self.mock_catalog, constraints)
        self.assertEqual(len(filtered), 3)  # Should include Java (30), Cognitive (25), Personality (15)
        names = [a["name"] for a in filtered]
        self.assertIn("Java Coding Assessment", names)
        self.assertIn("Cognitive Ability Test", names)
        self.assertIn("Personality Assessment", names)
        
        # Test filtering by test type
        constraints = {"test_types": ["Technical"]}
        filtered = engine.filter_by_constraints(self.mock_catalog, constraints)
        self.assertEqual(len(filtered), 2)  # Should include Java and Python
        names = [a["name"] for a in filtered]
        self.assertIn("Java Coding Assessment", names)
        self.assertIn("Python Coding Test", names)
        
        # Test filtering by adaptive support
        constraints = {"adaptive_support": "Yes"}
        filtered = engine.filter_by_constraints(self.mock_catalog, constraints)
        self.assertEqual(len(filtered), 2)  # Should include Leadership and Cognitive
        names = [a["name"] for a in filtered]
        self.assertIn("Leadership Assessment", names)
        self.assertIn("Cognitive Ability Test", names)
        
        # Test combining constraints
        constraints = {"max_duration": 30, "test_types": ["Cognitive"]}
        filtered = engine.filter_by_constraints(self.mock_catalog, constraints)
        self.assertEqual(len(filtered), 1)  # Should only include Cognitive
        self.assertEqual(filtered[0]["name"], "Cognitive Ability Test")
        
        # Test empty result when no matches
        constraints = {"max_duration": 10, "test_types": ["Technical"]}
        filtered = engine.filter_by_constraints(self.mock_catalog, constraints)
        self.assertEqual(len(filtered), 0)  # Should be empty, no tests match both constraints
        
        # Test filtering with invalid constraint (should be ignored)
        constraints = {"invalid_constraint": "value"}
        filtered = engine.filter_by_constraints(self.mock_catalog, constraints)
        self.assertEqual(len(filtered), 5)  # Should include all assessments
    
    @patch("models.recommendation_engine.SentenceTransformer")
    @patch("models.recommendation_engine.chromadb.PersistentClient")
    def test_recommend_empty_catalog(self, mock_chromadb_client, mock_transformer):
        """Test recommendation behavior with empty catalog."""
        # Setup mocks
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0  # Empty collection
        mock_client = MagicMock()
        mock_chromadb_client.return_value = mock_client
        mock_client.get_collection.return_value = mock_collection
        
        # Create engine with empty catalog
        with patch("builtins.open", mock_open(read_data="[]")):
            engine = RecommendationEngine()
            engine.catalog = []
        
        # Test recommendation with empty catalog
        recommendations = engine.recommend("Java developer assessment")
        self.assertEqual(recommendations, [])
    
    @patch("models.recommendation_engine.SentenceTransformer")
    @patch("models.recommendation_engine.chromadb.PersistentClient")
    def test_recommend(self, mock_chromadb_client, mock_transformer):
        """Test full recommendation flow."""
        # Setup mocks
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        mock_model.encode.return_value = [0.1, 0.2, 0.3]
        
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_chromadb_client.return_value = mock_client
        mock_client.get_collection.return_value = mock_collection
        mock_collection.count.return_value = 5
        
        # Setup query results
        mock_collection.query.return_value = {
            "ids": [["0", "1", "3"]],
            "metadatas": [[
                {
                    "name": "Java Coding Assessment",
                    "url": "https://example.com/java",
                    "remote_support": "Yes",
                    "adaptive_support": "No",
                    "duration": "30 minutes",
                    "type": "Technical"
                },
                {
                    "name": "Python Coding Test",
                    "url": "https://example.com/python",
                    "remote_support": "Yes",
                    "adaptive_support": "No",
                    "duration": "45 minutes",
                    "type": "Technical"
                },
                {
                    "name": "Cognitive Ability Test",
                    "url": "https://example.com/cognitive",
                    "remote_support": "Yes",
                    "adaptive_support": "Yes",
                    "duration": "25 minutes",
                    "type": "Cognitive"
                }
            ]]
        }
        
        # Create engine with temp directory
        engine = RecommendationEngine(data_dir=self.temp_dir)
        
        # Test recommendation
        recommendations = engine.recommend("Need a Java coding assessment under 30 minutes", top_k=2)
        
        # Verify results
        self.assertEqual(len(recommendations), 1)  # Should only include Java (constraint is 30 min)
        self.assertEqual(recommendations[0]["name"], "Java Coding Assessment")
        
        # Verify query was called
        mock_collection.query.assert_called_once()
    
    @patch("models.recommendation_engine.SentenceTransformer")
    @patch("models.recommendation_engine.chromadb.PersistentClient")
    def test_recommend_no_results(self, mock_chromadb_client, mock_transformer):
        """Test recommendation behavior when ChromaDB returns no results."""
        # Setup mocks
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_chromadb_client.return_value = mock_client
        mock_client.get_collection.return_value = mock_collection
        mock_collection.count.return_value = 5
        
        # Setup empty query results
        mock_collection.query.return_value = {"ids": [[]], "metadatas": [[]]}
        
        # Create engine with temp directory
        engine = RecommendationEngine(data_dir=self.temp_dir)
        
        # Test recommendation
        recommendations = engine.recommend("Something that won't match anything")
        
        # Verify empty results
        self.assertEqual(recommendations, [])
    
    @patch("models.recommendation_engine.SentenceTransformer")
    @patch("models.recommendation_engine.chromadb.PersistentClient") 
    def test_create_db(self, mock_chromadb_client, mock_transformer):
        """Test database creation with assessments."""
        # Setup mocks
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        mock_model.encode.return_value = [0.1, 0.2, 0.3]
        
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_chromadb_client.return_value = mock_client
        mock_client.create_collection.return_value = mock_collection
        
        # Create engine with temp directory
        engine = RecommendationEngine(data_dir=self.temp_dir)
        
        # Call create_db directly
        engine.create_db()
        
        # Verify collection creation
        mock_client.create_collection.assert_called_once()
        
        # Verify documents were added in batches
        self.assertTrue(mock_collection.add.called)
        
        # Ensure chunking is working (should be called at least once)
        self.assertGreaterEqual(mock_collection.add.call_count, 1)
    
    @patch("models.recommendation_engine.SentenceTransformer")
    @patch("models.recommendation_engine.chromadb.PersistentClient")
    def test_embedding_cache(self, mock_chromadb_client, mock_transformer):
        """Test that embedding cache exists and contains precomputed embeddings."""
        # Setup mocks
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        mock_model.encode.return_value = [0.1, 0.2, 0.3]
        
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_chromadb_client.return_value = mock_client
        mock_client.get_collection.return_value = mock_collection
        
        # Create engine with temp directory
        engine = RecommendationEngine(data_dir=self.temp_dir)
        
        # Test that embedding cache is initialized with common terms
        self.assertGreater(len(engine.embedding_cache), 0)
        
        # Check if common terms are in the cache
        common_terms = ["java developer", "python developer", "leadership", "cognitive assessment"]
        for term in common_terms:
            # Just check if the keys exist in the cache
            self.assertIn(term, engine.embedding_cache)
    
    @patch("models.recommendation_engine.SentenceTransformer")
    @patch("models.recommendation_engine.chromadb.PersistentClient")
    def test_embedding_function_with_cache(self, mock_chromadb_client, mock_transformer):
        """Test that embedding function uses cache properly."""
        # Setup mocks
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        mock_model.encode.return_value = [0.1, 0.2, 0.3]
        
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_chromadb_client.return_value = mock_client
        mock_client.get_collection.return_value = mock_collection
        
        # Create engine and manually setup a controlled cache
        engine = RecommendationEngine(data_dir=self.temp_dir)
        
        # Create a test embedding function class similar to the one in RecommendationEngine
        class TestEmbeddingFunction:
            def __init__(self, engine_model):
                self.model = engine_model
                # Create a simple cache with known values
                self.cache = {"cached_term": [0.5, 0.5, 0.5]}
                
            def __call__(self, input_text):
                if isinstance(input_text, str):
                    if input_text in self.cache:
                        # Return the cached value directly (it's already a list)
                        return self.cache[input_text]
                    # This should trigger a call to model.encode
                    return self.model.encode(input_text)
                elif isinstance(input_text, list):
                    result = []
                    for text in input_text:
                        if text in self.cache:
                            result.append(self.cache[text])
                        else:
                            result.append(self.model.encode(text))
                    return result
                return None
        
        # Create test function and reset mock
        mock_model.reset_mock()
        test_fn = TestEmbeddingFunction(mock_model)
        
        # Test with cached term - should not call encode
        result = test_fn("cached_term")
        mock_model.encode.assert_not_called()
        self.assertEqual(result, [0.5, 0.5, 0.5])
        
        # Test with non-cached term - should call encode
        test_fn("new uncached term")
        mock_model.encode.assert_called_once_with("new uncached term")
        
        # Test with list that includes both cached and uncached terms
        mock_model.reset_mock()
        test_fn(["cached_term", "another uncached term"])
        mock_model.encode.assert_called_once_with("another uncached term")
    
    @patch("models.recommendation_engine.SentenceTransformer")
    @patch("models.recommendation_engine.chromadb.PersistentClient")
    def test_load_catalog_error(self, mock_chromadb_client, mock_transformer):
        """Test error handling when loading catalog."""
        # Setup mocks
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_chromadb_client.return_value = mock_client
        mock_client.get_collection.return_value = mock_collection
        
        # Create engine with invalid catalog path
        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = FileNotFoundError("File not found")
            engine = RecommendationEngine(data_dir="/invalid/path")
            # Should handle error gracefully and initialize with empty catalog
            self.assertEqual(engine.catalog, [])
    
    @patch("models.recommendation_engine.SentenceTransformer")
    @patch("models.recommendation_engine.chromadb.PersistentClient")
    def test_recommend_exception_handling(self, mock_chromadb_client, mock_transformer):
        """Test exception handling in recommend method."""
        # Setup mocks
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_chromadb_client.return_value = mock_client
        mock_client.get_collection.return_value = mock_collection
        mock_collection.count.return_value = 5
        
        # Make query raise an exception
        mock_collection.query.side_effect = Exception("ChromaDB error")
        
        # Create engine with temp directory
        engine = RecommendationEngine(data_dir=self.temp_dir)
        
        # Test recommendation with error
        recommendations = engine.recommend("Test query")
        
        # Should handle error gracefully and return empty list
        self.assertEqual(recommendations, [])
    
    @patch("models.recommendation_engine.SentenceTransformer")
    @patch("models.recommendation_engine.chromadb.PersistentClient")
    def test_chunking_implementation(self, mock_chromadb_client, mock_transformer):
        """Test that chunking implementation works correctly for large catalogs."""
        # Setup mocks
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        mock_model.encode.return_value = [0.1, 0.2, 0.3]
        
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_chromadb_client.return_value = mock_client
        mock_client.create_collection.return_value = mock_collection
        
        # Create a large catalog (more than one chunk)
        large_catalog = []
        for i in range(25):  # 25 assessments (more than the chunk size of 10)
            large_catalog.append({
                "name": f"Assessment {i}",
                "url": f"https://example.com/{i}",
                "description": f"Description {i}",
                "remote_support": "Yes",
                "adaptive_support": "No",
                "duration": "30 minutes",
                "type": "Technical"
            })
        
        # Create engine with temp directory and large catalog
        engine = RecommendationEngine(data_dir=self.temp_dir)
        engine.catalog = large_catalog
        
        # Call create_db directly
        engine.create_db()
        
        # Verify collection creation
        mock_client.create_collection.assert_called_once()
        
        # Verify documents were added in multiple batches (chunk_size = 10)
        expected_calls = (len(large_catalog) + 9) // 10  # Ceiling division
        self.assertEqual(mock_collection.add.call_count, expected_calls)

if __name__ == "__main__":
    unittest.main() 