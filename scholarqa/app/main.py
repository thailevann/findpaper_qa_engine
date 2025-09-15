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
)
from .embedding import embed_single
from .qa import filter_passages, generate_themes, generate_final_report

app = FastAPI(title="ScholarQA Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))


