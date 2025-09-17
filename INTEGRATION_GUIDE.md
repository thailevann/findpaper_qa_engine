# ScholarQA Pipeline Integration Guide

## Overview

This guide documents the successful integration of the ScholarQA pipeline with the existing `online_team` finding module and frontend. The integration maintains full backward compatibility while providing enhanced structured output.

## ✅ Integration Status: COMPLETE

### Key Achievements

1. **Perfect Compatibility**: ScholarQA pipeline works seamlessly with existing `online_team` modules
2. **No Modifications Required**: The `online_team/` folder remains completely unchanged
3. **Frontend Integration**: TypeScript types and API methods updated for new structured output
4. **Backward Compatibility**: Legacy endpoints continue to work unchanged
5. **Enhanced Features**: New structured output with metadata, citations, and comparison tables

## 🔄 Data Flow Integration

### Current Architecture
```
User Query → online_team/preprocess → online_team/rag → ScholarQA Pipeline → Structured Output
```

### Detailed Flow
1. **Query Processing** (`online_team/preprocess/query_processeor.py`)
   - Decomposes user query using Gemini
   - Extracts search filters, rewritten queries
   - Returns structured query components

2. **Paper Finding** (`online_team/rag/`)
   - `KeywordSearch`: Elasticsearch keyword matching
   - `SemanticSearch`: Vector similarity search
   - `PaperReranker`: Cross-encoder reranking
   - Returns ranked passages with metadata

3. **ScholarQA Pipeline** (`scholarqa/app/components/`)
   - `PassageRetriever`: Retrieves top passages
   - `PassageReranker`: Semantic reranking
   - `QuoteExtractor`: Extracts quotes with metadata
   - `OutlinePlanner`: Generates structured outlines
   - `ComparisonGenerator`: Creates comparison tables
   - `ReportSynthesizer`: Synthesizes final report

## 📊 Data Format Compatibility

### online_team Output Format
```python
# PaperReranker.rerank() returns:
{
    "paper_id": "arxiv:2023.12345",
    "title": "Paper Title",
    "evidence": "Passage text content",
    "cross_score": 0.95,
    "final_score": 0.92
}
```

### ScholarQA Input Format
```python
# ScholarQA expects exactly the same format:
ranked_passages = [
    {
        "paper_id": str,
        "title": str, 
        "evidence": str,  # This becomes the passage text
        "cross_score": float,
        "final_score": float
    }
]
```

**✅ Perfect Match**: No data transformation needed!

## 🚀 API Endpoints

### Legacy Endpoints (Backward Compatibility)
- `POST /qa` - Original QA endpoint
- `POST /search_passsages` - Passage search
- `POST /top_papers` - Top papers aggregation

### New ScholarQA Endpoints
- `POST /scholarqa` - Enhanced ScholarQA pipeline
- `POST /scholarqa-pipeline` - Direct ScholarQA access

### Health Check
- `GET /health` - Returns version and available features

## 💻 Frontend Integration

### Updated TypeScript Types

```typescript
// New ScholarQA types
export interface ScholarQARequest {
  query: string
  limit?: number
  model?: string
  retrieval_top_k?: number
  rerank_top_k?: number
}

export interface ScholarQAResponse {
  original_query: string
  rewritten_query: string
  keyword_query: string
  gemini_filters: Record<string, any>
  raw_gemini_output: string
  scholarqa_result: StructuredReport
  finding_info: {
    total_passages_found: number
    passages_used_for_qa: number
  }
}

export interface StructuredReport {
  query: string
  summary: string
  sections: SectionInfo[]
  comparison_tables: ComparisonTable[]
  processing_trace: ProcessingTrace
  metadata: ReportMetadata
}
```

### API Methods

```typescript
// Legacy method (unchanged)
FindPaperAPI.searchQA(request: QARequest): Promise<QAResponse>

// New ScholarQA method
FindPaperAPI.searchScholarQA(request: ScholarQARequest): Promise<ScholarQAResponse>
```

## 🔧 Configuration

### Environment Variables
```bash
# Required for ScholarQA pipeline
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4o-mini  # Optional, defaults to gpt-4o-mini

# Required for online_team modules
GEMINI_API_KEY=your-gemini-key  # For query decomposition
ELASTICSEARCH_URL=http://localhost:9200  # For paper search
```

