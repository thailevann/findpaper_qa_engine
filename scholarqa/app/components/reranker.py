"""
Reranker component for re-ranking retrieved passages.
"""
from typing import List, Dict, Any
import logging
import numpy as np
from numpy.linalg import norm

logger = logging.getLogger(__name__)


class PassageReranker:
    """Component responsible for re-ranking retrieved passages."""
    
    def __init__(self, top_k: int = 20):
        self.top_k = top_k
    
    def rerank_passages(self, query: str, passages: List[Dict[str, Any]], 
                       embeddings: List[List[float]]) -> List[Dict[str, Any]]:
        """
        Re-rank passages based on semantic similarity to query.
        
        Args:
            query: User query
            passages: List of passages with metadata
            embeddings: Embeddings for query and passages
            
        Returns:
            Re-ranked list of passages
        """
        logger.info(f"Re-ranking {len(passages)} passages")
        
        if not passages or embeddings is None or (hasattr(embeddings, '__len__') and len(embeddings) == 0):
            return passages
        
        # Calculate cosine similarities
        query_embedding = np.array(embeddings[0])
        passage_embeddings = np.array(embeddings[1:])
        
        # Normalize embeddings
        query_norm = query_embedding / np.clip(np.linalg.norm(query_embedding), 1e-12, None)
        passage_norms = passage_embeddings / np.clip(np.linalg.norm(passage_embeddings, axis=1, keepdims=True), 1e-12, None)
        
        # Calculate similarities
        similarities = np.dot(passage_norms, query_norm)
        
        # Create passage-score pairs and sort by similarity
        passage_scores = [(passages[i], float(similarities[i])) for i in range(len(passages))]
        passage_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Take top_k and add similarity scores
        reranked = []
        for passage, similarity in passage_scores[:self.top_k]:
            passage_copy = passage.copy()
            passage_copy['similarity_score'] = similarity
            reranked.append(passage_copy)
        
        logger.info(f"Re-ranked to {len(reranked)} passages")
        
        # Log processing trace
        trace_info = {
            "step": "passage_reranking",
            "query": query,
            "input_passages": len(passages),
            "output_passages": len(reranked),
            "top_similarities": [p['similarity_score'] for p in reranked[:5]]
        }
        logger.info(f"Reranking trace: {trace_info}")
        
        return reranked
