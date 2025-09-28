from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from online_team.preprocess.query_processor_enhanced import EnhancedQueryProcessor, QueryProcessorConfig
from online_team.rag.parallel_search import ParallelSearchPipeline, SearchPipelineConfig
from online_team.rag.keyword_search import KeywordSearchConfig
from online_team.rag.semantic_search import SemanticSearchConfig
from online_team.rag.reranker import RerankerConfig
from sentence_transformers import SentenceTransformer
from config import CROSS_ENCODER_MODEL, SEMANTIC_MODEL
from dotenv import load_dotenv
import os
import asyncio
from scholarqa.app.qa import process_qa_pipeline, process_scholarqa_pipeline

load_dotenv()

app = FastAPI(title="FindPaper QA Engine", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],   # Allows all headers
)

# Initialize optimized pipeline components
def initialize_pipeline():
    """Initialize the optimized search pipeline"""
    # Configuration for balanced performance
    keyword_config = KeywordSearchConfig(
        top_k=50,
        title_boost=5.0,
        abstract_boost=3.0,
        multi_match_boost=2.0
    )
    
    semantic_config = SemanticSearchConfig(
        top_k=50,
        knn_num_candidates=50,
        vector_fields=["title_embedding", "abstract_embedding", "chunks.embedding"]
    )
    
    reranker_config = RerankerConfig(
        top_final=20,
        use_crossencoder=True,
        crossencoder_model=CROSS_ENCODER_MODEL,
        batch_size=32,
        use_distil=True
    )

    pipeline_config = SearchPipelineConfig(
        keyword_config=keyword_config,
        semantic_config=semantic_config,
        reranker_config=reranker_config,
        use_parallel_search=True,
        use_multi_field_semantic=True,
        enable_reranking=True,
        search_timeout=30.0,
        rerank_timeout=60.0
    )
    
    # Initialize pipeline
    pipeline = ParallelSearchPipeline(
        es_url=os.getenv("ES_HOST", "http://localhost:9200"),
        text_index=os.getenv("ES_INDEX", "papers_text"),
        vector_index=os.getenv("ES_VECTOR_INDEX", "papers_vectors"),
        config=pipeline_config
    )
    
    # Initialize query processor with caching
    query_processor_config = QueryProcessorConfig(
        enable_caching=True,
        cache_ttl=3600,  # 1 hour cache
        enable_fallback=True,
        use_regex_fallback=True
    )
    
    query_processor = EnhancedQueryProcessor(config=query_processor_config)
    
    return pipeline, query_processor

# Initialize components
pipeline, query_processor = initialize_pipeline()
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

class ScholarQAQuery(BaseModel):
    query: str
    limit: Optional[int] = 50
    model: Optional[str] = None
    retrieval_top_k: Optional[int] = 50
    rerank_top_k: Optional[int] = 20

def convert_filters(gemini_filters: dict) -> dict:
    """Convert Gemini filters to Elasticsearch format"""
    filters = {}
    if "year" in gemini_filters:
        start_year, end_year = gemini_filters["year"].split("-")
        filters["update_date"] = f"{start_year}-01-01:{end_year}-12-31"
    if "venue" in gemini_filters:
        filters["venue"] = gemini_filters["venue"]
    if "fieldsOfStudy" in gemini_filters:
        filters["fieldsOfStudy"] = gemini_filters["fieldsOfStudy"]
    return filters

async def retrieve_papers_optimized(payload: PaperQuery):
    """
    Optimized paper retrieval using the new parallel pipeline
    """
    # --- Step 1: Process query with caching ---
    processed, raw_content = query_processor.process_query(payload.query)
    filters = convert_filters(processed.search_filters)

    # --- Step 2: Generate embeddings ---
    query_embeddings = [
        model.encode(payload.query, normalize_embeddings=True).tolist(),
        model.encode(processed.rewritten_query or payload.query, normalize_embeddings=True).tolist()
    ]

    # --- Step 3: Run optimized parallel search with reranking ---
    final_results = await pipeline.search_with_reranking(
        query_text=processed.rewritten_query or payload.query,
        query_embedding=query_embeddings[0],  # <-- truyền vector đã encode
        filters=filters,
        top_k=payload.limit,
        top_final=payload.limit
    )



    return processed, raw_content, final_results

