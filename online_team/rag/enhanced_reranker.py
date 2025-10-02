"""
Enhanced Reranker with constraint checking and domain-specific scoring.

Features:
1. CrossEncoder-based relevance scoring
2. Constraint checks (minimum keyword occurrences)
3. Boost/downrank based on content analysis
4. Configurable scoring weights
5. Quality filters
"""

import logging
import numpy as np
from sentence_transformers import CrossEncoder
from elasticsearch import Elasticsearch
from typing import List, Dict, Optional
from dataclasses import dataclass
import re

from config import CROSS_ENCODER_MODEL

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class EnhancedRerankerConfig:
    """Configuration for enhanced reranker"""
    top_final: int = 20
    crossencoder_model: str = None
    batch_size: int = 32
    use_distil: bool = False
    use_crossencoder: bool = True
    max_candidates_for_rerank: int = 300
    
    # Constraint checking
    use_constraint_checks: bool = True
    min_keyword_occurrences: int = 2  # Min occurrences of main topic
    
    # Boost/downrank settings
    use_content_boosting: bool = True
    boost_if_contains: List[str] = None  # Keywords that boost score
    downrank_if_contains: List[str] = None  # Keywords that downrank
    
    # Scoring weights
    crossencoder_weight: float = 0.7
    constraint_weight: float = 0.15
    content_boost_weight: float = 0.15
    
    def __post_init__(self):
        if self.boost_if_contains is None:
            self.boost_if_contains = []
        if self.downrank_if_contains is None:
            self.downrank_if_contains = []


