from __future__ import annotations

import os
import logging
import time
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    EmbedRequest,
    EmbedResponse,
    FilterQuotesRequest,
    FilterQuotesResponse,
    GenerateThemesRequest,
    GenerateThemesResponse,
    FinalReportRequest,
    FinalReportResponse,
    QARequest,
    QAResponse,
    ScholarQARequest,
    ScholarQAResponse,
    Theme,
)
from .embedding import embed_single
from .qa import filter_passages, generate_themes, generate_final_report, process_qa_pipeline, process_scholarqa_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scholarqa_api.log')
    ]
)
logger = logging.getLogger(__name__)

# Response counter
response_counter: Dict[str, int] = {
    "health": 0,
    "embed": 0,
    "filter_quotes": 0,
    "generate_themes": 0,
    "final_report": 0,
    "qa_pipeline": 0,
    "scholarqa_pipeline": 0,
    "total_requests": 0
}

app = FastAPI(title="ScholarQA Backend", version="2.0.0")

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"📥 INCOMING REQUEST: {request.method} {request.url.path}")
    logger.info(f"   Client: {request.client.host if request.client else 'unknown'}")
    logger.info(f"   Headers: {dict(request.headers)}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Update counters
    endpoint = request.url.path.lstrip('/')
    if endpoint in response_counter:
        response_counter[endpoint] += 1
    response_counter["total_requests"] += 1
    
    # Log response
    logger.info(f"📤 OUTGOING RESPONSE: {response.status_code}")
    logger.info(f"   Processing time: {process_time:.3f}s")
    logger.info(f"   Endpoint count: {response_counter.get(endpoint, 0)}")
    logger.info(f"   Total requests: {response_counter['total_requests']}")
    
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    logger.info("🏥 Health check requested")
    return {
        "status": "ok", 
        "version": "2.0.0", 
        "features": ["legacy_api", "scholarqa_pipeline"],
        "response_counts": response_counter,
        "uptime": datetime.now().isoformat()
    }


@app.post("/embed", response_model=EmbedResponse)
async def embed_endpoint(payload: EmbedRequest) -> EmbedResponse:
    logger.info(f"🔤 Embed request: text length={len(payload.text)}")
    try:
        embedding = embed_single(payload.text)
        logger.info(f"✅ Embed successful: vector size={len(embedding)}")
        return EmbedResponse(embedding=embedding)
    except Exception as e:
        logger.error(f"❌ Embed failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/filter-quotes", response_model=FilterQuotesResponse)
async def filter_quotes_endpoint(payload: FilterQuotesRequest) -> FilterQuotesResponse:
    logger.info(f"🔍 Filter quotes request: query='{payload.query[:50]}...', passages={len(payload.passages)}, top_k={payload.top_k}")
    try:
        filtered, indices, scores = filter_passages(payload.query, payload.passages, payload.top_k)
        logger.info(f"✅ Filter quotes successful: filtered={len(filtered)}")
        return FilterQuotesResponse(query=payload.query, filtered_passages=filtered, indices=indices, scores=scores)
    except Exception as e:
        logger.error(f"❌ Filter quotes failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-themes", response_model=GenerateThemesResponse)
async def generate_themes_endpoint(payload: GenerateThemesRequest) -> GenerateThemesResponse:
    logger.info(f"🎨 Generate themes request: query='{payload.query[:50]}...', passages={len(payload.passages)}, max_themes={payload.max_themes}")
    try:
        themes = generate_themes(payload.query, payload.passages, payload.model, payload.max_themes)
        logger.info(f"✅ Generate themes successful: themes={len(themes)}")
        return GenerateThemesResponse(themes=[{"name": t["name"], "quotes": t["quotes"]} for t in themes])
    except Exception as e:
        logger.error(f"❌ Generate themes failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/final-report", response_model=FinalReportResponse)
async def final_report_endpoint(payload: FinalReportRequest) -> FinalReportResponse:
    logger.info(f"📝 Final report request: query='{payload.query[:50]}...', themes={len(payload.themes)}")
    try:
        report = generate_final_report(payload.query, [t.dict() for t in payload.themes], payload.model)
        logger.info(f"✅ Final report successful: report length={len(report)}")
        return FinalReportResponse(report=report)
    except Exception as e:
        logger.error(f"❌ Final report failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/qa-pipeline", response_model=QAResponse)
async def qa_pipeline_endpoint(payload: QARequest) -> QAResponse:
    """
    Legacy QA pipeline endpoint for backward compatibility.
    """
    logger.info(f"🔄 Legacy QA pipeline request: query='{payload.query[:50]}...', passages={len(payload.ranked_passages)}, max_themes={payload.max_themes}")
    try:
        # Convert RankedPassage objects to dictionaries
        ranked_passages = [p.dict() for p in payload.ranked_passages]
        
        # Process through the legacy QA pipeline
        result = process_qa_pipeline(
            query=payload.query,
            ranked_passages=ranked_passages,
            model=payload.model,
            max_themes=payload.max_themes
        )
        
        logger.info(f"✅ Legacy QA pipeline successful: themes={len(result['themes'])}, quotes={len(result['filtered_passages'])}")
        return QAResponse(
            query=result["query"],
            filtered_passages=result["filtered_passages"],
            themes=[Theme(name=t["name"], quotes=t["quotes"]) for t in result["themes"]],
            final_report=result["final_report"],
            processing_info=result["processing_info"]
        )
    except Exception as e:
        logger.error(f"❌ Legacy QA pipeline failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scholarqa-pipeline", response_model=ScholarQAResponse)
async def scholarqa_pipeline_endpoint(payload: ScholarQARequest) -> ScholarQAResponse:
    """
    New ScholarQA pipeline endpoint following AllenAI best practices.
    
    Features:
    - Metadata and citations for each quote
    - Structured outline with planning/clustering
    - Tabular comparisons when multiple papers discuss same dimension
    - Detailed processing trace for debugging
    - Modular components for extensibility
    - Structured JSON output with sections, quotes, tables, and narrative
    """
    logger.info(f"🚀 ScholarQA pipeline request: query='{payload.query[:50]}...', passages={len(payload.ranked_passages)}, retrieval_top_k={payload.retrieval_top_k}, rerank_top_k={payload.rerank_top_k}")
    try:
        # Convert RankedPassage objects to dictionaries
        ranked_passages = [p.dict() for p in payload.ranked_passages]
        
        # Process through the new ScholarQA pipeline
        structured_report = process_scholarqa_pipeline(
            query=payload.query,
            ranked_passages=ranked_passages,
            model=payload.model,
            retrieval_top_k=payload.retrieval_top_k,
            rerank_top_k=payload.rerank_top_k
        )
        
        logger.info(f"✅ ScholarQA pipeline successful: sections={structured_report.get('metadata', {}).get('total_sections', 0)}, quotes={structured_report.get('metadata', {}).get('total_quotes', 0)}, papers={structured_report.get('metadata', {}).get('total_papers', 0)}")
        return ScholarQAResponse(
            structured_report=structured_report,
            success=True,
            error_message=None
        )
    except Exception as e:
        logger.error(f"❌ ScholarQA pipeline failed: {str(e)}")
        return ScholarQAResponse(
            structured_report={
                "query": payload.query,
                "summary": f"Error processing query: {str(e)}",
                "sections": [],
                "comparison_tables": [],
                "processing_trace": {"error": str(e), "pipeline_failed": True},
                "metadata": {
                    "total_sections": 0,
                    "total_quotes": 0,
                    "total_papers": 0,
                    "comparison_tables_count": 0
                }
            },
            success=False,
            error_message=str(e)
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))


