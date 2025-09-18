from elasticsearch import Elasticsearch
import numpy as np
from typing import Dict, List, Optional, Union
import asyncio
import concurrent.futures
from dataclasses import dataclass


@dataclass
class SemanticSearchConfig:
    """Configuration for semantic search"""
    top_k: int = 50
    knn_num_candidates: int = 100
    vector_fields: List[str] = None
    
    def __post_init__(self):
        if self.vector_fields is None:
            self.vector_fields = ["title_embedding", "abstract_embedding", "chunks.embedding"]


class SemanticSearch:
    def __init__(
        self, 
        es_url: str = "http://localhost:9200", 
        index_name: str = "papers_vectors",
        config: Optional[SemanticSearchConfig] = None
    ):
        self.es = Elasticsearch(es_url, request_timeout=120)
        self.index_name = index_name
        self.config = config or SemanticSearchConfig()
        
    def _build_knn_query(
        self, 
        query_embedding: List[float], 
        top_k: int,
        filters: Optional[Dict[str, str]] = None
    ) -> Dict:
        """Build Elasticsearch knn query for dense vector search"""
        
        # Base knn query
        knn_query = {
            "knn": {
                "field": "title_embedding",  # Primary field for knn
                "query_vector": query_embedding,
                "k": top_k,
                "num_candidates": self.config.knn_num_candidates
            }
        }
        
        # Add filters if provided
        if filters:
            filter_clauses = []
            for field, value in filters.items():
                if ":" in value:
                    gte, lte = value.split(":")
                    filter_clauses.append({"range": {field: {"gte": gte, "lte": lte}}})
                else:
                    filter_clauses.append({"term": {field: value}})
            
            knn_query["knn"]["filter"] = {"bool": {"must": filter_clauses}}
        
        return knn_query
    
    def _build_multi_field_knn_query(
        self, 
        query_embedding: List[float], 
        top_k: int,
        filters: Optional[Dict[str, str]] = None
    ) -> Dict:
        """Build multi-field knn query for better coverage"""
        
        # Create multiple knn queries for different vector fields
        knn_queries = []
        
        for field in self.config.vector_fields:
            knn_query = {
                "knn": {
                    "field": field,
                    "query_vector": query_embedding,
                    "k": top_k,
                    "num_candidates": self.config.knn_num_candidates
                }
            }
            
            # Add filters if provided
            if filters:
                filter_clauses = []
                for field_name, value in filters.items():
                    if ":" in value:
                        gte, lte = value.split(":")
                        filter_clauses.append({"range": {field_name: {"gte": gte, "lte": lte}}})
                    else:
                        filter_clauses.append({"term": {field_name: value}})
                
                knn_query["knn"]["filter"] = {"bool": {"must": filter_clauses}}
            
            knn_queries.append(knn_query)
        
        # Combine with should clause for multi-field search
        return {
            "bool": {
                "should": knn_queries,
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
        """
        Perform semantic search using Elasticsearch knn
        
        Args:
            query_embedding: Query vector for similarity search
            top_k: Number of results to return
            filters: Optional filters (year, venue, etc.)
            use_multi_field: Whether to search across multiple vector fields
            
        Returns:
            Dict mapping paper_id to similarity score
        """
        top_k = top_k or self.config.top_k
        
        # Choose query strategy
        if use_multi_field and len(self.config.vector_fields) > 1:
            query = self._build_multi_field_knn_query(query_embedding, top_k, filters)
        else:
            query = self._build_knn_query(query_embedding, top_k, filters)
        
        body = {
            "size": top_k,
            "_source": ["paper_id"],
            "query": query
        }
        
        try:
            res = self.es.search(index=self.index_name, body=body)
            scores = {hit["_source"]["paper_id"]: hit["_score"] for hit in res["hits"]["hits"]}
            return scores
        except Exception as e:
            print(f"Error in semantic search: {e}")
            # Fallback to script_score if knn fails
            return self._fallback_script_score_search(query_embedding, top_k, filters)
    
    def _fallback_script_score_search(
        self, 
        query_embedding: List[float], 
        top_k: int, 
        filters: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """Fallback to script_score search if knn fails"""
        
        # Base query: match all
        base_query = {"match_all": {}}
        
        # Apply filters
        if filters:
            must_clauses = []
            for field, value in filters.items():
                if ":" in value:
                    gte, lte = value.split(":")
                    must_clauses.append({"range": {field: {"gte": gte, "lte": lte}}})
                else:
                    must_clauses.append({"term": {field: value}})
            base_query = {"bool": {"must": must_clauses}}
        
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
        """Async version of search for parallel execution"""
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor, 
                self.search, 
                query_embedding, 
                top_k, 
                filters, 
                use_multi_field
            )