def retrieve_papers_legacy(payload: PaperQuery):
    """
    Legacy paper retrieval for backward compatibility
    """
    # --- Step 1: Decompose query ---
    from online_team.preprocess.query_processeor import decompose_query_with_gemini
    processed, raw_content = decompose_query_with_gemini(payload.query)
    filters = convert_filters(processed.search_filters)

    # --- Step 2: Generate embeddings ---
    query_embeddings = [
        model.encode(payload.query, normalize_embeddings=True).tolist(),
        model.encode(processed.rewritten_query or payload.query, normalize_embeddings=True).tolist()
    ]

    # --- Step 3: Keyword search ---
    keyword_query_text = processed.keyword_query or processed.rewritten_query or payload.query
    from online_team.rag.keyword_search import KeywordSearch
    key_search = KeywordSearch()
    key_scores = key_search.search(
        keyword_query_text,
        top_k=payload.limit,
        filters=filters
    )

    # --- Step 4: Semantic search ---
    from online_team.rag.semantic_search import SemanticSearch
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
    from online_team.rag.reranker import PaperReranker
    reranker = PaperReranker(CROSS_ENCODER_MODEL)
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
async def search_papers(payload: PaperQuery):
    """Optimized search endpoint using parallel pipeline"""
    processed, raw_content, final_results = await retrieve_papers_optimized(payload)
    return {
        "original_query": payload.query,
        "rewritten_query": processed.rewritten_query,
        "keyword_query": processed.keyword_query,
        "gemini_filters": processed.search_filters,
        "raw_gemini_output": raw_content,
        "matched_count": len(final_results),
        "matched_papers": final_results,
        "pipeline_info": pipeline.get_pipeline_info(),
        "cache_stats": query_processor.get_cache_stats()
    }

