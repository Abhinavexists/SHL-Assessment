# SHL Assessment Recommendation System - Solution 

## Approach

The SHL Intelligent Assessment Recommendation System is designed to help hiring managers find relevant assessments from the SHL catalog using natural language queries. The system follows a modular architecture consisting of:

1. **Data Pipeline**: A scraper collects assessment data from the SHL product catalog, extracting key metadata including assessment name, URL, remote testing support, adaptive/IRT support, duration, and test type. This data is stored in structured JSON format.

2. **Recommendation Engine**: The engine uses sentence-transformers to create embeddings for each assessment, enabling semantic search. When a query is received, it:
   - Converts the query to an embedding
   - Finds similar assessments using ChromaDB vector search
   - Extracts constraints (duration, skills, test types) from the query
   - Filters results based on these constraints
   - Returns the most relevant assessments

3. **API Layer**: A FastAPI backend exposes endpoints for health checks and recommendations.

## Evaluation Strategy

The system's performance is evaluated using standard information retrieval metrics:

- **Mean Recall@K**: Measures the proportion of relevant assessments found in the top K recommendations
- **MAP@K (Mean Average Precision@K)**: Measures the precision at each relevant recommendation, averaged over all queries

The evaluation uses a set of benchmark queries with known constraints (test type, duration, skills). For each query, we:

1. Determine which assessments in the catalog satisfy the constraints
2. Compare these "ground truth" assessments with the system's recommendations
3. Calculate Recall@3 and MAP@3

## Performance Insights

Based on evaluation, the system achieves:

- Precision@3: 0.8667
- Mean Recall@3: 0.2575
- MAP@3: 0.2575

The model achieves a **high precision@3** of <u>0.8667</u>, indicating that the recommendations in the top-3 positions are highly accurate. However, the **recall@3** is lower at <u>0.2575</u>, which is expected due to the constraint of selecting only **3 items per query**, while some queries have up to 25 relevant assessments.

- This trade-off highlights that while the model is effective at ranking the most relevant items at the top, it doesn't retrieve all possible relevant items in the limited top-k output.

- Evaluation can be done using -> [Evaluate](app/scripts/evaluate.py)

## Optimization Insights

Several optimizations enhance the system's performance:

1. **Constraint Extraction**: The system intelligently extracts implied constraints from natural language queries, such as duration limits and test types.

2. **Vector Search + Filtering**: We use a hybrid approach combining semantic similarity (vector search) with rule-based filtering, which outperforms either method alone.

3. **Text Augmentation**: Assessment descriptions are augmented with test type information to improve embedding quality.

4. **Caching**: Query results are cached to improve response times for repeated queries, and embeddings are pre-computed for common terms.

## System Architecture

The system follows a three-layer architecture:

1. **Data Layer**: JSON catalog and ChromaDB vector database
2. **Core Engine**: Sentence transformer model, recommendation logic, and constraint extraction
3. **Application Layer**: FastAPI backend and Streamlit UI

For a detailed architecture diagram, see [Architecture](Architecture.md).
