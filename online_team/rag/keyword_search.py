from elasticsearch import Elasticsearch
from typing import Dict, Optional
import asyncio
import concurrent.futures
from dataclasses import dataclass


@dataclass
class KeywordSearchConfig:
    """Configuration for keyword search"""
    top_k: int = 50
    title_boost: float = 5.0
    abstract_boost: float = 3.0
    multi_match_boost: float = 2.0


class KeywordSearch:
    def __init__(
        self, 
        es_url: str = "http://localhost:9200", 
        index_name: str = "papers_text",
        config: Optional[KeywordSearchConfig] = None
    ):
        self.es = Elasticsearch(es_url, request_timeout=120)
        self.index_name = index_name
        self.config = config or KeywordSearchConfig()

    def search(
        self, 
        query_text: str, 
        top_k: Optional[int] = None, 
        filters: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """
        Perform keyword search using match_phrase and multi_match
        
        Args:
            query_text: Text query for keyword search
            top_k: Number of results to return
            filters: Optional filters (year, venue, etc.)
            
        Returns:
            Dict mapping paper_id to normalized score (0-1)
        """
        top_k = top_k or self.config.top_k
        
        body = {
            "size": top_k,
            "_source": ["paper_id", "title", "abstract"],
            "query": {
                "bool": {
                    "must": [],
                    "should": [
                        {
                            "match_phrase": {
                                "title": {
                                    "query": query_text, 
                                    "boost": self.config.title_boost
                                }
                            }
                        },
                        {
                            "match_phrase": {
                                "abstract": {
                                    "query": query_text, 
                                    "boost": self.config.abstract_boost
                                }
                            }
                        },
                        {
                            "multi_match": {
                                "query": query_text, 
                                "fields": ["title^2", "abstract"], 
                                "type": "best_fields",
                                "boost": self.config.multi_match_boost
                            }
                        }
                    ]
                }
            }
        }

        # Apply filters
        if filters:
            for field, value in filters.items():
                if ":" in value:
                    gte, lte = value.split(":")
                    body["query"]["bool"]["must"].append({
                        "range": {field: {"gte": gte, "lte": lte}}
                    })
                else:
                    body["query"]["bool"]["must"].append({
                        "term": {field: value}
                    })

        try:
            res = self.es.search(index=self.index_name, body=body)
            scores = {}

            raw_scores = [hit["_score"] for hit in res["hits"]["hits"]]
            max_score = max(raw_scores) if raw_scores else 1  # Avoid division by zero

            for hit in res["hits"]["hits"]:
                pid = hit["_source"]["paper_id"]
                scores[pid] = hit["_score"] / max_score  # Normalize to 0-1

            return scores
        except Exception as e:
            print(f"Error in keyword search: {e}")
            return {}

    async def search_async(
        self, 
        query_text: str, 
        top_k: Optional[int] = None, 
        filters: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """Async version of search for parallel execution"""
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor, 
                self.search, 
                query_text, 
                top_k, 
                filters
            )

    def search_with_highlight(
        self, 
        query_text: str, 
        top_k: Optional[int] = None, 
        filters: Optional[Dict[str, str]] = None
    ) -> Dict[str, Dict]:
        """
        Perform keyword search with highlighting
        
        Returns:
            Dict mapping paper_id to dict with score and highlights
        """
        top_k = top_k or self.config.top_k
        
        body = {
            "size": top_k,
            "_source": ["paper_id", "title", "abstract"],
            "query": {
                "bool": {
                    "must": [],
                    "should": [
                        {
                            "match_phrase": {
                                "title": {
                                    "query": query_text, 
                                    "boost": self.config.title_boost
                                }
                            }
                        },
                        {
                            "match_phrase": {
                                "abstract": {
                                    "query": query_text, 
                                    "boost": self.config.abstract_boost
                                }
                            }
                        },
                        {
                            "multi_match": {
                                "query": query_text, 
                                "fields": ["title^2", "abstract"], 
                                "type": "best_fields",
                                "boost": self.config.multi_match_boost
                            }
                        }
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "title": {"fragment_size": 150, "number_of_fragments": 1},
                    "abstract": {"fragment_size": 200, "number_of_fragments": 2}
                }
            }
        }

        # Apply filters
        if filters:
            for field, value in filters.items():
                if ":" in value:
                    gte, lte = value.split(":")
                    body["query"]["bool"]["must"].append({
                        "range": {field: {"gte": gte, "lte": lte}}
                    })
                else:
                    body["query"]["bool"]["must"].append({
                        "term": {field: value}
                    })

        try:
            res = self.es.search(index=self.index_name, body=body)
            results = {}

            raw_scores = [hit["_score"] for hit in res["hits"]["hits"]]
            max_score = max(raw_scores) if raw_scores else 1

            for hit in res["hits"]["hits"]:
                pid = hit["_source"]["paper_id"]
                normalized_score = hit["_score"] / max_score
                
                highlights = hit.get("highlight", {})
                results[pid] = {
                    "score": normalized_score,
                    "highlights": highlights
                }

            return results
        except Exception as e:
            print(f"Error in keyword search with highlight: {e}")
            return {}