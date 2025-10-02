"""
Advanced Search Pipeline with Enhanced Components

Integrates:
1. Advanced Query Rewriter
2. Enhanced Keyword Search (multi-query + negative filters)
3. Enhanced Semantic Search (dataset/metric boosting)
4. Enhanced Reranker (constraint checks + content boosting)
5. Seed Paper Booster

This pipeline provides state-of-the-art retrieval quality for academic papers.
"""

import asyncio
import logging
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from online_team.preprocess.advanced_query_rewriter import AdvancedQueryRewriter, AdvancedRewrittenQuery
from online_team.rag.enhanced_keyword_search import EnhancedKeywordSearch, EnhancedKeywordSearchConfig
from online_team.rag.enhanced_semantic_search import EnhancedSemanticSearch, EnhancedSemanticSearchConfig
from online_team.rag.enhanced_reranker import EnhancedReranker, EnhancedRerankerConfig

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class AdvancedSearchPipelineConfig:
    """Configuration for the advanced search pipeline"""
    # Component configs
    keyword_config: Optional[EnhancedKeywordSearchConfig] = None
    semantic_config: Optional[EnhancedSemanticSearchConfig] = None
    reranker_config: Optional[EnhancedRerankerConfig] = None
    
    # Pipeline behavior
    use_parallel_search: bool = True
    use_query_rewriting: bool = True
    use_seed_boosting: bool = False
    
    # Performance tuning
    search_timeout: float = 30.0
    rerank_timeout: float = 60.0
    max_results_before_rerank: int = 150


