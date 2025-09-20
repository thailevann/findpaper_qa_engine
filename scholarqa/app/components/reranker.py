"""
Reranker component for re-ranking retrieved passages.
"""
from typing import List, Dict, Any
import logging
import numpy as np
import heapq

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
            embeddings: Embeddings for query and passages (query first)

        Returns:
            Re-ranked list of passages
        """
        logger.info(f"Re-ranking {len(passages)} passages")

        # Validate embeddings
        if not passages or embeddings is None or len(embeddings) < 2:
            return passages

        query_emb = np.array(embeddings[0], dtype=np.float32)
        passage_embs = np.array(embeddings[1:], dtype=np.float32)

        if query_emb.size == 0 or passage_embs.size == 0:
            return passages

        # Normalize embeddings (vectorized)
        query_emb /= np.linalg.norm(query_emb) + 1e-12
        passage_embs /= np.linalg.norm(passage_embs, axis=1, keepdims=True) + 1e-12

        # Cosine similarity
        similarities = passage_embs @ query_emb  # shape: (num_passages,)

        # Get top-k efficiently
        top_k = min(self.top_k, len(passages))
        top_indices = heapq.nlargest(top_k, range(len(similarities)), key=lambda i: similarities[i])

        reranked = []
        for i in top_indices:
            p = passages[i].copy()
            p['similarity_score'] = float(similarities[i])
            reranked.append(p)

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
