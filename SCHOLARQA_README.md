# ScholarQA Pipeline - AllenAI Best Practices Implementation

This document describes the refactored QA pipeline that incorporates best practices from AllenAI's ScholarQA library.

## Overview

The ScholarQA pipeline has been completely refactored to follow AllenAI's best practices, providing:

- **Metadata and citations** for each extracted quote (paper_id, title, score)
- **Planning/clustering step** to generate structured outlines (Background, Methods, Results, Discussion, Open Questions)
- **Tabular comparison** when multiple papers discuss the same dimension
- **Detailed processing trace** at each step for debugging and reproducibility
- **Modular components** (retriever, reranker, quote extraction, theme generation, report synthesis)
- **Structured JSON output** with sections, quotes (with metadata), optional comparison tables, and narrative report

## Architecture

### Modular Components

The pipeline is now composed of separate, interchangeable components:

1. **PassageRetriever** (`components/retriever.py`)
   - Retrieves top-k passages from ranked passages
   - Logs processing trace for debugging

2. **PassageReranker** (`components/reranker.py`)
   - Re-ranks passages based on semantic similarity to query
   - Uses cosine similarity with normalized embeddings

3. **QuoteExtractor** (`components/quote_extractor.py`)
   - Extracts relevant quotes with full metadata
   - Associates quotes with paper_id, title, score, similarity_score
   - Maintains traceability to original sources

4. **OutlinePlanner** (`components/planner.py`)
   - Generates structured outlines with standard sections
   - Clusters quotes into logical sections
   - Ensures Background section is always present

5. **ComparisonGenerator** (`components/comparison_generator.py`)
   - Creates tabular comparisons when multiple papers discuss same dimension
   - Identifies suitable sections for comparison (Methods, Results, etc.)
   - Generates structured comparison tables

6. **ReportSynthesizer** (`components/report_synthesizer.py`)
   - Synthesizes final structured report
   - Generates section narratives and overall summary
   - Combines quotes, tables, and processing trace

7. **ScholarQAPipeline** (`components/pipeline.py`)
   - Main orchestrator that coordinates all components
   - Manages processing flow and error handling
   - Maintains comprehensive processing trace

## API Endpoints

### Legacy Endpoints (Backward Compatibility)

- `POST /qa` - Legacy QA endpoint
- `POST /qa-pipeline` - Legacy pipeline endpoint

### New ScholarQA Endpoints

- `POST /scholarqa` - New ScholarQA pipeline endpoint
- `POST /scholarqa-pipeline` - Direct ScholarQA pipeline endpoint

## Usage Examples

### Using the New ScholarQA Pipeline

```python
from scholarqa.app.qa import process_scholarqa_pipeline

# Process query through new pipeline
result = process_scholarqa_pipeline(
    query="What are the latest advances in transformer architectures?",
    ranked_passages=ranked_passages,
    model="gpt-4o-mini",
    retrieval_top_k=50,
    rerank_top_k=20
)

# Access structured results
print(f"Summary: {result['summary']}")
print(f"Sections: {len(result['sections'])}")
print(f"Comparison tables: {len(result['comparison_tables'])}")
print(f"Total quotes: {result['metadata']['total_quotes']}")
print(f"Papers referenced: {result['metadata']['total_papers']}")
```

### API Request Example

```json
{
  "query": "What are the latest advances in transformer architectures?",
  "limit": 50,
  "model": "gpt-4o-mini",
  "retrieval_top_k": 50,
  "rerank_top_k": 20
}
```

### API Response Structure