### Pipeline Parameters
```python
# ScholarQA pipeline configuration
process_scholarqa_pipeline(
    query="user query",
    ranked_passages=ranked_passages,  # From online_team
    model="gpt-4o-mini",              # Optional
    retrieval_top_k=50,               # Passages to retrieve
    rerank_top_k=20                   # Passages to keep after reranking
)
```

## 📈 Enhanced Output Features

### 1. Metadata and Citations
Each quote includes full traceability:
```json
{
  "quote_text": "Actual quote text",
  "paper_id": "arxiv:2023.12345",
  "title": "Paper Title",
  "score": 0.95,
  "similarity_score": 0.88,
  "passage_index": 0,
  "metadata": {
    "cross_score": 0.92,
    "final_score": 0.95
  }
}
```

### 2. Structured Sections
Organized content with narratives:
```json
{
  "name": "Background",
  "description": "Introduction and background information",
  "narrative": "Generated narrative for this section...",
  "quotes": [...],
  "quote_count": 5,
  "papers_referenced": ["arxiv:2023.12345", "arxiv:2023.67890"]
}
```

### 3. Comparison Tables
When multiple papers discuss same dimension:
```json
{
  "section": "Methods",
  "headers": ["Architecture", "Dataset", "Performance"],
  "rows": [
    {
      "paper_title": "Paper Title",
      "attributes": ["GPT-4", "WebText", "95% accuracy"]
    }
  ],
  "paper_count": 3
}
```

### 4. Processing Trace
Complete debugging information:
```json
{
  "pipeline_start": true,
  "query": "user query",
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
}
```

## 🧪 Testing

### Integration Test
```bash
python test_integration_complete.py
```

This test verifies:
- Module imports and compatibility
- Query decomposition (online_team)
- Finding pipeline (online_team)
- ScholarQA pipeline integration
- Data format compatibility
- API endpoint functionality

### Frontend Test
```typescript
// Test new ScholarQA endpoint
const response = await FindPaperAPI.searchScholarQA({
  query: "What are transformer architectures?",
  limit: 50,
  model: "gpt-4o-mini"
});

console.log(response.scholarqa_result.sections);
console.log(response.scholarqa_result.comparison_tables);
console.log(response.scholarqa_result.processing_trace);
```

## 🚀 Deployment

### Backend Deployment
1. Ensure all dependencies are installed
2. Set required environment variables
3. Start Elasticsearch (for online_team)
4. Run the FastAPI server:
   ```bash
   python app.py
   ```

### Frontend Deployment
1. Update API types (already done)
2. Use new ScholarQA endpoint for enhanced features
3. Maintain legacy endpoint for backward compatibility

## 🔄 Migration Strategy

### Phase 1: Parallel Operation
- Deploy ScholarQA pipeline alongside existing system
- Both legacy and new endpoints available
- Gradual testing and validation

### Phase 2: Frontend Updates
- Update frontend to use new ScholarQA endpoint
- Implement new UI components for structured output
- Maintain fallback to legacy endpoint

### Phase 3: Full Migration
- Switch to ScholarQA as primary endpoint
- Keep legacy endpoint for emergency fallback
- Monitor performance and user feedback

## 📋 Checklist

### ✅ Completed
- [x] ScholarQA pipeline implementation
- [x] online_team compatibility verification
- [x] Frontend TypeScript types updated
- [x] API endpoints implemented
- [x] Backward compatibility maintained
- [x] Integration tests created
- [x] Documentation completed

### 🔄 Ready for Production
- [x] All integration tests pass
- [x] No modifications to online_team folder
- [x] Enhanced structured output available
- [x] Legacy endpoints continue working
- [x] Frontend integration ready

## 🎯 Benefits

1. **Enhanced Output**: Structured sections, metadata, comparison tables
2. **Better Traceability**: Every quote linked to source paper
3. **Improved Debugging**: Comprehensive processing trace
4. **Modular Design**: Easy to extend or modify components
5. **Backward Compatibility**: Existing integrations continue working
6. **No Breaking Changes**: online_team folder unchanged

## 🔮 Future Enhancements

The modular architecture enables easy future improvements:
- Custom retrieval strategies
- Different ranking algorithms
- Additional comparison logic
- Multi-language support
- Advanced clustering algorithms
- Integration with other LLM providers

## 📞 Support

For questions or issues:
1. Check integration test results
2. Verify environment variables
3. Review processing trace for debugging
4. Check API endpoint responses
5. Consult this integration guide

The ScholarQA pipeline is now fully integrated and ready for production use!
