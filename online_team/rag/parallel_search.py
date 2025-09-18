"""
Parallel search orchestrator for combining keyword and semantic search
"""
import asyncio
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import time

from .keyword_search import KeywordSearch, KeywordSearchConfig
from .semantic_search import SemanticSearch, SemanticSearchConfig
from .reranker import PaperReranker, RerankerConfig


@dataclass
class SearchPipelineConfig:
    """Configuration for the entire search pipeline"""
    # Search configs
    keyword_config: Optional[KeywordSearchConfig] = None
    semantic_config: Optional[SemanticSearchConfig] = None
    reranker_config: Optional[RerankerConfig] = None
    
    # Pipeline settings
    use_parallel_search: bool = True
    use_multi_field_semantic: bool = True
    enable_reranking: bool = True
    
    # Performance settings
    search_timeout: float = 30.0  # seconds
    rerank_timeout: float = 60.0  # seconds


class ParallelSearchPipeline:
    """
    Orchestrates parallel keyword and semantic search with optional reranking
    """
    
    def __init__(
        self,
        es_url: str = "http://localhost:9200",
        text_index: str = "papers_text",
        vector_index: str = "papers_vectors",
        config: Optional[SearchPipelineConfig] = None
    ):
        self.config = config or SearchPipelineConfig()
        
        # Initialize search components
        self.keyword_search = KeywordSearch(
            es_url=es_url,
            index_name=text_index,
            config=self.config.keyword_config
        )
        
        self.semantic_search = SemanticSearch(
            es_url=es_url,
            index_name=vector_index,
            config=self.config.semantic_config
        )
        
        self.reranker = PaperReranker(
            es_url=es_url,
            index_name=text_index,
            config=self.config.reranker_config
        ) if self.config.enable_reranking else None

    async def search_parallel(
        self,
        query_text: str,
        query_embeddings: List[List[float]],
        filters: Optional[Dict[str, str]] = None,
        top_k: Optional[int] = None
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Run keyword and semantic search in parallel
        
        Returns:
            Tuple of (keyword_scores, semantic_scores)
        """
        if not self.config.use_parallel_search:
            # Sequential execution
            key_scores = self.keyword_search.search(query_text, top_k, filters)
            sem_scores = self.semantic_search.search(
                query_embeddings[0], top_k, filters, 
                self.config.use_multi_field_semantic
            )
            return key_scores, sem_scores
        
        # Parallel execution
        try:
            # Run both searches concurrently
            key_task = self.keyword_search.search_async(query_text, top_k, filters)
            sem_task = self.semantic_search.search_async(
                query_embeddings[0], top_k, filters,
                self.config.use_multi_field_semantic
            )
            
            # Wait for both with timeout
            key_scores, sem_scores = await asyncio.wait_for(
                asyncio.gather(key_task, sem_task),
                timeout=self.config.search_timeout
            )
            
            return key_scores, sem_scores
            
        except asyncio.TimeoutError:
            print(f"Search timeout after {self.config.search_timeout}s")
            # Fallback to sequential
            key_scores = self.keyword_search.search(query_text, top_k, filters)
            sem_scores = self.semantic_search.search(
                query_embeddings[0], top_k, filters,
                self.config.use_multi_field_semantic
            )
            return key_scores, sem_scores
        except Exception as e:
            print(f"Error in parallel search: {e}")
            # Fallback to sequential
            key_scores = self.keyword_search.search(query_text, top_k, filters)
            sem_scores = self.semantic_search.search(
                query_embeddings[0], top_k, filters,
                self.config.use_multi_field_semantic
            )
            return key_scores, sem_scores

    async def search_with_reranking(
        self,
        query_text: str,
        query_embeddings: List[List[float]],
        filters: Optional[Dict[str, str]] = None,
        top_k: Optional[int] = None,
        top_final: Optional[int] = None
    ) -> List[Dict[str, Union[str, float]]]:
        """
        Complete search pipeline with parallel search and optional reranking
        
        Returns:
            List of ranked results
        """
        start_time = time.time()
        
        # Step 1: Parallel search
        print("Running parallel keyword and semantic search...")
        key_scores, sem_scores = await self.search_parallel(
            query_text, query_embeddings, filters, top_k
        )
        
        search_time = time.time() - start_time
        print(f"Search completed in {search_time:.2f}s")
        print(f"Found {len(key_scores)} keyword results, {len(sem_scores)} semantic results")
        
        # Step 2: Reranking (if enabled)
        if self.reranker and self.config.enable_reranking:
            print("Running reranking...")
            rerank_start = time.time()
            
            try:
                results = await asyncio.wait_for(
                    self.reranker.rerank_async(
                        query_text=query_text,
                        query_embeddings=query_embeddings,
                        sem_scores=sem_scores,
                        key_scores=key_scores,
                        vector_index_name=self.semantic_search.index_name,
                        top_final=top_final
                    ),
                    timeout=self.config.rerank_timeout
                )
                
                rerank_time = time.time() - rerank_start
                print(f"Reranking completed in {rerank_time:.2f}s")
                
            except asyncio.TimeoutError:
                print(f"Reranking timeout after {self.config.rerank_timeout}s")
                # Fallback to simple hybrid scoring
                results = self._simple_hybrid_ranking(
                    key_scores, sem_scores, top_final or 20
                )
        else:
            # Simple hybrid ranking without CrossEncoder
            print("Using simple hybrid ranking...")
            results = self._simple_hybrid_ranking(
                key_scores, sem_scores, top_final or 20
            )
        
        total_time = time.time() - start_time
        print(f"Total pipeline time: {total_time:.2f}s")
        
        return results

    def _simple_hybrid_ranking(
        self,
        key_scores: Dict[str, float],
        sem_scores: Dict[str, float],
        top_final: int
    ) -> List[Dict[str, Union[str, float]]]:
        """Simple hybrid ranking without CrossEncoder"""
        # Normalize scores
        max_key = max(key_scores.values()) if key_scores else 1
        max_sem = max(sem_scores.values()) if sem_scores else 1
        
        combined_scores = {}
        all_ids = set(key_scores.keys()) | set(sem_scores.keys())
        
        for pid in all_ids:
            key_score = key_scores.get(pid, 0) / max_key
            sem_score = sem_scores.get(pid, 0) / max_sem
            combined_scores[pid] = key_score + sem_score
        
        # Sort and get top results
        ranked = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for pid, score in ranked[:top_final]:
            try:
                doc_text = self.keyword_search.es.get(
                    index=self.keyword_search.index_name, id=pid
                )["_source"]
                title = doc_text.get("title", "")
                abstract = doc_text.get("abstract", "")
            except:
                title, abstract = "", ""
            
            results.append({
                "paper_id": pid,
                "title": title,
                "score": score,
                "evidence": abstract,
                "cross_score": 0.0,
                "final_score": score
            })
        
        return results

    def get_pipeline_info(self) -> Dict[str, Union[str, bool, int, float]]:
        """Get information about the current pipeline configuration"""
        info = {
            "use_parallel_search": self.config.use_parallel_search,
            "use_multi_field_semantic": self.config.use_multi_field_semantic,
            "enable_reranking": self.config.enable_reranking,
            "search_timeout": self.config.search_timeout,
            "rerank_timeout": self.config.rerank_timeout,
            "text_index": self.keyword_search.index_name,
            "vector_index": self.semantic_search.index_name
        }
        
        if self.reranker:
            info.update(self.reranker.get_reranker_info())
        
        return info


