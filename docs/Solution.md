# SHL Assessment Recommendation System: Comprehensive Solution

## Problem Statement

Develop an intelligent recommendation system that matches hiring managers with appropriate SHL assessments based on natural language queries, job descriptions, or specific requirements.

## Solution Overview

The SHL Assessment Recommendation System uses advanced NLP techniques to understand hiring requirements and recommend the most suitable assessments from SHL's catalog. The system intelligently processes natural language queries, extracts constraints, and ranks assessments based on relevance and requirement alignment.

## Technical Architecture

### Data Layer

**Assessment Catalog Management**
- Created a structured JSON catalog of 45 SHL assessments
- Each assessment contains:
  - Name and description
  - Assessment type (Technical, Cognitive, Personality, Role-specific)
  - Duration (minutes)
  - Remote testing support (Yes/No)
  - Adaptive testing support (Yes/No)
  - URL to SHL website

**Vector Database**
- Implemented ChromaDB as a vector store for semantic search
- Organized assessments into collections for efficient retrieval
- Pre-computed embeddings for all assessment descriptions

### Core Engine

**Semantic Matching Engine**
- Used Sentence Transformers to create embeddings from natural language
- Implemented cosine similarity for matching queries to assessments
- Created a scoring system that balances semantic relevance with constraint satisfaction

**Constraint Extraction**
- Developed pattern recognition for duration requirements (e.g., "under 40 minutes")
- Implemented classification for assessment type requirements
- Created detection for remote/adaptive support requirements

### API Layer

**FastAPI Backend**
- Designed RESTful endpoints for recommendations
- Implemented standard JSON response format:
```json
{
  "recommended_assessments": [
    {
      "url": "https://www.shl.com/solutions/products/product-catalog/view/python-new/",
      "adaptive_support": "No",
      "description": "Multi-choice test that measures the knowledge of Python programming...",
      "duration": 11,
      "remote_support": "Yes",
      "test_type": ["Knowledge & Skills"],
      "name": "Python Assessment"
    }
  ]
}
```
- Implemented caching for improved performance
- Added CORS support for cross-origin requests
- Created health check endpoint for system monitoring

### User Interface

**Streamlit Application**
- Designed a modern, responsive UI with dark/light mode support
- Implemented a two-column layout for better organization
- Created visual assessment cards with attribute badges:
  - Type indicator (color-coded by assessment category)
  - Remote testing support indicator
  - Adaptive testing support indicator
  - Duration information
- Added interactive features:
  - Example query suggestions
  - Assessment comparison tool
  - Expandable descriptions
  - Direct links to SHL website

## Implementation Details

### Key Components

1. **Data Collection & Processing**
   - Scraper for SHL catalog (app/scripts/scrape_catalog.py)
   - ChromaDB vector database builder (app/scripts/rebuild_chroma.py)

2. **Recommendation Engine**
   - Core semantic search functionality (app/models/recommendation_engine.py)
   - Constraint extraction and processing

3. **API Service**
   - FastAPI endpoints (app/api/main.py)
   - Response caching and error handling

4. **User Interface**
   - Streamlit application (app/ui/streamlit_app.py)
   - Custom CSS styling for modern appearance
   - Loading animations and progress indicators

### Deployment Strategy

- Created separate deployment scripts for API and UI components
- Added Docker support for containerized deployment
- Implemented environment variable configuration for flexibility
- Ensured cross-origin support for distributed hosting

## Performance Optimizations

- **Embedding Precomputation**: Precomputed embeddings for all assessments
- **Response Caching**: Implemented LRU cache for frequent queries
- **Efficient Batching**: Optimized vector operations with batching
- **Warm-up Queries**: Initialized the model with warm-up queries on startup

## Use Cases Supported

1. **Skill-Based Assessment Finding**
   - Example: "Looking for assessments to test Java developers who will collaborate with business teams"

2. **Time-Constrained Selection**
   - Example: "Need Python assessments that can be completed in under 45 minutes"

3. **Role-Specific Recommendations**
   - Example: "ICICI Bank Assistant Admin role, need assessments for 0-2 years experience"

4. **Test Type Specification**
   - Example: "Looking for cognitive assessments for analyst roles"

## Results and Benefits

- **Improved Selection Process**: Reduced time to find appropriate assessments
- **Better Matching**: Improved relevance of assessment recommendations
- **User-Friendly Experience**: Intuitive interface with visual guidance
- **Flexible Deployment**: Separate components allow for distributed hosting

This solution successfully bridges the gap between hiring requirements and assessment selection, providing an intelligent, user-friendly system that enhances the SHL assessment discovery process.
