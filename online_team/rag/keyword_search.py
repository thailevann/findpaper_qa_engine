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
    multi_match_boost: float = 1.0


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
    def _build_query(self, query_text: str) -> Dict:
        body = {
            "size": self.config.top_k,   # cuối cùng vẫn trả ra top_k
            "_source": ["paper_id", "title", "abstract"], 
            "query": {
                "bool": {
                    "must": [],
                    "should": [
                        {"match_phrase": {
                            "title": {"query": query_text, "boost": self.config.title_boost}
                        }},
                        {"match_phrase": {
                            "abstract": {"query": query_text, "boost": self.config.abstract_boost}
                        }},
                        {"multi_match": {
                            "query": query_text,
                            "fields": ["title^2", "abstract"],
                            "type": "best_fields",
                            "boost": self.config.multi_match_boost
                        }}
                    ],
                    "minimum_should_match": 1  
                }
            },
            "highlight": {
                "fields": {"title": {}, "abstract": {}}
            },
            "explain": True,
            "rescore": {
                "window_size": self.config.top_k,  
                "query": {
                    "rescore_query": {
                        "multi_match": {
                            "query": query_text,
                            "fields": ["title^3", "abstract^2"], 
                            "type": "phrase"  
                        }
                    },
                    "query_weight": 0.7,
                    "rescore_query_weight": 1.3
                }
            }
        }
        return body

    def search(
        self, 
        query_text: str, 
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, str]] = None
    ) -> list[dict]:
        """
        Keyword search returning per-field matches with highlight info:
        [
        {"paper_id": str, "field": "title", "text": "...", "highlight": [...]|None},
        {"paper_id": str, "field": "abstract", "text": "...", "highlight": [...]|None},
        ...
        ]
        """
        top_k = top_k or self.config.top_k
        body = self._build_query(query_text)
        body["size"] = top_k
        self._apply_filters(body, filters)

        logger.debug(f"[KeywordSearch] Sending ES query: {body}")

        results = []
        try:
            res = self.es.search(index=self.index_name, body=body)
            hits = res["hits"]["hits"]

            for i, hit in enumerate(hits, start=1):
                src = hit.get("_source", {})
                pid = src.get("paper_id")
                highlight = hit.get("highlight", {})

                logger.debug(
                    f"[KeywordSearch] Hit {i}: pid={pid}, highlight_keys={list(highlight.keys())}"
                )

                if "title" in highlight:
                    for frag in highlight["title"]:
                        results.append({
                            "paper_id": pid,
                            "field": "title",
                            "text": frag,
                            "highlight": highlight["title"]  
                        })

                if "abstract" in highlight:
                    for frag in highlight["abstract"]:
                        results.append({
                            "paper_id": pid,
                            "field": "abstract",
                            "text": frag,
                            "highlight": highlight["abstract"]
                        })

            return results
        except Exception as e:
            logger.warning(f"Error in keyword search: {e}", exc_info=True)
            return []
        finally:
            # Log produced fragment info (how many pieces and unique papers). Use a
            # local-safe lookup so logging doesn't raise if results isn't defined.
            try:
                _results = locals().get('results', []) or []
                frag_count = len(_results)
                unique_papers = len(set(r.get("paper_id") for r in _results if r.get("paper_id")))
                logger.info(f"[KeywordSearch] Produced {frag_count} fragments across {unique_papers} unique papers for query '{query_text}'")
            except Exception:
                # best-effort logging; don't break functionality on logging errors
                pass


    async def search_async(
        self, 
        query_text: str, 
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, str]] = None
    ) -> list[dict]:
        logger.debug(f"[KeywordSearch] search_async called with top_k={top_k}")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            self.search,
            query_text, top_k, filters
        )
