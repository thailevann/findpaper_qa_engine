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
    max_results_before_rerank: int = 100  # Limit results before reranking


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
        
    async def _sequential_search(
        self,
        query_text: str,
        query_embedding: List[float],
        filters: Optional[Dict[str, str]],
        top_k: Optional[int]
    ) -> Tuple[List[Dict], List[Dict]]:
        key_results = self.keyword_search.search(query_text, top_k, filters)
        sem_results = await self.semantic_search.search_async(
            query_embedding=query_embedding,  
            top_k=top_k,
            filters=filters,
            use_multi_field=self.config.use_multi_field_semantic
        )
        return key_results, sem_results

    async def search_parallel(
        self,
        query_text: str,
        query_embedding: list[float] = None,
        filters: Optional[Dict[str, str]] = None,
        top_k: Optional[int] = None
    ) -> Tuple[List[Dict], List[Dict]]:
        """Parallel keyword & semantic search"""
        try:
            key_task = self.keyword_search.search_async(query_text, top_k, filters)
            sem_task = self.semantic_search.search_async(
                query_embedding=query_embedding,
                top_k=top_k,
                filters=filters,
                use_multi_field=self.config.use_multi_field_semantic
            )
            keyword_results, semantic_results = await asyncio.wait_for(
                asyncio.gather(key_task, sem_task),
                timeout=self.config.search_timeout
            )
            return keyword_results, semantic_results
        except Exception as e:
            logger.warning(f"Parallel search failed ({e}), falling back to sequential search")
            return await self._sequential_search(query_text, query_embedding, filters, top_k)

    def merge_keyword_semantic(
        self,
        keyword_results: List[Dict],
        semantic_results: List[Dict]
    ) -> List[Dict]:
        """Merge keyword and semantic results using OR semantics over pieces.

        We treat each piece (paper_id + normalized text) as an atomic candidate. The
        merged set is the union of keyword and semantic pieces. When a piece appears
        in both keyword and semantic results, prefer the keyword entry (which may
        contain highlights). This preserves all non-common parts while removing
        exact duplicates.
        """
        merged: Dict[Tuple[str, str], Dict] = {}

        def _normalize_text(x) -> str:
            if x is None:
                return ""
            if isinstance(x, list):
                x = " ".join(str(t) for t in x if t)
            return str(x).strip()

        # Add keyword pieces first so we prefer highlights when duplicates exist
        for r in keyword_results:
            pid = r.get("paper_id")
            if not pid:
                continue
            text = _normalize_text(r.get("text"))
            if not text:
                continue
            key = (pid, text)
            merged[key] = {
                "paper_id": pid,
                "field": r.get("field"),
                "text": text,
                "highlight": r.get("highlight"),
                "score": r.get("score", 0.0),
                "source": "keyword"
            }

        # Add semantic pieces if their (paper_id, text) isn't already present
        for r in semantic_results:
            pid = r.get("paper_id")
            if not pid:
                continue
            text = _normalize_text(r.get("text"))
            if not text:
                continue
            key = (pid, text)
            if key in merged:
                # Already present from keyword; upgrade source tag to reflect both
                merged[key]["source"] = "keyword+semantic"
                # If keyword had no score but semantic has, update score
                if merged[key].get("score", 0.0) < r.get("score", 0.0):
                    merged[key]["score"] = r.get("score", 0.0)
                continue
            merged[key] = {
                "paper_id": pid,
                "field": r.get("field"),
                "text": text,
                "highlight": None,
                "score": r.get("score", 0.0),
                "source": "semantic"
            }

        logger.info(f"Merged {len(merged)} unique pieces from keyword+semantic search")
        # return as list preserving some order (sort by score desc)
        results = list(merged.values())
        results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return results

    async def search_with_reranking(
        self,
        query_text: str,
        query_embedding: list[float] = None,  
        filters: Optional[Dict[str, str]] = None,
        top_k: Optional[int] = None,
        top_final: Optional[int] = None
    ) -> List[Dict[str, Union[str, float]]]:
        """
        Main pipeline:
        1. Run keyword & semantic search in parallel
        2. Merge results
        3. Prepare evidence for reranker with highlights
        4. Rerank using CrossEncoder
        """
        start_time = time.time()
        logger.info("Running parallel keyword and semantic search...")
        
        # Determine requested counts
        requested_final = top_final or top_k or self.config.keyword_config and getattr(self.config.keyword_config, 'top_k', None) or 20
        print("DEBUG requested_final =", requested_final, "top_k =", top_k)

        requested_search_k = max(requested_final, top_k or 0, 50)

        # Step 1: Parallel search -- request more from underlying searches so we can merge and still reach requested_final
        keyword_results, semantic_results = await self.search_parallel(
            query_text=query_text,
            query_embedding=query_embedding,
            filters=filters,
            top_k=requested_search_k
        )
        # Log raw retrieval counts to help debug differences between ES hits and produced fragments
        try:
            kw_count = len(keyword_results) if keyword_results is not None else 0
        except Exception:
            kw_count = 0
        try:
            sem_count = len(semantic_results) if semantic_results is not None else 0
        except Exception:
            sem_count = 0
        logger.info(f"Raw retrieval counts - keyword: {kw_count}, semantic: {sem_count}")
        
        # Step 2: Merge results
        merged_results = self.merge_keyword_semantic(keyword_results, semantic_results)
        # Breakdown merged sources (keyword / semantic / keyword+semantic)
        src_counts = {"keyword": 0, "semantic": 0, "keyword+semantic": 0}
        unique_papers_before = set()
        for r in merged_results:
            s = r.get("source")
            if s in src_counts:
                src_counts[s] += 1
            else:
                src_counts[s] = src_counts.get(s, 0) + 1
            pid = r.get("paper_id")
            if pid:
                unique_papers_before.add(pid)
        logger.info(f"Merged source breakdown: keyword={src_counts.get('keyword',0)}, semantic={src_counts.get('semantic',0)}, keyword+semantic={src_counts.get('keyword+semantic',0)}")
        
        # Step 3: Prepare evidence for reranking and limit results
        cleaned_results = []
        for r in merged_results:
            # Use highlight for evidence if available, otherwise use text
            highlight = r.get("highlight")
            text = r.get("text", "")
            
            # Handle list highlights
            if isinstance(highlight, list):
                highlight = " ".join(str(h) for h in highlight if h)
            if isinstance(text, list):
                text = " ".join(str(t) for t in text if t)

            # Prepare evidence (highlight takes priority for user experience)
            evidence_text = highlight if highlight and highlight.strip() else text
            
            if not evidence_text or not evidence_text.strip():
                logger.warning(f"Skipping result with empty evidence for paper_id={r.get('paper_id')}")
                continue
                
            # Add evidence to result
            r["evidence"] = evidence_text
            cleaned_results.append(r)
        
        # Ensure we have at least requested_final candidates before limiting for rerank
        max_before_rerank = self.config.max_results_before_rerank
        # If user requested more than configured cap, temporarily bump cap to honor the request
        if requested_final and requested_final > max_before_rerank:
            logger.info(f"Bumping pre-rerank cap from {max_before_rerank} to {requested_final} to honor requested final limit")
            max_before_rerank = requested_final

        # If merged results are fewer than requested_final, try to pad from semantic results first, then keyword
        if requested_final and len(cleaned_results) < requested_final:
            needed = requested_final - len(cleaned_results)
            logger.info(f"Merged results ({len(cleaned_results)}) < requested_final ({requested_final}), attempting to pad {needed} more candidates from semantic results")
            # Build set of existing paper_ids to avoid duplicates (we want unique papers)
            existing_keys = set(r['paper_id'] for r in cleaned_results if r.get('paper_id'))
            # semantic_results may contain entries without highlights; use them to pad
            sem_added = 0
            for s in semantic_results:
                pid = s.get('paper_id')
                if not pid or pid in existing_keys:
                    continue
                # create a normalized result similar to merged format
                candidate = {
                    'paper_id': pid,
                    'field': s.get('field'),
                    'text': s.get('text'),
                    'highlight': None,
                    'score': s.get('score', 0.0),
                    'source': 'semantic'
                }
                # prepare evidence same as above
                text = candidate.get('text', '')
                evidence_text = text if isinstance(text, str) else ' '.join(text) if isinstance(text, list) else ''
                if evidence_text and evidence_text.strip():
                    candidate['evidence'] = evidence_text
                    cleaned_results.append(candidate)
                    existing_keys.add(pid)
                    needed -= 1
                    sem_added += 1
                if needed <= 0:
                    break
            logger.info(f"Padded {sem_added} candidates from semantic results")

            # If still need more, try keyword results as last resort
            if requested_final and len(cleaned_results) < requested_final:
                needed = requested_final - len(cleaned_results)
                logger.info(f"Padding still needs {needed} candidates, trying keyword results")
                kw_added = 0
                for k in keyword_results:
                    pid = k.get('paper_id')
                    if not pid or pid in existing_keys:
                        continue
                    candidate = {
                        'paper_id': pid,
                        'field': k.get('field'),
                        'text': k.get('text'),
                        'highlight': k.get('highlight'),
                        'score': k.get('score', 0.0),
                        'source': 'keyword'
                    }
                    # evidence preparation
                    highlight = candidate.get('highlight')
                    text = candidate.get('text', '')
                    if isinstance(highlight, list):
                        highlight_val = ' '.join(str(h) for h in highlight if h)
                    else:
                        highlight_val = highlight
                    if isinstance(text, list):
                        text_val = ' '.join(str(t) for t in text if t)
                    else:
                        text_val = text
                    evidence_text = highlight_val if highlight_val and str(highlight_val).strip() else text_val
                    if evidence_text and str(evidence_text).strip():
                        candidate['evidence'] = evidence_text
                        cleaned_results.append(candidate)
                        existing_keys.add(pid)
                        needed -= 1
                        kw_added += 1
                    if needed <= 0:
                        break
                logger.info(f"Padded {kw_added} candidates from keyword results")

        # Do not truncate candidates before reranking - reranker will limit internally
        # (This ensures we rerank all candidates and then take the top_final afterwards.)
        logger.info(f"Search completed in {time.time()-start_time:.2f}s "
                    f"(merged {len(cleaned_results)} results after cleaning)")

        # Step 4: Reranking
        if self.reranker and self.config.enable_reranking and cleaned_results:
            logger.info("Running reranking...")
            try:
                results = await asyncio.wait_for(
                    self.reranker.rerank_async(
                        query_text=query_text,
                        candidate_results=cleaned_results,  # Pass full results, not just IDs
                        top_final=top_final
                    ),
                    timeout=self.config.rerank_timeout
                )
                logger.info(f"Reranking completed in {time.time()-start_time:.2f}s")
            except Exception as e:
                logger.error(f"Reranking failed: {e}. Using merged results directly.")
                results = cleaned_results[:top_final or 20]
        else:
            if not self.config.enable_reranking:
                logger.info("Reranking disabled, returning merged results")
            else:
                logger.info("No reranker available or no results to rerank")
            results = cleaned_results[:top_final or 20]

        logger.info(f"Total pipeline time: {time.time()-start_time:.2f}s, returning {len(results)} results")
        return results

    def get_pipeline_info(self) -> Dict[str, Union[str, bool, int, float]]:
        """Get pipeline configuration information"""
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