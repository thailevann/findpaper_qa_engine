from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
from online_team.preprocess.query_processeor import decompose_query_with_gemini
from online_team.rag.keyword_search import KeywordSearch
from online_team.rag.reranker import PaperReranker
from online_team.rag.semantic_search import SemanticSearch
from sentence_transformers import SentenceTransformer
from config import CROSS_ENCODER_MODEL, SEMANTIC_MODEL
from dotenv import load_dotenv
import os
from scholarqa.app.qa import process_qa_pipeline

load_dotenv()

app = FastAPI(title="FindPaper QA Engine", version="1.0.0")
reranker = PaperReranker(CROSS_ENCODER_MODEL)
model = SentenceTransformer(SEMANTIC_MODEL)

class PaperQuery(BaseModel):
    query: str
    limit: Optional[int] = 5

class RankedPassage(BaseModel):
    paper_id: str
    title: str
    evidence: str
    cross_score: float
    final_score: float

class QAQuery(BaseModel):
    query: str
    limit: Optional[int] = 50
    max_themes: Optional[int] = 5
    model: Optional[str] = None

def convert_filters(gemini_filters: dict) -> dict:
    filters = {}
    if "year" in gemini_filters:
        start_year, end_year = gemini_filters["year"].split("-")
        filters["update_date"] = f"{start_year}-01-01:{end_year}-12-31"
    return filters

def retrieve_papers(payload: PaperQuery):
    # --- Step 1: Decompose query ---
    processed, raw_content = decompose_query_with_gemini(payload.query)
    filters = convert_filters(processed.search_filters)

    # --- Step 2: Generate embeddings ---
    query_embeddings = [
        model.encode(payload.query, normalize_embeddings=True).tolist(),
        model.encode(processed.rewritten_query or payload.query, normalize_embeddings=True).tolist()
    ]

    # --- Step 3: Keyword search ---
    keyword_query_text = processed.keyword_query or processed.rewritten_query or payload.query
    key_search = KeywordSearch()
    key_scores = key_search.search(
        keyword_query_text,
        top_k=payload.limit,
        filters=filters
    )

    # --- Step 4: Semantic search ---
    sem_search = SemanticSearch()
    sem_scores_all = {}
    for q_emb in query_embeddings:
        sem_scores = sem_search.search(
            q_emb,
            top_k=payload.limit,
            filters=filters
        )
        for pid, s in sem_scores.items():
            sem_scores_all[pid] = max(sem_scores_all.get(pid, 0), s)

    # --- Step 5: Rerank ---
    final_results = reranker.rerank(
        query_text=keyword_query_text,
        query_embeddings=query_embeddings,
        sem_scores=sem_scores_all,
        key_scores=key_scores,
        top_final=payload.limit,
        alpha=1.0,
        beta=1.0,
        index_name=key_search.index_name
    )

    return processed, raw_content, final_results

@app.post("/search_passsages")
def search_papers(payload: PaperQuery):
    processed, raw_content, final_results = retrieve_papers(payload)
    return {
        "original_query": payload.query,
        "rewritten_query": processed.rewritten_query,
        "keyword_query": processed.keyword_query,
        "gemini_filters": processed.search_filters,
        "raw_gemini_output": raw_content,
        "matched_count": len(final_results),
        "matched_papers": final_results
    }

@app.post("/top_papers")
def top_papers(payload: PaperQuery):
    processed, raw_content, final_results = retrieve_papers(payload)

    # --- Aggregate chunks per paper ---
    papers_dict = {}
    for r in final_results:
        pid = r["paper_id"]
        if pid not in papers_dict:
            papers_dict[pid] = {
                "paper_id": pid,
                "title": r["title"],   # <-- thêm title ở đây
                "chunks": []
            }
        papers_dict[pid]["chunks"].append({
            "evidence": r["evidence"],  # r["evidence"] = semantic chunk
            "cross_score": r["cross_score"],
            "final_score": r["final_score"]
        })

    # Chọn chunk có cross_score cao nhất
    for pid, paper in papers_dict.items():
        best_chunk = max(paper["chunks"], key=lambda x: x["cross_score"])
        paper["final_score"] = best_chunk["final_score"]
        paper["evidence"] = best_chunk["evidence"]

    # Top papers
    top_papers = sorted(papers_dict.values(), key=lambda x: x["final_score"], reverse=True)[:payload.limit]

    # Loại bỏ mảng chunks để JSON gọn
    for paper in top_papers:
        paper.pop("chunks", None) 

    return {
        "original_query": payload.query,
        "rewritten_query": processed.rewritten_query,
        "keyword_query": processed.keyword_query,
        "gemini_filters": processed.search_filters,
        "raw_gemini_output": raw_content,
        "matched_count": len(top_papers),
        "matched_papers": top_papers
    }

@app.post("/qa")
def qa_endpoint(payload: QAQuery):
    """
    Complete QA endpoint that combines finding and QA pipelines.
    This follows the flow diagram: Finding Paper -> QA pipeline -> Final answer
    """
    # Step 1: Use the finding pipeline to get top-ranked passages
    processed, raw_content, final_results = retrieve_papers(PaperQuery(query=payload.query, limit=payload.limit))
    
    # Step 2: Convert results to ranked passages format
    ranked_passages = []
    for result in final_results:
        ranked_passages.append({
            "paper_id": result["paper_id"],
            "title": result["title"],
            "evidence": result["evidence"],
            "cross_score": result["cross_score"],
            "final_score": result["final_score"]
        })
    
    # Step 3: Process through QA pipeline
    qa_result = process_qa_pipeline(
        query=payload.query,
        ranked_passages=ranked_passages,
        model=payload.model,
        max_themes=payload.max_themes
    )
    
    return {
        "original_query": payload.query,
        "rewritten_query": processed.rewritten_query,
        "keyword_query": processed.keyword_query,
        "gemini_filters": processed.search_filters,
        "raw_gemini_output": raw_content,
        "qa_result": {
            "query": qa_result["query"],
            "filtered_passages": qa_result["filtered_passages"],
            "themes": qa_result["themes"],
            "final_report": qa_result["final_report"],
            "processing_info": qa_result["processing_info"]
        },
        "finding_info": {
            "total_passages_found": len(final_results),
            "passages_used_for_qa": len(ranked_passages)
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "message": "FindPaper QA Engine is running"}

