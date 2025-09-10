import os
from dotenv import load_dotenv
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

# Load env
load_dotenv()

# Import internal modules
from online_team.preprocess.query_processeor import decompose_query_with_gemini
from online_team.rag.local_retriever import retrieve_papers

app = FastAPI(title="Gemini + Local Retriever API")


# --- Request model ---
class PaperQuery(BaseModel):
    query: str
    limit: Optional[int] = 5


# --- Helper: convert Gemini filters to local retriever filters ---
def convert_filters(gemini_filters: dict) -> dict:
    filters = {}
    if "year" in gemini_filters:
        start_year, end_year = gemini_filters["year"].split("-")
        filters["update_date"] = f"{start_year}-01-01:{end_year}-12-31"
    if "venue" in gemini_filters:
        filters["venue"] = gemini_filters["venue"]
    # Uncomment if you want to include fieldsOfStudy
    # if "fieldsOfStudy" in gemini_filters:
    #     filters["field_of_study"] = gemini_filters["fieldsOfStudy"]
    return filters


# --- API endpoint ---
@app.post("/search_papers")
def search_papers(payload: PaperQuery):
    # 1. Decompose query with Gemini
    processed, raw_content = decompose_query_with_gemini(payload.query)

    # 2. Convert filters
    filters = convert_filters(processed.search_filters)

    # 3. Retrieve papers locally
    matched = retrieve_papers(
        query=processed.keyword_query or processed.rewritten_query,
        filters=filters,
        limit=payload.limit
    )

    # 4. Return structured response
    return {
        "original_query": payload.query,
        "rewritten_query": processed.rewritten_query,
        "keyword_query": processed.keyword_query,
        "gemini_filters": processed.search_filters,
        "raw_gemini_output": raw_content,
        "matched_count": len(matched),
        "matched_papers": matched
    }


# --- Run: uvicorn app_api:app --reload
