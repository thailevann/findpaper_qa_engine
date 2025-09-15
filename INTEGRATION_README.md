# FindPaper QA Engine - Integration Guide

## Overview

This system integrates the **Finding Paper** pipeline (`online_team`) with the **QA pipeline** (`scholarqa`) to create a complete question-answering system for research papers.

## System Architecture

The system follows the flow diagram with two main components:

### 1. Finding Paper Pipeline (`online_team`)
- **Query Processing**: Uses Gemini to decompose and rewrite queries
- **Keyword Search**: Elasticsearch-based search on titles and abstracts
- **Semantic Search**: Vector similarity search using sentence transformers
- **Reranking**: Cross-encoder reranking for final relevance scoring
- **Output**: Top-ranked passages with scores

### 2. QA Pipeline (`scholarqa`)
- **Quote Selection**: LLM selects relevant verbatim quotes
- **Theme Generation**: LLM groups quotes into thematic categories
- **Content Synthesis**: LLM synthesizes comprehensive answers
- **Output**: Structured final report with themes and citations

## API Endpoints

### Main Integration Endpoint

#### `POST /qa`
Complete QA pipeline that combines finding and QA modules.

**Request:**
```json
{
  "query": "What are the latest advances in machine learning?",
  "limit": 50,
  "max_themes": 5,
  "model": "gpt-4o-mini"
}
```

**Response:**
```json
{
  "original_query": "What are the latest advances in machine learning?",
  "rewritten_query": "...",
  "keyword_query": "...",
  "gemini_filters": {...},
  "qa_result": {
    "query": "...",
    "filtered_passages": [...],
    "themes": [
      {
        "name": "Introduction/Background",
        "quotes": [...]
      }
    ],
    "final_report": "Comprehensive answer...",
    "processing_info": {
      "total_passages": 50,
      "selected_quotes": 15,
      "themes_generated": 5,
      "papers_used": 25
    }
  },
  "finding_info": {
    "total_passages_found": 50,
    "passages_used_for_qa": 50
  }
}
```

### Individual Module Endpoints

#### Finding Paper Endpoints
- `POST /search_passsages` - Get ranked passages
- `POST /top_papers` - Get top papers aggregated by paper ID

#### QA Module Endpoints
- `POST /qa-pipeline` - Process ranked passages through QA pipeline
- `POST /filter-quotes` - Filter relevant quotes
- `POST /generate-themes` - Generate thematic categories
- `POST /final-report` - Generate final answer

### Utility Endpoints
- `GET /health` - Health check

## Environment Variables

Required environment variables:

```bash
# Elasticsearch
ES_HOST=localhost:9200
ES_INDEX=papers_text

# Models
CROSS_ENCODER_MODEL=your-cross-encoder-model
SEMANTIC_MODEL=your-semantic-model

# API Keys
GOOGLE_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key
```

## Running the System

1. **Start Elasticsearch** (if not already running)
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Start the server**:
   ```bash
   python app.py
   ```
4. **Test the integration**:
   ```bash
   python test_integration.py
   ```

## Flow Diagram Implementation

The system implements the complete flow from your diagram:

1. **User Query** → Query decomposition with Gemini
2. **Keyword Search** → Elasticsearch search on abstracts/titles
3. **Semantic Search** → Vector similarity search
4. **First Rerank** → Combined keyword + semantic scores
5. **Second Rerank** → Cross-encoder reranking
6. **Top 50 Passages** → Input to QA pipeline
7. **Quote Selection** → LLM selects relevant quotes
8. **Theme Generation** → LLM groups quotes into themes
9. **Content Synthesis** → LLM generates final answer
10. **Final Report** → Comprehensive answer with citations

## Testing

Use the provided test script to verify integration:

```bash
python test_integration.py
```

This will test:
- Health endpoint
- Complete QA pipeline
- Individual ScholarQA endpoints

## Notes

- The `online_team` finding modules are unchanged as requested
- The `scholarqa` module has been enhanced with the complete QA pipeline
- The main `app.py` integrates both modules seamlessly
- All endpoints maintain backward compatibility

