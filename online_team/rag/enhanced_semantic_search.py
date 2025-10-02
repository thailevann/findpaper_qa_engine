"""
Enhanced Semantic Search with dataset/metric keyword boosting.

Features:
1. Standard vector similarity search
2. Post-retrieval boosting for papers containing important domain terms
3. Dataset keyword detection (CNN/DailyMail, ImageNet, etc.)
4. Metric keyword detection (ROUGE, mAP, etc.)
5. Combined scoring: semantic similarity + keyword boost
"""

from typing import List, Dict, Optional
import logging
from dataclasses import dataclass
import re

from online_team.rag.semantic_search import SemanticSearch, SemanticSearchConfig

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class EnhancedSemanticSearchConfig(SemanticSearchConfig):
    """Extended config with boosting parameters"""
    use_keyword_boosting: bool = True
    dataset_boost_factor: float = 1.3  # Boost papers mentioning datasets
    metric_boost_factor: float = 1.2   # Boost papers mentioning metrics
    model_boost_factor: float = 1.15   # Boost papers mentioning key models
    min_boost_occurrences: int = 1    # Minimum mentions to apply boost


# Domain-specific boost keywords
BOOST_KEYWORDS = {
    "nlp_datasets": [
        "CNN/DailyMail", "XSum", "PubMed", "Multi-News", "arXiv", "Gigaword",
        "Reddit", "WikiHow", "SAMSum", "BillSum", "NEWSROOM"
    ],
    "nlp_metrics": [
        "ROUGE", "BLEU", "METEOR", "BERTScore", "MoverScore",
        "BLEURT", "human evaluation", "F1", "precision", "recall"
    ],
    "nlp_models": [
        "BART", "PEGASUS", "T5", "GPT", "BERT", "Transformer",
        "ProphetNet", "MASS", "UniLM", "TextRank", "Pointer-Generator"
    ],
    "cv_datasets": [
        "ImageNet", "COCO", "Pascal VOC", "Cityscapes", "ADE20K",
        "KITTI", "Places", "Open Images"
    ],
    "cv_metrics": [
        "mAP", "IoU", "accuracy", "top-1", "top-5", "FID", "IS",
        "pixel accuracy", "mean IoU"
    ],
    "cv_models": [
        "ResNet", "VGG", "YOLO", "Faster R-CNN", "Mask R-CNN",
        "U-Net", "SegNet", "DeepLab", "Vision Transformer", "CLIP"
    ],
    "ml_general": [
        "cross-validation", "train/test split", "validation set",
        "benchmark", "baseline", "state-of-the-art", "SOTA"
    ]
}