class AdvancedSearchPipeline:
    """
    Advanced search pipeline orchestrating all enhanced components.
    
    Pipeline flow:
    1. Query Rewriting (taxonomy expansion, survey-aware)
    2. Parallel Search:
       - Enhanced Keyword Search (multi-query + negative filters)
       - Enhanced Semantic Search (dataset/metric boosting)
    3. Result Merging & Deduplication
    4. Enhanced Reranking (constraints + content analysis)
    5. Seed Paper Boosting
    """
    
    def __init__(
        self,
        es_url: str = "http://localhost:9200",
        text_index: str = "papers_text",
        vector_index: str = "papers_vectors",
        config: Optional[AdvancedSearchPipelineConfig] = None
    ):
        self.es_url = es_url
        self.text_index = text_index
        self.vector_index = vector_index
        self.config = config or AdvancedSearchPipelineConfig()
        
        # Initialize components
        logger.info("[AdvancedSearchPipeline] Initializing components...")
        
        # Query rewriter
        self.query_rewriter = AdvancedQueryRewriter() if self.config.use_query_rewriting else None
        
        # Keyword search
        keyword_config = self.config.keyword_config or EnhancedKeywordSearchConfig()
        self.keyword_search = EnhancedKeywordSearch(
            es_url=es_url,
            index_name=text_index,
            config=keyword_config
        )
        
        # Semantic search
        semantic_config = self.config.semantic_config or EnhancedSemanticSearchConfig()
        self.semantic_search = EnhancedSemanticSearch(
            es_url=es_url,
            index_name=vector_index,
            config=semantic_config
        )
        
        # Reranker
        reranker_config = self.config.reranker_config or EnhancedRerankerConfig()
        self.reranker = EnhancedReranker(
            es_url=es_url,
            index_name=text_index,
            config=reranker_config
        )
        
        # Seed booster removed/disabled per configuration
        self.seed_booster = None
        
        logger.info("[AdvancedSearchPipeline] Initialization complete")
    
    async def search_with_full_pipeline(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        filters: Optional[Dict[str, str]] = None,
        top_k: int = 50,
        top_final: int = 20
    ) -> Tuple[List[Dict], Dict]:
        """
        Execute the full advanced search pipeline.
        
        Args:
            query: User query
            query_embedding: Pre-computed query embedding (optional)
            filters: Search filters (year, venue, etc.)
            top_k: Number of results to retrieve initially
            top_final: Number of final results after reranking
            
        Returns:
            Tuple of (final_results, pipeline_info)
        """
        start_time = time.time()
        pipeline_info = {
            "original_query": query,
            "stages": {}
        }
        
        # ============================================================
        # Stage 1: Query Rewriting
        # ============================================================
        logger.info(f"[AdvancedSearchPipeline] Stage 1: Query Rewriting")
        stage1_start = time.time()
        
        if self.query_rewriter:
            rewritten_query, raw_rewrite = self.query_rewriter.rewrite_query(query, filters)
            pipeline_info["rewritten_query"] = rewritten_query
        else:
            # Fallback: no rewriting
            from online_team.preprocess.advanced_query_rewriter import AdvancedRewrittenQuery
            rewritten_query = AdvancedRewrittenQuery(
                original_query=query,
                rewritten_query=query,
                keyword_queries=[query],
                exclude_terms=[],
                boost_terms=[],
                domain_hints=[],
                search_filters=filters or {}
            )
        
        pipeline_info["stages"]["query_rewriting"] = {
            "duration_ms": (time.time() - stage1_start) * 1000,
            "rewritten_query": rewritten_query.rewritten_query,
            "num_keyword_queries": len(rewritten_query.keyword_queries),
            "num_exclude_terms": len(rewritten_query.exclude_terms),
            "num_boost_terms": len(rewritten_query.boost_terms),
            "domain_hints": rewritten_query.domain_hints
        }
        
        # ============================================================
        # Stage 2: Parallel Search
        # ============================================================
        logger.info(f"[AdvancedSearchPipeline] Stage 2: Parallel Search")
        stage2_start = time.time()
        
        # Execute keyword and semantic search in parallel
        if self.config.use_parallel_search:
            keyword_task = asyncio.create_task(
                self._keyword_search_async(
                    rewritten_query.keyword_queries,
                    rewritten_query.exclude_terms,
                    filters,
                    top_k
                )
            )
            semantic_task = asyncio.create_task(
                self._semantic_search_async(
                    query_embedding,
                    rewritten_query.domain_hints,
                    filters,
                    top_k
                )
            )
            
            keyword_results, semantic_results = await asyncio.gather(
                keyword_task,
                semantic_task,
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(keyword_results, Exception):
                logger.error(f"Keyword search failed: {keyword_results}")
                keyword_results = []
            if isinstance(semantic_results, Exception):
                logger.error(f"Semantic search failed: {semantic_results}")
                semantic_results = []
        else:
            # Sequential execution
            keyword_results = await self._keyword_search_async(
                rewritten_query.keyword_queries,
                rewritten_query.exclude_terms,
                filters,
                top_k
            )
            semantic_results = await self._semantic_search_async(
                query_embedding,
                rewritten_query.domain_hints,
                filters,
                top_k
            )
        
        pipeline_info["stages"]["parallel_search"] = {
            "duration_ms": (time.time() - stage2_start) * 1000,
            "keyword_results": len(keyword_results),
            "semantic_results": len(semantic_results)
        }
        
        # ============================================================
        # Stage 3: Merge & Deduplicate
        # ============================================================
        logger.info(f"[AdvancedSearchPipeline] Stage 3: Merge & Deduplicate")
        stage3_start = time.time()
        
        merged_results = self._merge_and_deduplicate(keyword_results, semantic_results)
        
        # Limit before reranking
        if len(merged_results) > self.config.max_results_before_rerank:
            merged_results = merged_results[:self.config.max_results_before_rerank]
        
        pipeline_info["stages"]["merge"] = {
            "duration_ms": (time.time() - stage3_start) * 1000,
            "merged_results": len(merged_results),
            "unique_papers": len(set(r["paper_id"] for r in merged_results))
        }
        
        # ============================================================
        # Stage 4: Enhanced Reranking
        # ============================================================
        logger.info(f"[AdvancedSearchPipeline] Stage 4: Enhanced Reranking")
        stage4_start = time.time()
        
        # Prefer advanced rewritten query for reranking if available
        rerank_query_text = rewritten_query.rewritten_query if hasattr(rewritten_query, "rewritten_query") and rewritten_query.rewritten_query else query
        reranked_results = await self.reranker.rerank_async(
            query_text=rerank_query_text,
            candidate_results=merged_results,
            top_final=top_final,
            boost_terms=rewritten_query.boost_terms,
            downrank_terms=rewritten_query.exclude_terms
        )
        
        pipeline_info["stages"]["reranking"] = {
            "duration_ms": (time.time() - stage4_start) * 1000,
            "reranked_results": len(reranked_results)
        }
        
        # Stage 5 removed: Seed Paper Boosting is disabled
        final_results = reranked_results
        
        # ============================================================
        # Pipeline Summary
        # ============================================================
        total_duration = time.time() - start_time
        pipeline_info["total_duration_ms"] = total_duration * 1000
        pipeline_info["final_results_count"] = len(final_results)
        
        logger.info(f"[AdvancedSearchPipeline] Pipeline complete in {total_duration:.2f}s - {len(final_results)} results")
        
        return final_results, pipeline_info
    
    async def _keyword_search_async(
        self,
        query_texts: List[str],
        exclude_terms: List[str],
        filters: Optional[Dict[str, str]],
        top_k: int
    ) -> List[Dict]:
        """Async wrapper for keyword search"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.keyword_search.search,
            query_texts,
            exclude_terms,
            filters,
            top_k
        )
    
    async def _semantic_search_async(
        self,
        query_embedding: Optional[List[float]],
        domain_hints: List[str],
        filters: Optional[Dict[str, str]],
        top_k: int
    ) -> List[Dict]:
        """Async wrapper for semantic search"""
        if query_embedding is None:
            logger.warning("[AdvancedSearchPipeline] No query embedding provided, skipping semantic search")
            return []
        
        return await self.semantic_search.search_async(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters,
            use_multi_field=True,
            domain_hints=domain_hints
        )
    
    def _merge_and_deduplicate(
        self,
        keyword_results: List[Dict],
        semantic_results: List[Dict]
    ) -> List[Dict]:
        """
        Merge keyword and semantic results with intelligent deduplication.
        
        Deduplication strategy:
        - Keep highest-scoring fragment per (paper_id, field)
        - Combine evidence from both sources
        """
        # Index by (paper_id, field)
        merged_dict = {}
        
        for result in keyword_results + semantic_results:
            paper_id = result.get("paper_id")
            field = result.get("field", "unknown")
            key = (paper_id, field)
            
            if key not in merged_dict:
                merged_dict[key] = result
                merged_dict[key]["sources"] = [result.get("source", "unknown")]
            else:
                # Merge: keep higher score, combine sources
                existing = merged_dict[key]
                existing_score = existing.get("score", 0)
                new_score = result.get("score", 0)
                
                if new_score > existing_score:
                    # Replace with higher-scoring version
                    source_list = existing.get("sources", [])
                    merged_dict[key] = result
                    merged_dict[key]["sources"] = source_list + [result.get("source", "unknown")]
                else:
                    # Keep existing, just add source
                    existing["sources"].append(result.get("source", "unknown"))
        
        # Convert back to list and prepare evidence field
        merged_results = []
        for result in merged_dict.values():
            # Ensure evidence field exists
            if "evidence" not in result:
                result["evidence"] = result.get("text", "")
            
            # Mark if found by both sources
            sources = set(result.get("sources", []))
            if len(sources) > 1:
                result["found_by_both"] = True
                # Slight boost for consensus
                result["score"] = result.get("score", 0) * 1.1
            
            merged_results.append(result)
        
        # Sort by score
        merged_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        logger.info(f"[AdvancedSearchPipeline] Merged {len(keyword_results)} keyword + "
                   f"{len(semantic_results)} semantic = {len(merged_results)} unique results")
        
        return merged_results
    
    def get_pipeline_info(self) -> Dict:
        """Get information about pipeline configuration"""
        return {
            "components": {
                "query_rewriter": self.query_rewriter is not None,
                "keyword_search": "enhanced",
                "semantic_search": "enhanced",
                "reranker": "enhanced",
                "seed_booster": False
            },
            "config": {
                "use_parallel_search": self.config.use_parallel_search,
                "use_query_rewriting": self.config.use_query_rewriting,
                "use_seed_boosting": False,
                "max_results_before_rerank": self.config.max_results_before_rerank
            }
        }


async def demo():
    """Demo the advanced search pipeline"""
    # Create configuration
    config = AdvancedSearchPipelineConfig(
        keyword_config=EnhancedKeywordSearchConfig(
            top_k=50,
            use_query_expansion=True,
            use_negative_filtering=True
        ),
        semantic_config=EnhancedSemanticSearchConfig(
            top_k=50,
            use_keyword_boosting=True,
            dataset_boost_factor=1.3
        ),
        reranker_config=EnhancedRerankerConfig(
            top_final=20,
            use_constraint_checks=True,
            use_content_boosting=True
        ),
        use_parallel_search=True,
        use_query_rewriting=True,
        use_seed_boosting=True
    )
    
    # Initialize pipeline
    pipeline = AdvancedSearchPipeline(config=config)
    
    print(f"\n{'='*80}")
    print(f"Advanced Search Pipeline Demo")
    print(f"{'='*80}")
    
    info = pipeline.get_pipeline_info()
    print(f"\nPipeline Components:")
    for comp, status in info["components"].items():
        print(f"  {comp}: {status}")
    
    print(f"\nPipeline Configuration:")
    for key, value in info["config"].items():
        print(f"  {key}: {value}")
    
    print(f"\n{'='*80}")
    print(f"Pipeline is ready for queries!")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(demo())