@app.post("/top_papers")
async def top_papers(payload: PaperQuery):
    """Top papers endpoint: sort by final_score, pick highest-scoring evidence per paper,
    remove papers with negative score and log reason"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # --- Process query ---
    processed, raw_content = query_processor.process_query(payload.query)
    filters = convert_filters(processed.search_filters)

    # --- Generate embeddings ---
    query_embeddings = [
        model.encode(payload.query, normalize_embeddings=True).tolist(),
        model.encode(processed.rewritten_query or payload.query, normalize_embeddings=True).tolist()
    ]

    # --- Candidate window for retrieval/rerank ---
    candidate_top_k = max(payload.limit * 10, 200)
    candidate_top_final = max(payload.limit * 4, 200)

    final_results = await pipeline.search_with_reranking(
        query_text=processed.rewritten_query or payload.query,
        query_embedding=query_embeddings[0],
        filters=filters,
        top_k=candidate_top_k,
        top_final=candidate_top_final
    )

    # --- Aggregate chunks per paper ---
    papers_dict = {}
    for r in final_results:
        pid = r["paper_id"]
        evidence = r.get("evidence")
        title = r.get("title") or ""
        cross_score = r.get("cross_score", 0.0)
        final_score = r.get("final_score", 0.0)

        if pid not in papers_dict:
            papers_dict[pid] = {
                "paper_id": pid,
                "title": title,
                "best_evidence": evidence or "",
                "best_final_score": final_score,
                "best_cross_score": cross_score,
            }
        else:
            entry = papers_dict[pid]
            if final_score > entry["best_final_score"]:
                entry["best_final_score"] = final_score
                entry["best_cross_score"] = cross_score
                entry["best_evidence"] = evidence or ""

    # --- Convert dict to list and filter negative scores ---
    papers_list = []
    for entry in papers_dict.values():
        if entry["best_final_score"] < 0:
            logging.info(f"Skipping paper {entry['paper_id']} due to negative score: {entry['best_final_score']}")
            continue
        papers_list.append({
            "paper_id": entry["paper_id"],
            "title": entry["title"],
            "evidence": entry["best_evidence"],
            "final_score": entry["best_final_score"],
            "cross_score": entry["best_cross_score"],
        })

    # --- Sort papers by final_score descending ---
    top_papers = sorted(papers_list, key=lambda x: x["final_score"], reverse=True)[:payload.limit]

    return {
        "original_query": payload.query,
        "rewritten_query": processed.rewritten_query,
        "keyword_query": processed.keyword_query,
        "gemini_filters": processed.search_filters,
        "raw_gemini_output": raw_content,
        "matched_count": len(top_papers),
        "matched_papers": top_papers,
        "pipeline_info": pipeline.get_pipeline_info(),
        "cache_stats": query_processor.get_cache_stats()
    }


@app.post("/qa")
async def qa_endpoint(payload: QAQuery):
    """
    Optimized QA endpoint using parallel pipeline.
    This follows the flow diagram: Finding Paper -> QA pipeline -> Final answer
    """
    # Step 1: Use the optimized finding pipeline to get top-ranked passages
    processed, raw_content, final_results = await retrieve_papers_optimized(PaperQuery(query=payload.query, limit=payload.limit))
    
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
    
    # Step 3: Process through legacy QA pipeline
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
        },
        "pipeline_info": pipeline.get_pipeline_info(),
        "cache_stats": query_processor.get_cache_stats()
    }

@app.post("/scholarqa")
async def scholarqa_endpoint(payload: ScholarQAQuery):
    """
    Optimized ScholarQA endpoint following AllenAI best practices.
    
    Features:
    - Metadata and citations for each quote (paper_id, title, score)
    - Planning/clustering step to generate structured outline (Background, Methods, Results, Discussion, Open Questions)
    - Tabular comparison when multiple papers discuss the same dimension
    - Detailed processing trace at each step for debugging and reproducibility
    - Modular components (retriever, reranker, quote extraction, theme generation, report synthesis)
    - Structured JSON output with sections, quotes (with metadata), optional comparison tables, and narrative report
    """
    # Step 1: Use the optimized finding pipeline to get top-ranked passages
    processed, raw_content, final_results = await retrieve_papers_optimized(PaperQuery(query=payload.query, limit=payload.limit))
    
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
    
    # Step 3: Process through new ScholarQA pipeline
    scholarqa_result = process_scholarqa_pipeline(
        query=payload.query,
        ranked_passages=ranked_passages,
        model=payload.model,
        retrieval_top_k=payload.retrieval_top_k,
        rerank_top_k=payload.rerank_top_k
    )
    
    return {
        "original_query": payload.query,
        "rewritten_query": processed.rewritten_query,
        "keyword_query": processed.keyword_query,
        "gemini_filters": processed.search_filters,
        "raw_gemini_output": raw_content,
        "scholarqa_result": scholarqa_result,
        "finding_info": {
            "total_passages_found": len(final_results),
            "passages_used_for_qa": len(ranked_passages)
        },
        "pipeline_info": pipeline.get_pipeline_info(),
        "cache_stats": query_processor.get_cache_stats()
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok", 
        "message": "FindPaper QA Engine is running", 
        "version": "2.0.0", 
        "features": ["optimized_search", "legacy_qa", "scholarqa_pipeline"],
        "pipeline_info": pipeline.get_pipeline_info(),
        "cache_stats": query_processor.get_cache_stats()
    }

@app.get("/pipeline/config")
async def get_pipeline_config():
    """Get current pipeline configuration"""
    return {
        "pipeline_config": pipeline.get_pipeline_info(),
        "query_processor_config": query_processor.get_processor_info()
    }

@app.post("/pipeline/config")
async def update_pipeline_config(config_update: dict):
    """Update pipeline configuration (requires restart for some changes)"""
    # Note: This is a simplified version. Full reconfiguration would require restarting the pipeline
    return {
        "message": "Configuration update received. Some changes may require service restart.",
        "current_config": pipeline.get_pipeline_info(),
        "update_requested": config_update
    }

@app.post("/cache/clear")
async def clear_cache():
    """Clear query processing cache"""
    query_processor.clear_cache()
    return {
        "message": "Query processing cache cleared",
        "cache_stats": query_processor.get_cache_stats()
    }

@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    return {
        "cache_stats": query_processor.get_cache_stats()
    }

@app.post("/search_passsages/legacy")
def search_papers_legacy(payload: PaperQuery):
    """Legacy search endpoint for backward compatibility"""
    processed, raw_content, final_results = retrieve_papers_legacy(payload)
    return {
        "original_query": payload.query,
        "rewritten_query": processed.rewritten_query,
        "keyword_query": processed.keyword_query,
        "gemini_filters": processed.search_filters,
        "raw_gemini_output": raw_content,
        "matched_count": len(final_results),
        "matched_papers": final_results,
        "pipeline_type": "legacy"
    }