class EnhancedSemanticSearch(SemanticSearch):
    """
    Enhanced semantic search with keyword-based boosting for domain relevance.
    """
    
    def __init__(
        self,
        es_url: str = "http://localhost:9200",
        index_name: str = "papers_vectors",
        config: Optional[EnhancedSemanticSearchConfig] = None,
        boost_keywords: Optional[Dict[str, List[str]]] = None,
        max_workers: int = 8
    ):
        # Initialize parent class
        if config is None:
            config = EnhancedSemanticSearchConfig()
        
        super().__init__(
            es_url=es_url,
            index_name=index_name,
            config=config,
            max_workers=max_workers
        )
        
        self.enhanced_config = config if isinstance(config, EnhancedSemanticSearchConfig) else EnhancedSemanticSearchConfig()
        self.boost_keywords = boost_keywords or BOOST_KEYWORDS
        
        # Compile regex patterns for efficient matching
        self._compile_boost_patterns()
    
    def _compile_boost_patterns(self):
        """Pre-compile regex patterns for boost keywords"""
        self.boost_patterns = {}
        
        for category, keywords in self.boost_keywords.items():
            patterns = []
            for keyword in keywords:
                # Escape special regex characters and create case-insensitive pattern
                escaped = re.escape(keyword)
                # Use word boundaries for better matching
                pattern = re.compile(r'\b' + escaped + r'\b', re.IGNORECASE)
                patterns.append((keyword, pattern))
            self.boost_patterns[category] = patterns
    
    def _count_keyword_matches(self, text: str, category: str) -> Dict[str, int]:
        """
        Count occurrences of boost keywords in text.
        
        Returns:
            Dict mapping keyword to count
        """
        if not text or category not in self.boost_patterns:
            return {}
        
        matches = {}
        for keyword, pattern in self.boost_patterns[category]:
            count = len(pattern.findall(text))
            if count > 0:
                matches[keyword] = count
        
        return matches
    
    def _calculate_boost_score(
        self,
        title: str,
        abstract: str,
        domain_hints: Optional[List[str]] = None
    ) -> float:
        """
        Calculate boost score based on keyword matches.
        
        Args:
            title: Paper title
            abstract: Paper abstract
            domain_hints: Specific keywords to look for (from query rewriting)
            
        Returns:
            Boost multiplier (1.0 = no boost, >1.0 = boosted)
        """
        if not self.enhanced_config.use_keyword_boosting:
            return 1.0
        
        combined_text = f"{title} {abstract}".lower()
        boost_multiplier = 1.0
        matched_keywords = []
        
        # Check domain hints first (highest priority)
        if domain_hints:
            for hint in domain_hints:
                hint_lower = hint.lower()
                if hint_lower in combined_text:
                    boost_multiplier *= 1.25  # Strong boost for query-specific hints
                    matched_keywords.append(f"hint:{hint}")
        
        # Check dataset keywords
        dataset_matches = {}
        for category in ["nlp_datasets", "cv_datasets"]:
            matches = self._count_keyword_matches(combined_text, category)
            dataset_matches.update(matches)
        
        if len(dataset_matches) >= self.enhanced_config.min_boost_occurrences:
            boost_multiplier *= self.enhanced_config.dataset_boost_factor
            matched_keywords.extend([f"dataset:{k}" for k in dataset_matches.keys()])
        
        # Check metric keywords
        metric_matches = {}
        for category in ["nlp_metrics", "cv_metrics"]:
            matches = self._count_keyword_matches(combined_text, category)
            metric_matches.update(matches)
        
        if len(metric_matches) >= self.enhanced_config.min_boost_occurrences:
            boost_multiplier *= self.enhanced_config.metric_boost_factor
            matched_keywords.extend([f"metric:{k}" for k in metric_matches.keys()])
        
        # Check model keywords
        model_matches = {}
        for category in ["nlp_models", "cv_models"]:
            matches = self._count_keyword_matches(combined_text, category)
            model_matches.update(matches)
        
        if len(model_matches) >= self.enhanced_config.min_boost_occurrences:
            boost_multiplier *= self.enhanced_config.model_boost_factor
            matched_keywords.extend([f"model:{k}" for k in model_matches.keys()])
        
        # Check general ML keywords
        general_matches = self._count_keyword_matches(combined_text, "ml_general")
        if len(general_matches) >= self.enhanced_config.min_boost_occurrences:
            boost_multiplier *= 1.1
            matched_keywords.extend([f"general:{k}" for k in general_matches.keys()])
        
        if matched_keywords:
            logger.debug(f"[EnhancedSemanticSearch] Boost {boost_multiplier:.2f}x - Matched: {', '.join(matched_keywords[:5])}")
        
        return boost_multiplier
    
    def search(
        self,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, str]] = None,
        use_multi_field: bool = True,
        domain_hints: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Enhanced semantic search with keyword boosting.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results
            filters: Search filters
            use_multi_field: Use multiple vector fields
            domain_hints: Domain-specific keywords to boost (from query rewriting)
            
        Returns:
            List of results with boosted scores
        """
        # Get base semantic search results
        results = super().search(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters,
            use_multi_field=use_multi_field
        )
        
        if not self.enhanced_config.use_keyword_boosting:
            return results
        
        # Apply keyword boosting
        boosted_results = []
        for result in results:
            title = result.get("text", "") if result.get("field") == "title" else ""
            abstract = result.get("text", "") if result.get("field") == "abstract" else ""
            
            # For chunks, we might not have title/abstract directly
            if not title and not abstract:
                # Use the text we have
                text = result.get("text", "")
                boost_multiplier = self._calculate_boost_score(text, "", domain_hints)
            else:
                boost_multiplier = self._calculate_boost_score(title, abstract, domain_hints)
            
            # Apply boost to score
            original_score = result.get("score", 0)
            boosted_score = original_score * boost_multiplier
            
            result["original_semantic_score"] = original_score
            result["boost_multiplier"] = boost_multiplier
            result["score"] = boosted_score
            result["source"] = "enhanced_semantic"
            
            boosted_results.append(result)
        
        # Re-sort by boosted score
        boosted_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Log boost statistics
        boosted_count = sum(1 for r in boosted_results if r.get("boost_multiplier", 1.0) > 1.0)
        if boosted_count > 0:
            logger.info(f"[EnhancedSemanticSearch] Applied boosting to {boosted_count}/{len(boosted_results)} results")
        
        return boosted_results
    
    async def search_async(
        self,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, str]] = None,
        use_multi_field: bool = True,
        domain_hints: Optional[List[str]] = None
    ) -> List[Dict]:
        """Async version with keyword boosting"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.search,
            query_embedding,
            top_k,
            filters,
            use_multi_field,
            domain_hints
        )


def demo():
    """Demo the enhanced semantic search"""
    config = EnhancedSemanticSearchConfig(
        top_k=20,
        use_keyword_boosting=True,
        dataset_boost_factor=1.3,
        metric_boost_factor=1.2
    )
    
    searcher = EnhancedSemanticSearch(config=config)
    
    # Mock query embedding (would come from actual embedding model)
    # In practice, this would be generated by sentence-transformers
    print(f"\n{'='*80}")
    print(f"Enhanced Semantic Search Configuration")
    print(f"{'='*80}")
    print(f"Dataset boost: {config.dataset_boost_factor}x")
    print(f"Metric boost: {config.metric_boost_factor}x")
    print(f"Model boost: {config.model_boost_factor}x")
    print(f"\nBoost Keywords:")
    for category, keywords in BOOST_KEYWORDS.items():
        print(f"  {category}: {', '.join(keywords[:5])}...")


if __name__ == "__main__":
    demo()

