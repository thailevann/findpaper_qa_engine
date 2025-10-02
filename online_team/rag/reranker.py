import logging
import numpy as np
from sentence_transformers import CrossEncoder
from elasticsearch import Elasticsearch
from typing import List, Dict, Union, Optional
from dataclasses import dataclass
from config import CROSS_ENCODER_MODEL
import asyncio

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@dataclass
class RerankerConfig:
    top_final: int = 20
    crossencoder_model: str = None
    batch_size: int = 64
    use_distil: bool = False
    use_crossencoder: bool = True
    max_candidates_for_rerank: int = 200  

class PaperReranker:
    def __init__(self, 
                 es_url: str = "http://localhost:9200",
                 index_name: str = "papers_text",
                 config: Optional[RerankerConfig] = None):
        self.config = config or RerankerConfig()
        self.batch_size = self.config.batch_size
        self.es = Elasticsearch(es_url, request_timeout=120)
        self.index_name = index_name
        
        # Init CrossEncoder
        model_name = self.config.crossencoder_model or CROSS_ENCODER_MODEL
        if self.config.use_distil and "distil" not in model_name.lower():
            model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
        self.ce_model = CrossEncoder(model_name)
        logger.info(f"Loaded CrossEncoder: {model_name}")

    def _get_best_chunk(self, chunks: List[dict]) -> str:
        for ch in chunks:
            if isinstance(ch, dict) and "text" in ch:
                return ch["text"]
            elif isinstance(ch, str):
                return ch
        return ""

    def rerank(self, query_text: str, candidate_results: List[dict], top_final: Optional[int] = None):
        """
        Rerank merged search results (not just IDs).
        candidate_results should be a list of dicts with structure:
        [{"paper_id": str, "field": str, "text": str, "evidence": str, ...}, ...]
        """
        top_final = top_final or self.config.top_final
        if not candidate_results:
            logger.info("No candidate papers to rerank.")
            return []
    
        logger.info(f"Number of candidate results before rerank: {len(candidate_results)}")
        
        # Extract unique paper IDs for fetching additional data
        unique_paper_ids = list(set(r.get("paper_id") for r in candidate_results if r.get("paper_id")))
        
        # Fetch paper metadata if needed (for title, abstract, chunks)
        paper_data = {}
        if unique_paper_ids:
            try:
                res = self.es.mget(index=self.index_name, ids=unique_paper_ids)
                paper_data = {doc["_id"]: doc.get("_source", {}) for doc in res["docs"] if doc.get("found", False)}
            except Exception as e:
                logger.warning(f"Failed to fetch paper data from ES: {e}")

        # Prepare results for reranking
        results = []
        for result in candidate_results:
            paper_id = result.get("paper_id")
            
            # Use evidence from the merged result, fallback to text, then to paper data
            evidence = result.get("evidence", "")
            if not evidence:
                evidence = result.get("text", "")
            
            # If still no evidence, try to get from paper data
            if not evidence and paper_id in paper_data:
                paper = paper_data[paper_id]
                chunks = paper.get("chunks", [])
                evidence = self._get_best_chunk(chunks) or paper.get("abstract", "")
            
            if not evidence.strip():
                logger.warning(f"Skipping result with empty evidence for paper_id={paper_id}")
                continue
                
            # Prepare result for reranking
            rerank_result = {
                "paper_id": paper_id,
                "title": paper_data.get(paper_id, {}).get("title", result.get("title", "")),
                "evidence": evidence,
                "field": result.get("field", ""),
                "original_result": result  # Keep original for reference
            }
            results.append(rerank_result)

        if not results:
            logger.warning("No valid results to rerank after filtering")
            return []

        # Calculate CrossEncoder scores in batches
        pairs = [(query_text, r["evidence"]) for r in results]
        ce_scores = []
        
        try:
            for i in range(0, len(pairs), self.batch_size):
                batch = pairs[i:i+self.batch_size]
                batch_scores = self.ce_model.predict(batch).tolist()
                ce_scores.extend(batch_scores)
        except Exception as e:
            logger.error(f"CrossEncoder prediction failed: {e}")
            # Fallback: return original results without reranking
            return candidate_results[:top_final]

        # Assign scores and sort
        for r, score in zip(results, ce_scores):
            r["cross_score"] = float(score)
            r["final_score"] = float(score)

        results.sort(key=lambda x: x["final_score"], reverse=True)
        final_results = results[:top_final]
        
        logger.info(f"Number of papers after rerank): {len(final_results)}")
        
        # Return results in the expected format
        output_results = []
        for r in final_results:
            output_result = r["original_result"].copy()  # Start with original result
            output_result.update({
                "cross_score": r["cross_score"],
                "final_score": r["final_score"],
                "title": r["title"]  # Add title if not present
            })
            output_results.append(output_result)
            
        return output_results
    
    async def rerank_async(self, query_text: str, candidate_results: List[dict], top_final: Optional[int] = None):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.rerank, query_text, candidate_results, top_final)

    def get_reranker_info(self) -> dict:
        """Return current reranker configuration"""
        return {
            "use_crossencoder": self.config.use_crossencoder,
            "crossencoder_model": self.config.crossencoder_model,
            "use_distil": self.config.use_distil,
            "top_final": self.config.top_final,
            "batch_size": self.config.batch_size
        }