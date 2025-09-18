import numpy as np
from sentence_transformers import CrossEncoder
from elasticsearch import Elasticsearch
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import asyncio
import concurrent.futures
from config import CROSS_ENCODER_MODEL


@dataclass
class RerankerConfig:
    """Configuration for paper reranker"""
    top_final: int = 20
    alpha: float = 1.0  # Weight for semantic scores
    beta: float = 1.0   # Weight for keyword scores
    use_crossencoder: bool = True
    crossencoder_model: str = None
    batch_size: int = 32
    use_distil: bool = False  # Use smaller DistilCrossEncoder for speed


class PaperReranker:
    def __init__(
        self, 
        es_url: str = "http://localhost:9200",
        index_name: str = "papers_text",
        config: Optional[RerankerConfig] = None
    ):
        self.config = config or RerankerConfig()
        self.es_text = Elasticsearch(es_url, request_timeout=120)
        self.index_name = index_name
        
        # Initialize CrossEncoder if enabled
        self.ce_model = None
        if self.config.use_crossencoder:
            model_name = self.config.crossencoder_model or CROSS_ENCODER_MODEL
            if self.config.use_distil and "distil" not in model_name.lower():
                # Use a smaller DistilCrossEncoder for faster inference
                model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
            
            try:
                self.ce_model = CrossEncoder(model_name)
                print(f"Loaded CrossEncoder: {model_name}")
            except Exception as e:
                print(f"Failed to load CrossEncoder: {e}")
                print("Falling back to hybrid scoring only")
                self.ce_model = None
                self.config.use_crossencoder = False

    def find_best_chunk_mean(
        self, 
        pid: str, 
        query_embeddings: List[List[float]], 
        vector_index_name: str
    ) -> Tuple[Optional[str], float]:
        """
        Find the best chunk for a paper based on semantic similarity
        
        Args:
            pid: Paper ID
            query_embeddings: List of query embeddings
            vector_index_name: Name of the vector index
            
        Returns:
            Tuple of (best_chunk_text, best_score)
        """
        try:
            vec_doc = self.es_text.get(index=vector_index_name, id=pid)["_source"]
        except:
            return None, 0.0

        chunks_vec = vec_doc.get("chunks", [])
        if not chunks_vec:
            return None, 0.0

        best_score = -1
        best_chunk_id = None
        
        for chunk in chunks_vec:
            emb = chunk.get("embedding")
            if not emb:
                continue
                
            emb = np.array(emb, dtype=np.float32)
            scores = []
            
            for qvec in query_embeddings:
                qvec = np.array(qvec, dtype=np.float32)
                # Cosine similarity
                score = np.dot(qvec, emb) / (np.linalg.norm(qvec) * np.linalg.norm(emb) + 1e-8)
                scores.append(score)
            
            mean_score = np.mean(scores)
            if mean_score > best_score:
                best_score = mean_score
                best_chunk_id = chunk.get("chunk_id")

        # Find the best chunk text
        for chunk in chunks_vec:
            if chunk.get("chunk_id") == best_chunk_id:
                return chunk.get("text"), best_score

        return None, best_score

    def _normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Normalize scores to [0, 1] range"""
        if not scores:
            return {}
        
        max_score = max(scores.values())
        if max_score == 0:
            return scores
            
        return {pid: score / max_score for pid, score in scores.items()}

    def _combine_scores(
        self, 
        sem_scores: Dict[str, float], 
        key_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Combine semantic and keyword scores with weights"""
        # Normalize scores
        norm_sem = self._normalize_scores(sem_scores)
        norm_key = self._normalize_scores(key_scores)
        
        final_scores = {}
        all_ids = set(norm_sem.keys()) | set(norm_key.keys())
        
        for pid in all_ids:
            sem_score = norm_sem.get(pid, 0)
            key_score = norm_key.get(pid, 0)
            final_scores[pid] = self.config.alpha * sem_score + self.config.beta * key_score
        
        return final_scores

    def _batch_crossencoder_predict(
        self, 
        pairs: List[Tuple[str, str]]
    ) -> List[float]:
        """Batch CrossEncoder prediction for efficiency"""
        if not self.ce_model or not pairs:
            return [0.0] * len(pairs)
        
        try:
            # Process in batches
            all_scores = []
            for i in range(0, len(pairs), self.config.batch_size):
                batch = pairs[i:i + self.config.batch_size]
                batch_scores = self.ce_model.predict(batch)
                all_scores.extend(batch_scores.tolist())
            
            return all_scores
        except Exception as e:
            print(f"Error in CrossEncoder prediction: {e}")
            return [0.0] * len(pairs)

    def rerank(
        self, 
        query_text: str, 
        query_embeddings: List[List[float]],
        sem_scores: Dict[str, float], 
        key_scores: Dict[str, float],
        vector_index_name: str,
        top_final: Optional[int] = None,
        alpha: Optional[float] = None,
        beta: Optional[float] = None
    ) -> List[Dict[str, Union[str, float]]]:
        """
        Rerank papers based on semantic + keyword scores, optionally with CrossEncoder
        
        Args:
            query_text: Original query text
            query_embeddings: List of query embeddings
            sem_scores: Semantic similarity scores
            key_scores: Keyword search scores
            vector_index_name: Name of the vector index
            top_final: Number of final results to return
            alpha: Weight for semantic scores
            beta: Weight for keyword scores
            
        Returns:
            List of ranked results with paper info and scores
        """
        # Use config values if not provided
        top_final = top_final or self.config.top_final
        if alpha is not None:
            self.config.alpha = alpha
        if beta is not None:
            self.config.beta = beta
        
        # Combine scores
        final_scores = self._combine_scores(sem_scores, key_scores)
        
        # Sort by combined score
        ranked = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Take top candidates for reranking
        top_candidates = ranked[:top_final * 2]  # Get more candidates for better reranking
        
        results = []
        for pid, score in top_candidates:
            try:
                doc_text = self.es_text.get(index=self.index_name, id=pid)["_source"]
                title = doc_text.get("title", "")
                abstract = doc_text.get("abstract", "")
            except:
                title, abstract = "", ""

            # Get best chunk as evidence
            best_chunk, sem_score = self.find_best_chunk_mean(
                pid, query_embeddings, vector_index_name
            )
            evidence = best_chunk or abstract

            results.append({
                "paper_id": pid,
                "title": title,
                "score": score,
                "evidence": evidence,
                "semantic_score": sem_score
            })

        # Apply CrossEncoder reranking if enabled
        if self.config.use_crossencoder and self.ce_model and results:
            pairs = [(query_text, r["evidence"]) for r in results]
            ce_scores = self._batch_crossencoder_predict(pairs)
            
            for result, ce_score in zip(results, ce_scores):
                result["cross_score"] = float(ce_score)
                result["final_score"] = result["score"] + result["cross_score"]
        else:
            # Use hybrid score as final score
            for result in results:
                result["cross_score"] = 0.0
                result["final_score"] = result["score"]

        # Sort by final score and return top results
        final_results = sorted(results, key=lambda x: x["final_score"], reverse=True)
        return final_results[:top_final]

    async def rerank_async(
        self, 
        query_text: str, 
        query_embeddings: List[List[float]],
        sem_scores: Dict[str, float], 
        key_scores: Dict[str, float],
        vector_index_name: str,
        top_final: Optional[int] = None,
        alpha: Optional[float] = None,
        beta: Optional[float] = None
    ) -> List[Dict[str, Union[str, float]]]:
        """Async version of rerank for parallel execution"""
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor,
                self.rerank,
                query_text,
                query_embeddings,
                sem_scores,
                key_scores,
                vector_index_name,
                top_final,
                alpha,
                beta
            )

    def get_reranker_info(self) -> Dict[str, Union[str, bool, int]]:
        """Get information about the current reranker configuration"""
        return {
            "use_crossencoder": self.config.use_crossencoder,
            "crossencoder_model": self.config.crossencoder_model or "None",
            "use_distil": self.config.use_distil,
            "top_final": self.config.top_final,
            "alpha": self.config.alpha,
            "beta": self.config.beta,
            "batch_size": self.config.batch_size
        }