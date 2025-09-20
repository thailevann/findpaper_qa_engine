from elasticsearch import Elasticsearch
from typing import Dict, List, Optional
import asyncio
import concurrent.futures
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class SemanticSearchConfig:
    """Configuration for semantic search"""
    top_k: int = 50
    knn_num_candidates: int = 50
    vector_fields: Optional[List[str]] = None

    def __post_init__(self):
        if self.vector_fields is None:
            self.vector_fields = ["title_embedding", "abstract_embedding", "chunks.embedding"]


class SemanticSearch:
    """Semantic search using Elasticsearch KNN vectors with async support"""

    def __init__(
        self,
        es_url: str = "http://localhost:9200",
        index_name: str = "papers_vectors",
        config: Optional[SemanticSearchConfig] = None,
        max_workers: int = 8
    ):
        self.es = Elasticsearch(es_url, request_timeout=120)
        self.index_name = index_name
        self.config = config or SemanticSearchConfig()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def _apply_filters(self, filters: Optional[Dict[str, str]]) -> List[Dict]:
        """Build filter clauses"""
        clauses = []
        if not filters:
            return clauses
        for field, value in filters.items():
            if ":" in value:
                gte, lte = value.split(":")
                clauses.append({"range": {field: {"gte": gte, "lte": lte}}})
            else:
                clauses.append({"term": {field: value}})
        return clauses

    def _build_knn_query(self, field: str, query_embedding: List[float], top_k: int, filters: Optional[Dict[str, str]] = None):
        """Build KNN query for a single vector field"""
        knn_query = {
            "knn": {
                "field": field,
                "query_vector": query_embedding,
                "k": top_k,
                "num_candidates": self.config.knn_num_candidates
            }
        }
        filter_clauses = self._apply_filters(filters)
        if filter_clauses:
            knn_query["knn"]["filter"] = {"bool": {"must": filter_clauses}}
        return knn_query

    def _build_multi_field_knn_query(self, query_embedding: List[float], top_k: int, filters: Optional[Dict[str, str]] = None):
        """Build multi-field KNN query"""
        should_queries = [
            self._build_knn_query(field, query_embedding, top_k, filters)
            for field in self.config.vector_fields
        ]
        return {
            "bool": {
                "should": should_queries,
                "minimum_should_match": 1
            }
        }

    def search(
        self,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, str]] = None,
        use_multi_field: bool = True
    ) -> Dict[str, float]:
        """Perform semantic search"""
        top_k = top_k or self.config.top_k
        if use_multi_field and len(self.config.vector_fields) > 1:
            query = self._build_multi_field_knn_query(query_embedding, top_k, filters)
        else:
            query = self._build_knn_query(self.config.vector_fields[0], query_embedding, top_k, filters)

        body = {"size": top_k, "_source": ["paper_id"], "query": query}
        try:
            res = self.es.search(index=self.index_name, body=body)
            scores = {hit["_source"]["paper_id"]: hit["_score"] for hit in res["hits"]["hits"]}
            logger.info(f"Semantic search returned {len(scores)} results")
            return scores
        except Exception as e:
            logger.warning(f"KNN search failed, fallback to script_score: {e}")
            return self._fallback_script_score_search(query_embedding, top_k, filters)

    def _fallback_script_score_search(
        self,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """Fallback search using script_score"""
        filter_clauses = self._apply_filters(filters)
        base_query = {"bool": {"must": filter_clauses}} if filter_clauses else {"match_all": {}}

        body = {
            "size": top_k,
            "_source": ["paper_id"],
            "query": {
                "script_score": {
                    "query": base_query,
                    "script": {
                        "source": """
                            double maxScore = 0;
                            if (doc['title_embedding'].size() != 0) {
                                double score = cosineSimilarity(params.qvec, 'title_embedding');
                                if (score > maxScore) maxScore = score;
                            }
                            if (doc['abstract_embedding'].size() != 0) {
                                double score = cosineSimilarity(params.qvec, 'abstract_embedding');
                                if (score > maxScore) maxScore = score;
                            }
                            if (doc['chunks.embedding'].size() != 0) {
                                for (int i=0; i<doc['chunks.embedding'].size(); i++) {
                                    double score = cosineSimilarity(params.qvec, doc['chunks.embedding'][i]);
                                    if (score > maxScore) maxScore = score;
                                }
                            }
                            return maxScore;
                        """,
                        "params": {"qvec": query_embedding}
                    }
                }
            }
        }

        res = self.es.search(index=self.index_name, body=body)
        scores = {hit["_source"]["paper_id"]: hit["_score"] for hit in res["hits"]["hits"]}
        return scores

    async def search_async(
        self,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, str]] = None,
        use_multi_field: bool = True
    ) -> Dict[str, float]:
        """Async semantic search using executor"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.search,
            query_embedding,
            top_k,
            filters,
            use_multi_field
        )