```json
{
  "original_query": "What are the latest advances in transformer architectures?",
  "rewritten_query": "...",
  "keyword_query": "...",
  "gemini_filters": {...},
  "raw_gemini_output": "...",
  "scholarqa_result": {
    "query": "What are the latest advances in transformer architectures?",
    "summary": "Comprehensive summary of transformer advances...",
    "sections": [
      {
        "name": "Background",
        "description": "Introduction and background information",
        "narrative": "Generated narrative for this section...",
        "quotes": [
          {
            "quote_text": "Transformer architectures have revolutionized...",
            "paper_id": "arxiv:2023.12345",
            "title": "Advanced Transformer Architectures",
            "score": 0.95,
            "similarity_score": 0.88,
            "passage_index": 0,
            "metadata": {
              "cross_score": 0.92,
              "final_score": 0.95
            }
          }
        ],
        "quote_count": 5,
        "papers_referenced": ["arxiv:2023.12345", "arxiv:2023.67890"]
      }
    ],
    "comparison_tables": [
      {
        "section": "Methods",
        "headers": ["Architecture", "Dataset", "Performance"],
        "rows": [
          {
            "paper_title": "Advanced Transformer Architectures",
            "attributes": ["GPT-4", "WebText", "95% accuracy"]
          }
        ],
        "paper_count": 3,
        "metadata": {
          "papers": ["arxiv:2023.12345", "arxiv:2023.67890"],
          "generated_at": "comparison_step"
        }
      }
    ],
    "processing_trace": {
      "pipeline_start": true,
      "query": "What are the latest advances in transformer architectures?",
      "input_passages": 50,
      "retrieved_passages": 50,
      "embeddings_generated": 51,
      "reranked_passages": 20,
      "extracted_quotes": 15,
      "outline_generated": true,
      "sections_created": 4,
      "comparison_tables": 1,
      "pipeline_completed": true,
      "final_sections": 4,
      "final_quotes": 15,
      "final_papers": 8
    },
    "metadata": {
      "total_sections": 4,
      "total_quotes": 15,
      "total_papers": 8,
      "comparison_tables_count": 1
    }
  },
  "finding_info": {
    "total_passages_found": 50,
    "passages_used_for_qa": 50
  }
}
```

## Key Features

### 1. Metadata and Citations
Each extracted quote includes:
- `paper_id`: Unique identifier for the paper
- `title`: Paper title
- `score`: Relevance score
- `similarity_score`: Semantic similarity to query
- `passage_index`: Original passage index
- `metadata`: Additional metadata (cross_score, final_score)

### 2. Structured Outline
The pipeline generates structured outlines with standard sections:
- Background (always included)
- Methods
- Results
- Discussion
- Open Questions
- Custom sections based on content

### 3. Tabular Comparisons
When multiple papers discuss the same dimension, the pipeline:
- Identifies suitable sections for comparison
- Extracts comparable attributes (methods, datasets, results)
- Generates structured comparison tables
- Maintains paper references

### 4. Processing Trace
Comprehensive logging at each step:
- Passage retrieval statistics
- Embedding generation counts
- Reranking results
- Quote extraction details
- Outline generation info
- Comparison table creation
- Final synthesis metrics

### 5. Modular Design
Components can be easily swapped or extended:
- Each component has a clear interface
- Components are independent and testable
- Easy to add new retrieval or ranking strategies
- Simple to extend with new comparison logic

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for LLM components
- `OPENAI_MODEL`: Default model (default: "gpt-4o-mini")
- `PORT`: Server port (default: 8000)

### Pipeline Parameters
- `retrieval_top_k`: Number of passages to retrieve initially (default: 50)
- `rerank_top_k`: Number of passages to keep after reranking (default: 20)
- `model`: OpenAI model to use for LLM components

## Error Handling

The pipeline includes comprehensive error handling:
- Graceful degradation when components fail
- Detailed error messages in processing trace
- Fallback to empty sections when needed
- Error reporting in API responses

## Backward Compatibility

The refactored pipeline maintains backward compatibility:
- Legacy endpoints continue to work
- Old API formats are supported
- Existing integrations remain functional
- Gradual migration path available

## Performance Considerations

- Parallel processing where possible
- Efficient embedding generation
- Caching of intermediate results
- Configurable batch sizes
- Memory-efficient quote processing

## Future Extensions

The modular design enables easy extensions:
- New retrieval strategies
- Different ranking algorithms
- Custom comparison logic
- Additional output formats
- Integration with other LLM providers

