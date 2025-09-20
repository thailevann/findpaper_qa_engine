from elasticsearch import Elasticsearch
from typing import Dict, Optional
import asyncio
import concurrent.futures
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class KeywordSearchConfig:
    """Configuration for keyword search"""
    top_k: int = 50
    title_boost: float = 5.0
    abstract_boost: float = 3.0
    multi_match_boost: float = 2.0


class KeywordSearch:
    """Keyword search using Elasticsearch with optional async support"""
    
    def __init__(
        self,
        es_url: str = "http://localhost:9200",
        index_name: str = "papers_text",
        config: Optional[KeywordSearchConfig] = None,
        max_workers: int = 8
    ):
        self.es = Elasticsearch(es_url, request_timeout=120)
        self.index_name = index_name
        self.config = config or KeywordSearchConfig()
        # Reusable executor for async
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def _build_query(self, query_text: str) -> Dict:
        """Construct the ES query body"""
        body = {
            "size": self.config.top_k,
            "_source": ["paper_id", "title", "abstract"],
            "query": {
                "bool": {
                    "must": [],
                    "should": [
                        {"match_phrase": {"title": {"query": query_text, "boost": self.config.title_boost}}},
                        {"match_phrase": {"abstract": {"query": query_text, "boost": self.config.abstract_boost}}},
                        {"multi_match": {"query": query_text, "fields": ["title^2", "abstract"],
                                         "type": "best_fields", "boost": self.config.multi_match_boost}}
                    ]
                }
            }
        }
        return body

    def _apply_filters(self, body: Dict, filters: Optional[Dict[str, str]]):
        """Apply filters to the ES query"""
        if not filters:
            return
        must = body["query"]["bool"]["must"]
        for field, value in filters.items():
            if ":" in value:
                gte, lte = value.split(":")
                must.append({"range": {field: {"gte": gte, "lte": lte}}})
            else:
                must.append({"term": {field: value}})

    def search(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """Perform keyword search"""
        top_k = top_k or self.config.top_k
        print(f"[DEBUG] KeywordSearch.search called with top_k={top_k}")

        body = self._build_query(query_text)
        body["size"] = top_k
        print(f"[DEBUG] ES query size: {body['size']}")

        self._apply_filters(body, filters)

        try:
            res = self.es.search(index=self.index_name, body=body)
            scores = {}
            raw_scores = [hit["_score"] for hit in res["hits"]["hits"]]
            max_score = max(max(raw_scores, default=1), 1e-6)  # avoid divide by zero
            for hit in res["hits"]["hits"]:
                pid = hit["_source"]["paper_id"]
                scores[pid] = hit["_score"] / max_score
            logger.info(f"Keyword search returned {len(scores)} results for query '{query_text}'")
            return scores
        except Exception as e:
            logger.warning(f"Error in keyword search: {e}")
            return {}

    async def search_async(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """Async version of search for parallel execution"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.search,
            query_text, top_k, filters
        )

    def search_with_highlight(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, str]] = None
    ) -> Dict[str, Dict]:
        """Perform keyword search with highlighting"""
        top_k = top_k or self.config.top_k
        body = self._build_query(query_text)
        body["size"] = top_k
        self._apply_filters(body, filters)

        body["highlight"] = {
            "fields": {
                "title": {"fragment_size": 150, "number_of_fragments": 1},
                "abstract": {"fragment_size": 200, "number_of_fragments": 2}
            }
        }

        try:
            res = self.es.search(index=self.index_name, body=body)
            results = {}
            raw_scores = [hit["_score"] for hit in res["hits"]["hits"]]
            max_score = max(max(raw_scores, default=1), 1e-6)
            for hit in res["hits"]["hits"]:
                pid = hit["_source"]["paper_id"]
                results[pid] = {
                    "score": hit["_score"] / max_score,
                    "highlights": hit.get("highlight", {})
                }
            logger.info(f"Keyword search with highlight returned {len(results)} results")
            return results
        except Exception as e:
            logger.warning(f"Error in keyword search with highlight: {e}")
            return {}
