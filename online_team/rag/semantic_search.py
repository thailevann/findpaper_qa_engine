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
        # Perform a lightweight index/mapping diagnostic to help debug 0-hit cases
        try:
            mapping = self.es.indices.get_mapping(index=self.index_name)
            logger.info(f"[SemanticSearch] Retrieved mapping for index '{self.index_name}'")
            # Inspect whether configured vector fields exist in mapping
            props = {}
            try:
                props = mapping.get(self.index_name, {}).get('mappings', {}).get('properties', {})
            except Exception:
                # Try alternate nested path
                try:
                    props = list(mapping.values())[0].get('mappings', {}).get('properties', {})
                except Exception:
                    props = {}

            for vf in self.config.vector_fields:
                # support nested like 'chunks.embedding'
                parts = vf.split('.')
                node = props
                exists = True
                for p in parts:
                    if not node or p not in node:
                        exists = False
                        break
                    node = node[p].get('properties') if 'properties' in node[p] else node[p]
                if exists:
                    logger.info(f"[SemanticSearch] Vector field exists in mapping: {vf}")
                else:
                    logger.warning(f"[SemanticSearch] Vector field NOT found in mapping: {vf}")

            # Check index document count / sample
            try:
                count_res = self.es.count(index=self.index_name)
                total_docs = count_res.get('count', 0)
                logger.info(f"[SemanticSearch] Index '{self.index_name}' document count: {total_docs}")
                if total_docs == 0:
                    logger.warning(f"[SemanticSearch] Index '{self.index_name}' appears empty — no vectors available")
                else:
                    sample = self.es.search(index=self.index_name, size=1, _source=True)
                    if sample and sample.get('hits', {}).get('hits'):
                        logger.debug(f"[SemanticSearch] Sample hit keys: {list(sample['hits']['hits'][0].get('_source', {}).keys())}")
            except Exception:
                logger.debug("[SemanticSearch] Could not read index count/sample for diagnostics")
        except Exception as e:
            logger.warning(f"[SemanticSearch] Failed to fetch mapping for index '{self.index_name}': {e}")

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
        """Build KNN query for a single vector field compatible with ES 8.x"""
        # Ensure num_candidates is at least equal to k (top_k)
        num_candidates = max(self.config.knn_num_candidates, top_k)
        
        knn_query = {
            "field": field,
            "query_vector": query_embedding,
            "k": top_k,
            "num_candidates": num_candidates
        }
        
        # Add filters if provided
        if filters:
            filter_clauses = self._apply_filters(filters)
            if filter_clauses:
                knn_query["filter"] = filter_clauses
                
        return knn_query

    def _build_multi_field_knn_query(
        self,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[Dict[str, str]] = None
    ):
        """Build multiple KNN queries for different fields"""
        knn_queries = []
        # Ensure num_candidates is at least equal to k (top_k)
        num_candidates = max(self.config.knn_num_candidates, top_k)
        
        for field in self.config.vector_fields:
            knn_query = {
                "field": field,
                "query_vector": query_embedding,
                "k": top_k,
                "num_candidates": num_candidates,
                "boost": 1.0  # Equal weighting for all fields
            }
            
            # Add filters if provided
            if filters:
                filter_clauses = self._apply_filters(filters)
                if filter_clauses:
                    knn_query["filter"] = filter_clauses
                    
            knn_queries.append(knn_query)
            
        return knn_queries

    def fetch_text_from_papers_text(self, paper_ids: List[str]) -> Dict[str, dict]:
        """Fetch full text of papers from papers_text index"""
        if not paper_ids:
            return {}

        body = {
            "size": len(paper_ids),
            "_source": ["title", "abstract", "chunks.text"],
            "query": {
                "ids": {"values": paper_ids}
            }
        }
        res = self.es.search(index="papers_text", body=body)
        docs = {hit["_id"]: hit["_source"] for hit in res["hits"]["hits"]}
        return docs

    def search(
        self,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, str]] = None,
        use_multi_field: bool = True
    ) -> list[dict]:
        top_k = top_k or self.config.top_k

        try:
            # Use the new knn parameter instead of query for ES 8.x
            if use_multi_field and len(self.config.vector_fields) > 1:
                # Multiple KNN queries
                knn_queries = self._build_multi_field_knn_query(query_embedding, top_k, filters)
                body = {
                    "knn": knn_queries,
                    "size": top_k,
                    "_source": ["paper_id"]
                }
            else:
                # Single KNN query
                knn_query = self._build_knn_query(self.config.vector_fields[0], query_embedding, top_k, filters)
                body = {
                    "knn": knn_query,
                    "size": top_k,
                    "_source": ["paper_id"]
                }

            # Execute search
            # Diagnostic logging: embedding shape and a short sample
            try:
                emb_len = len(query_embedding) if query_embedding is not None else 0
            except Exception:
                emb_len = 0
            logger.info(f"[SemanticSearch] Executing KNN on index='{self.index_name}' field(s)='{self.config.vector_fields}' top_k={top_k} emb_len={emb_len}")
            logger.debug(f"[SemanticSearch] KNN request body: {body}")

            res = self.es.search(index=self.index_name, body=body)
            hits = res["hits"]["hits"]

            # If KNN returned no hits, try fallback script_score to avoid silent empty results
            if not hits:
                logger.info("[SemanticSearch] KNN returned 0 hits, trying fallback script_score search to recover results")
                return self._fallback_script_score_search(query_embedding, top_k, filters)
            paper_ids = [hit["_id"] for hit in hits]
            doc_scores = {hit["_id"]: hit["_score"] for hit in hits}

            # Fetch text content
            papers_text = self.fetch_text_from_papers_text(paper_ids)

            # Build results with all text fields
            all_records = []
            for pid in paper_ids:
                src = papers_text.get(pid, {})
                score = doc_scores.get(pid, 0.0)

                if src.get("title"):
                    all_records.append({
                        "paper_id": pid, 
                        "field": "title", 
                        "text": src["title"], 
                        "score": score
                    })
                if src.get("abstract"):
                    all_records.append({
                        "paper_id": pid, 
                        "field": "abstract", 
                        "text": src["abstract"], 
                        "score": score
                    })
                chunks = src.get("chunks", [])
                for idx, ch in enumerate(chunks):
                    if isinstance(ch, dict) and "text" in ch:
                        all_records.append({
                            "paper_id": pid, 
                            "field": "chunk", 
                            "text": ch["text"], 
                            "score": score, 
                            "chunk_idx": idx
                        })
                    elif isinstance(ch, str):
                        all_records.append({
                            "paper_id": pid, 
                            "field": "chunk", 
                            "text": ch, 
                            "score": score, 
                            "chunk_idx": idx
                        })

            # Sort by score and return top results
            all_records.sort(key=lambda x: x["score"], reverse=True)

     
            results = all_records[:top_k]
            logger.info(f"[SemanticSearch] Total semantic results after slice: {len(results)}")
            return results

        except Exception as e:
            logger.warning(f"Semantic search failed: {e}", exc_info=True)
            # Fallback to script_score search
            return self._fallback_script_score_search(query_embedding, top_k, filters)

    def _fallback_script_score_search(
        self,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[Dict[str, str]] = None
        ) -> list[dict]:
            """Fallback search using script_score, then fetch text from papers_text"""
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

            try:
                res = self.es.search(index=self.index_name, body=body)
                hits = res["hits"]["hits"]
                paper_ids = [hit["_id"] for hit in hits]
                scores = {hit["_id"]: hit["_score"] for hit in hits}
                
                # Fetch text from papers_text
                if not paper_ids:
                    return []

                text_body = {
                    "size": len(paper_ids),
                    "_source": ["title", "abstract", "chunks.text"],
                    "query": {"ids": {"values": paper_ids}}
                }
                text_res = self.es.search(index="papers_text", body=text_body)
                id_to_text = {hit["_id"]: hit["_source"] for hit in text_res["hits"]["hits"]}

                # Build results
                results = []
                for pid in paper_ids:
                    src = id_to_text.get(pid, {})
                    score = scores.get(pid, 0.0)

                    if src.get("title"):
                        results.append({
                            "paper_id": pid, 
                            "field": "title", 
                            "text": src["title"], 
                            "score": score
                        })
                    if src.get("abstract"):
                        results.append({
                            "paper_id": pid, 
                            "field": "abstract", 
                            "text": src["abstract"], 
                            "score": score
                        })
                    chunks = src.get("chunks", [])
                    for idx, ch in enumerate(chunks):
                        if isinstance(ch, dict) and "text" in ch:
                            results.append({
                                "paper_id": pid, 
                                "field": "chunk", 
                                "text": ch["text"], 
                                "score": score, 
                                "chunk_idx": idx
                            })
                        elif isinstance(ch, str):
                            results.append({
                                "paper_id": pid, 
                                "field": "chunk", 
                                "text": ch, 
                                "score": score, 
                                "chunk_idx": idx
                            })

                return results
            except Exception as e:
                logger.error(f"Fallback script_score search also failed: {e}")
                return []

    async def search_async(
        self,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, str]] = None,
        use_multi_field: bool = True
    ) -> list[dict]:
        """Async semantic search returning full text"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.search,
            query_embedding,
            top_k or self.config.top_k,
            filters,
            use_multi_field
        )