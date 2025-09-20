import asyncio
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import time
import logging

from .keyword_search import KeywordSearch, KeywordSearchConfig
from .semantic_search import SemanticSearch, SemanticSearchConfig
from .reranker import PaperReranker, RerankerConfig

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@dataclass
class SearchPipelineConfig:
    keyword_config: Optional[KeywordSearchConfig] = None
    semantic_config: Optional[SemanticSearchConfig] = None
    reranker_config: Optional[RerankerConfig] = None
    use_parallel_search: bool = True
    use_multi_field_semantic: bool = True
    enable_reranking: bool = True
    search_timeout: float = 30.0
    rerank_timeout: float = 60.0

class ParallelSearchPipeline:
    def __init__(
        self,
        es_url: str = "http://localhost:9200",
        text_index: str = "papers_text",
        vector_index: str = "papers_vectors",
        config: Optional[SearchPipelineConfig] = None
    ):
        self.config = config or SearchPipelineConfig()
        self.keyword_search = KeywordSearch(es_url, text_index, self.config.keyword_config)
        self.semantic_search = SemanticSearch(es_url, vector_index, self.config.semantic_config)
        self.reranker = PaperReranker(es_url, text_index, self.config.reranker_config) \
                        if self.config.enable_reranking else None

    async def _sequential_search(self, query_text, query_embeddings, filters, top_k):
        key_scores = self.keyword_search.search(query_text, top_k, filters)
        sem_scores = self.semantic_search.search(query_embeddings[0], top_k, filters, self.config.use_multi_field_semantic)
        return key_scores, sem_scores

    async def search_parallel(
        self,
        query_text: str,
        query_embeddings: List[List[float]],
        filters: Optional[Dict[str, str]] = None,
        top_k: Optional[int] = None
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        if not self.config.use_parallel_search:
            return await self._sequential_search(query_text, query_embeddings, filters, top_k)
        try:
            key_task = self.keyword_search.search_async(query_text, top_k, filters)
            sem_task = self.semantic_search.search_async(query_embeddings[0], top_k, filters, self.config.use_multi_field_semantic)
            return await asyncio.wait_for(asyncio.gather(key_task, sem_task), timeout=self.config.search_timeout)
        except Exception as e:
            logger.warning(f"Parallel search failed ({e}), falling back to sequential")
            return await self._sequential_search(query_text, query_embeddings, filters, top_k)

    async def search_with_reranking(
        self,
        query_text: str,
        query_embeddings: List[List[float]],
        filters: Optional[Dict[str, str]] = None,
        top_k: Optional[int] = None,
        top_final: Optional[int] = None
    ) -> List[Dict[str, Union[str, float]]]:
        start_time = time.time()
        logger.info("Running parallel keyword and semantic search...")
        key_scores, sem_scores = await self.search_parallel(query_text, query_embeddings, filters, top_k)
        logger.info(f"Search completed in {time.time()-start_time:.2f}s | {len(key_scores)} keyword, {len(sem_scores)} semantic results")

        if self.reranker and self.config.enable_reranking:
            logger.info("Running reranking...")
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
                logger.info(f"Reranking completed in {time.time()-start_time:.2f}s")
            except asyncio.TimeoutError:
                logger.warning(f"Reranking timeout ({self.config.rerank_timeout}s), using simple hybrid ranking")
                results = self._simple_hybrid_ranking(key_scores, sem_scores, top_final or 20)
        else:
            results = self._simple_hybrid_ranking(key_scores, sem_scores, top_final or 20)

        logger.info(f"Total pipeline time: {time.time()-start_time:.2f}s")
        return results

    def _simple_hybrid_ranking(
        self,
        key_scores: Dict[str, float],
        sem_scores: Dict[str, float],
        top_final: int
    ) -> List[Dict[str, Union[str, float]]]:
        max_key, max_sem = max(key_scores.values(), default=1), max(sem_scores.values(), default=1)
        combined_scores = {pid: key_scores.get(pid,0)/max_key + sem_scores.get(pid,0)/max_sem
                           for pid in set(key_scores)|set(sem_scores)}
        ranked = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        results = []
        for pid, score in ranked[:top_final]:
            try:
                doc = self.keyword_search.es.get(index=self.keyword_search.index_name, id=pid)["_source"]
                title, abstract = doc.get("title",""), doc.get("abstract","")
            except:
                title, abstract = "", ""
            results.append({"paper_id": pid, "title": title, "score": score, "evidence": abstract, "cross_score": 0.0, "final_score": score})
        return results

    def get_pipeline_info(self) -> Dict[str, Union[str, bool, int, float]]:
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