class EnhancedReranker:
    """
    Enhanced reranker with constraint checks and content-based scoring adjustments.
    """
    
    def __init__(
        self,
        es_url: str = "http://localhost:9200",
        index_name: str = "papers_text",
        config: Optional[EnhancedRerankerConfig] = None
    ):
        self.config = config or EnhancedRerankerConfig()
        self.batch_size = self.config.batch_size
        self.es = Elasticsearch(es_url, request_timeout=120)
        self.index_name = index_name
        
        # Initialize CrossEncoder
        model_name = self.config.crossencoder_model or CROSS_ENCODER_MODEL
        if self.config.use_distil and "distil" not in model_name.lower():
            model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
        
        self.ce_model = CrossEncoder(model_name) if self.config.use_crossencoder else None
        if self.ce_model:
            logger.info(f"[EnhancedReranker] Loaded CrossEncoder: {model_name}")
    
    def _extract_main_keywords(self, query: str) -> List[str]:
        """
        Extract main keywords from query for constraint checking.
        Removes stop words and extracts meaningful terms.
        """
        # Common stop words
        stop_words = {
            'a', 'an', 'the', 'in', 'on', 'at', 'for', 'to', 'of', 'and', 'or',
            'is', 'are', 'was', 'were', 'what', 'how', 'why', 'when', 'where',
            'survey', 'review', 'papers', 'research', 'methods', 'approaches'
        }
        
        # Tokenize and filter
        tokens = re.findall(r'\b\w+\b', query.lower())
        keywords = [t for t in tokens if t not in stop_words and len(t) > 3]
        
        # Keep only most important keywords (e.g., top 3-5)
        return keywords[:5]
    
    def _check_keyword_constraints(
        self,
        query: str,
        text: str,
        min_occurrences: Optional[int] = None
    ) -> float:
        """
        Check if text meets minimum keyword occurrence constraints.
        
        Returns:
            Constraint score (0.0 to 1.0)
        """
        if not self.config.use_constraint_checks:
            return 1.0
        
        min_occ = min_occurrences or self.config.min_keyword_occurrences
        main_keywords = self._extract_main_keywords(query)
        
        if not main_keywords:
            return 1.0
        
        text_lower = text.lower()
        
        # Count occurrences of each keyword
        occurrence_counts = {}
        for keyword in main_keywords:
            # Use word boundaries for accurate counting
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            count = len(pattern.findall(text))
            occurrence_counts[keyword] = count
        
        # Check if at least one keyword appears min_occ times
        max_occurrences = max(occurrence_counts.values()) if occurrence_counts else 0
        
        # Score based on maximum occurrences
        if max_occurrences >= min_occ:
            # Full credit if meets minimum
            constraint_score = 1.0
        elif max_occurrences > 0:
            # Partial credit
            constraint_score = max_occurrences / min_occ
        else:
            # No occurrences - significant penalty
            constraint_score = 0.1
        
        logger.debug(f"[EnhancedReranker] Constraint check - max_occ: {max_occurrences}, score: {constraint_score:.2f}")
        
        return constraint_score
    
    def _calculate_content_boost(
        self,
        text: str,
        boost_terms: Optional[List[str]] = None,
        downrank_terms: Optional[List[str]] = None
    ) -> float:
        """
        Calculate boost/downrank score based on content analysis.
        
        Returns:
            Content boost score (can be < 1.0 for downranking or > 1.0 for boosting)
        """
        if not self.config.use_content_boosting:
            return 1.0
        
        text_lower = text.lower()
        
        # Use provided terms or config defaults
        boost_terms = boost_terms or self.config.boost_if_contains
        downrank_terms = downrank_terms or self.config.downrank_if_contains
        
        boost_score = 1.0
        matched_boosts = []
        matched_downranks = []
        
        # Check boost terms
        if boost_terms:
            for term in boost_terms:
                if term.lower() in text_lower:
                    boost_score *= 1.15  # 15% boost per matching term
                    matched_boosts.append(term)
        
        # Check downrank terms
        if downrank_terms:
            for term in downrank_terms:
                if term.lower() in text_lower:
                    boost_score *= 0.7  # 30% downrank per matching term
                    matched_downranks.append(term)
        
        # Cap boost/downrank to reasonable ranges
        boost_score = min(max(boost_score, 0.3), 2.0)
        
        if matched_boosts or matched_downranks:
            logger.debug(f"[EnhancedReranker] Content boost: {boost_score:.2f} - "
                        f"Boosts: {matched_boosts}, Downranks: {matched_downranks}")
        
        return boost_score
    
    def _combine_scores(
        self,
        ce_score: float,
        constraint_score: float,
        content_boost: float
    ) -> float:
        """
        Combine multiple scores into final ranking score.
        
        Uses weighted combination of:
        - CrossEncoder relevance score
        - Constraint check score
        - Content boost/downrank multiplier
        """
        # Robust normalization of CrossEncoder score
        normalized_ce = self._normalize_ce(ce_score)
        
        # Weighted combination
        base_score = (
            self.config.crossencoder_weight * normalized_ce +
            self.config.constraint_weight * constraint_score
        )
        
        # Apply content boost as multiplier
        # Apply bounded content boost; cap the effect to avoid outliers
        bounded_boost = max(0.5, min(content_boost, 1.8))
        final_score = base_score * (1 + self.config.content_boost_weight * (bounded_boost - 1))
        
        return final_score

    def _normalize_ce(self, ce_score: float) -> float:
        """Normalize CE raw score to [0,1] using sigmoid; robust fallback to min-max."""
        try:
            import math
            return 1.0 / (1.0 + math.exp(-ce_score))
        except Exception:
            # Fallback to min-max style if sigmoid fails
            normalized = (ce_score + 5) / 10
            return max(0.0, min(1.0, normalized))
    
    def rerank(
        self,
        query_text: str,
        candidate_results: List[Dict],
        top_final: Optional[int] = None,
        boost_terms: Optional[List[str]] = None,
        downrank_terms: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Enhanced reranking with constraints and content-based adjustments.
        
        Args:
            query_text: User query
            candidate_results: List of candidate results to rerank
            top_final: Number of top results to return
            boost_terms: Additional terms to boost (supplements config)
            downrank_terms: Additional terms to downrank (supplements config)
            
        Returns:
            Reranked results with detailed scoring
        """
        top_final = top_final or self.config.top_final
        
        if not candidate_results:
            logger.info("[EnhancedReranker] No candidate results to rerank")
            return []
        
        # Limit candidates
        max_candidates = self.config.max_candidates_for_rerank
        if len(candidate_results) > max_candidates:
            logger.info(f"[EnhancedReranker] Limiting candidates from {len(candidate_results)} to {max_candidates}")
            candidate_results = candidate_results[:max_candidates]
        
        logger.info(f"[EnhancedReranker] Reranking {len(candidate_results)} candidates")
        
        # Fetch full paper data
        unique_paper_ids = list(set(r.get("paper_id") for r in candidate_results if r.get("paper_id")))
        paper_data = {}
        
        if unique_paper_ids:
            try:
                res = self.es.mget(index=self.index_name, ids=unique_paper_ids)
                paper_data = {
                    doc["_id"]: doc.get("_source", {})
                    for doc in res["docs"]
                    if doc.get("found", False)
                }
            except Exception as e:
                logger.warning(f"[EnhancedReranker] Failed to fetch paper data: {e}")
        
        # Prepare results with evidence text
        processed_results = []
        for result in candidate_results:
            paper_id = result.get("paper_id")
            evidence = result.get("evidence") or result.get("text", "")
            
            # Get full paper text if needed
            if not evidence and paper_id in paper_data:
                paper = paper_data[paper_id]
                abstract = paper.get("abstract", "")
                title = paper.get("title", "")
                evidence = f"{title} {abstract}"
            
            if not evidence.strip():
                logger.debug(f"[EnhancedReranker] Skipping result with no evidence: {paper_id}")
                continue
            
            processed_results.append({
                "paper_id": paper_id,
                "title": paper_data.get(paper_id, {}).get("title", result.get("title", "")),
                "abstract": paper_data.get(paper_id, {}).get("abstract", ""),
                "evidence": evidence,
                "original_result": result
            })
        
        if not processed_results:
            logger.warning("[EnhancedReranker] No valid results after processing")
            return []
        
        # Step 1: CrossEncoder scores
        ce_scores = []
        if self.ce_model and self.config.use_crossencoder:
            pairs = [(query_text, r["evidence"]) for r in processed_results]
            try:
                for i in range(0, len(pairs), self.batch_size):
                    batch = pairs[i:i+self.batch_size]
                    batch_scores = self.ce_model.predict(batch).tolist()
                    ce_scores.extend(batch_scores)
            except Exception as e:
                logger.error(f"[EnhancedReranker] CrossEncoder failed: {e}")
                # Fallback: use uniform scores
                ce_scores = [0.0] * len(processed_results)
        else:
            ce_scores = [0.0] * len(processed_results)
        
        # Step 2: Constraint checks and content boosting
        combined_boost_terms = list(set((boost_terms or []) + self.config.boost_if_contains))
        combined_downrank_terms = list(set((downrank_terms or []) + self.config.downrank_if_contains))
        
        for i, result in enumerate(processed_results):
            # Full text for analysis (title + abstract); fallback to evidence if too short
            full_text = f"{result['title']} {result['abstract']}".strip()
            if len(full_text) < 20:
                full_text = result.get("evidence", full_text)
            
            # Constraint check
            constraint_score = self._check_keyword_constraints(query_text, full_text)
            
            # Content boost/downrank
            content_boost = self._calculate_content_boost(
                full_text,
                boost_terms=combined_boost_terms,
                downrank_terms=combined_downrank_terms
            )
            
            # Combine scores
            final_score = self._combine_scores(ce_scores[i], constraint_score, content_boost)
            
            # Store all scores (include normalized CE for easier consumption)
            result["ce_score_raw"] = float(ce_scores[i])
            result["ce_score"] = float(self._normalize_ce(ce_scores[i]))
            result["constraint_score"] = float(constraint_score)
            result["content_boost"] = float(content_boost)
            result["final_score"] = float(final_score)
        
        # Sort by final score
        processed_results.sort(key=lambda x: x["final_score"], reverse=True)
        
        # Take top results
        final_results = processed_results[:top_final]
        
        logger.info(f"[EnhancedReranker] Reranking complete - returning {len(final_results)} results")
        
        # Log score statistics
        if final_results:
            avg_ce = np.mean([r["ce_score"] for r in final_results])
            avg_constraint = np.mean([r["constraint_score"] for r in final_results])
            avg_boost = np.mean([r["content_boost"] for r in final_results])
            logger.info(f"[EnhancedReranker] Score stats - CE: {avg_ce:.3f}, Constraint: {avg_constraint:.3f}, Boost: {avg_boost:.3f}")
        
        # Format output
        output_results = []
        for r in final_results:
            output = r["original_result"].copy()
            output.update({
                "title": r["title"],
                "cross_score": r["ce_score"],            # normalized [0,1]
                "cross_score_raw": r["ce_score_raw"],     # raw CE score
                "constraint_score": r["constraint_score"],
                "content_boost": r["content_boost"],
                "final_score": r["final_score"]
            })
            output_results.append(output)
        
        return output_results
    
    async def rerank_async(
        self,
        query_text: str,
        candidate_results: List[Dict],
        top_final: Optional[int] = None,
        boost_terms: Optional[List[str]] = None,
        downrank_terms: Optional[List[str]] = None
    ):
        """Async version of rerank"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.rerank,
            query_text,
            candidate_results,
            top_final,
            boost_terms,
            downrank_terms
        )


def demo():
    """Demo the enhanced reranker"""
    config = EnhancedRerankerConfig(
        top_final=10,
        use_constraint_checks=True,
        min_keyword_occurrences=2,
        use_content_boosting=True,
        boost_if_contains=["ROUGE", "CNN/DailyMail", "BART", "PEGASUS", "benchmark"],
        downrank_if_contains=["economics", "finance", "macroeconomics"]
    )
    
    reranker = EnhancedReranker(config=config)
    
    print(f"\n{'='*80}")
    print(f"Enhanced Reranker Configuration")
    print(f"{'='*80}")
    print(f"Constraint checking: {config.use_constraint_checks}")
    print(f"Min keyword occurrences: {config.min_keyword_occurrences}")
    print(f"Content boosting: {config.use_content_boosting}")
    print(f"Boost terms: {', '.join(config.boost_if_contains[:5])}...")
    print(f"Downrank terms: {', '.join(config.downrank_if_contains)}")
    print(f"\nScoring weights:")
    print(f"  CrossEncoder: {config.crossencoder_weight}")
    print(f"  Constraint: {config.constraint_weight}")
    print(f"  Content boost: {config.content_boost_weight}")


if __name__ == "__main__":
    demo()

