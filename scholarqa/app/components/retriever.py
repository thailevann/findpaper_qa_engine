"""
Retriever component for finding relevant passages from papers.
"""
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class PassageRetriever:
    """Component responsible for retrieving relevant passages from papers."""
    
    def __init__(self, top_k: int = 50):
        self.top_k = top_k
    
    def retrieve_passages(self, query: str, ranked_passages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.info(f"Retrieving top {self.top_k} passages from {len(ranked_passages)} ranked passages")
        
        # Use heapq.nlargest for faster top-k selection
        import heapq
        retrieved = heapq.nlargest(self.top_k, ranked_passages, key=lambda x: x.get('final_score', 0))
        
        logger.info(f"Retrieved {len(retrieved)} passages")
        
        trace_info = {
            "step": "passage_retrieval",
            "query": query,
            "total_ranked_passages": len(ranked_passages),
            "retrieved_passages": len(retrieved),
            "top_scores": [p.get('final_score', 0) for p in retrieved[:5]]
        }
        logger.info(f"Retrieval trace: {trace_info}")
        
        return retrieved

