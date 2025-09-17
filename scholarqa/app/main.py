from __future__ import annotations

import os
from fastapi import FastAPI, HTTPException
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

app = FastAPI(title="ScholarQA Backend", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "2.0.0", "features": ["legacy_api", "scholarqa_pipeline"]}


@app.post("/embed", response_model=EmbedResponse)
async def embed_endpoint(payload: EmbedRequest) -> EmbedResponse:
    try:
        embedding = embed_single(payload.text)
        return EmbedResponse(embedding=embedding)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/filter-quotes", response_model=FilterQuotesResponse)
async def filter_quotes_endpoint(payload: FilterQuotesRequest) -> FilterQuotesResponse:
    try:
        filtered, indices, scores = filter_passages(payload.query, payload.passages, payload.top_k)
        return FilterQuotesResponse(query=payload.query, filtered_passages=filtered, indices=indices, scores=scores)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-themes", response_model=GenerateThemesResponse)
async def generate_themes_endpoint(payload: GenerateThemesRequest) -> GenerateThemesResponse:
    try:
        themes = generate_themes(payload.query, payload.passages, payload.model, payload.max_themes)
        return GenerateThemesResponse(themes=[{"name": t["name"], "quotes": t["quotes"]} for t in themes])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/final-report", response_model=FinalReportResponse)
async def final_report_endpoint(payload: FinalReportRequest) -> FinalReportResponse:
    try:
        report = generate_final_report(payload.query, [t.dict() for t in payload.themes], payload.model)
        return FinalReportResponse(report=report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/qa-pipeline", response_model=QAResponse)
async def qa_pipeline_endpoint(payload: QARequest) -> QAResponse:
    """
    Legacy QA pipeline endpoint for backward compatibility.
    """
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
        
        return QAResponse(
            query=result["query"],
            filtered_passages=result["filtered_passages"],
            themes=[Theme(name=t["name"], quotes=t["quotes"]) for t in result["themes"]],
            final_report=result["final_report"],
            processing_info=result["processing_info"]
        )
    except Exception as e:
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
        
        return ScholarQAResponse(
            structured_report=structured_report,
            success=True,
            error_message=None
        )
    except Exception as e:
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


