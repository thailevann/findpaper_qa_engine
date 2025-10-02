"""
Seed Paper Boosting Module

This module provides functionality to boost influential/seed papers in search results.
Helps ensure that well-known foundational papers are not missed in retrieval.
"""

import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class SeedPaperConfig:
    """Configuration for seed paper boosting"""
    boost_factor: float = 1.5  # Multiplier for seed papers
    use_seed_boosting: bool = True
    seed_papers: Dict[str, List[str]] = field(default_factory=dict)
    # Map of domain -> list of paper IDs/identifiers


# Predefined influential papers by domain
INFLUENTIAL_PAPERS = {
    "nlp_summarization": {
        # Paper IDs and identifiers
        "arxiv_ids": [
            "1704.04368",  # Pointer-Generator Network
            "1912.08777",  # BART
            "1910.13461",  # PEGASUS
            "2004.04906",  # LED (Longformer Encoder-Decoder)
            "1509.00685",  # SummaRuNNer
            "1704.02971",  # TextRank variations
        ],
        "doi": [
            "10.1016/j.ipm.2016.09.005",  # Automatic text summarization survey
            "10.1162/tacl_a_00373",  # Survey on neural summarization
        ],
        "keywords": [
            # Title keywords that identify influential papers
            "Get To The Point: Summarization with Pointer-Generator",
            "BART: Denoising Sequence-to-Sequence",
            "PEGASUS: Pre-training with Extracted Gap-sentences",
            "Longformer: The Long-Document Transformer",
            "SummaRuNNer: A Recurrent Neural Network",
            "Neural Abstractive Text Summarization"
        ]
    },
    "computer_vision": {
        "arxiv_ids": [
            "1512.03385",  # ResNet
            "1506.01497",  # Faster R-CNN
            "1506.02640",  # YOLO
            "1703.06870",  # Mask R-CNN
            "2010.11929",  # Vision Transformer
        ],
        "keywords": [
            "Deep Residual Learning for Image Recognition",
            "Faster R-CNN: Towards Real-Time Object Detection",
            "You Only Look Once: Unified, Real-Time Object Detection",
            "Mask R-CNN",
            "An Image is Worth 16x16 Words"
        ]
    },
    "transformers": {
        "arxiv_ids": [
            "1706.03762",  # Attention Is All You Need
            "1810.04805",  # BERT
            "2005.14165",  # GPT-3
            "1910.10683",  # T5
        ],
        "keywords": [
            "Attention Is All You Need",
            "BERT: Pre-training of Deep Bidirectional Transformers",
            "Language Models are Few-Shot Learners",
            "Exploring the Limits of Transfer Learning with T5"
        ]
    }
}


class SeedPaperBooster:
    """
    Boost results that match known influential/seed papers.
    """
    
    def __init__(
        self,
        config: Optional[SeedPaperConfig] = None,
        custom_seeds: Optional[Dict[str, Dict[str, List[str]]]] = None
    ):
        """
        Initialize seed paper booster.
        
        Args:
            config: Configuration for boosting behavior
            custom_seeds: Custom seed papers to add (same structure as INFLUENTIAL_PAPERS)
        """
        self.config = config or SeedPaperConfig()
        
        # Merge predefined and custom seed papers
        self.seed_papers = INFLUENTIAL_PAPERS.copy()
        if custom_seeds:
            for domain, seeds in custom_seeds.items():
                if domain in self.seed_papers:
                    # Merge with existing
                    for key, values in seeds.items():
                        if key in self.seed_papers[domain]:
                            self.seed_papers[domain][key].extend(values)
                        else:
                            self.seed_papers[domain][key] = values
                else:
                    self.seed_papers[domain] = seeds
        
        # Build lookup sets for fast matching
        self._build_lookup_sets()
    
    def _build_lookup_sets(self):
        """Pre-build sets for fast lookup"""
        self.arxiv_lookup = set()
        self.doi_lookup = set()
        self.keyword_lookup = set()
        
        for domain, seeds in self.seed_papers.items():
            # ArXiv IDs
            if "arxiv_ids" in seeds:
                self.arxiv_lookup.update(seeds["arxiv_ids"])
            
            # DOIs
            if "doi" in seeds:
                self.doi_lookup.update(seeds["doi"])
            
            # Title keywords (lowercase for matching)
            if "keywords" in seeds:
                self.keyword_lookup.update(k.lower() for k in seeds["keywords"])
        
        logger.info(f"[SeedPaperBooster] Loaded {len(self.arxiv_lookup)} arXiv IDs, "
                   f"{len(self.doi_lookup)} DOIs, {len(self.keyword_lookup)} title keywords")
    
    def _extract_arxiv_id(self, paper_id: str) -> Optional[str]:
        """Extract arXiv ID from paper_id string"""
        # Handle formats like "arXiv:1704.04368", "arxiv:1704.04368v2", "1704.04368"
        import re
        
        # Try pattern: arXiv:XXXX.XXXXX or arXiv:XXXX.XXXXXvN
        match = re.search(r'arxiv:?(\d{4}\.\d{4,5})', paper_id, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Try pattern: just XXXX.XXXXX
        match = re.search(r'\b(\d{4}\.\d{4,5})\b', paper_id)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_doi(self, paper_id: str) -> Optional[str]:
        """Extract DOI from paper_id string"""
        import re
        
        # Try pattern: doi:XX.XXXX/...
        match = re.search(r'doi:?(10\.\d+/[^\s]+)', paper_id, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def _is_seed_paper(
        self,
        paper_id: str,
        title: str,
        abstract: str = ""
    ) -> bool:
        """
        Check if a paper matches any seed paper criteria.
        
        Args:
            paper_id: Paper ID (may contain arXiv ID, DOI, etc.)
            title: Paper title
            abstract: Paper abstract (optional)
            
        Returns:
            True if matches seed criteria
        """
        if not self.config.use_seed_boosting:
            return False
        
        # Check arXiv ID
        arxiv_id = self._extract_arxiv_id(paper_id)
        if arxiv_id and arxiv_id in self.arxiv_lookup:
            logger.debug(f"[SeedPaperBooster] Matched seed arXiv ID: {arxiv_id}")
            return True
        
        # Check DOI
        doi = self._extract_doi(paper_id)
        if doi and doi in self.doi_lookup:
            logger.debug(f"[SeedPaperBooster] Matched seed DOI: {doi}")
            return True
        
        # Check title keywords
        title_lower = title.lower()
        for keyword in self.keyword_lookup:
            if keyword in title_lower:
                logger.debug(f"[SeedPaperBooster] Matched seed title keyword: {keyword}")
                return True
        
        return False
    
    def boost_results(
        self,
        results: List[Dict],
        boost_factor: Optional[float] = None
    ) -> List[Dict]:
        """
        Apply seed paper boosting to results.
        
        Args:
            results: List of search results
            boost_factor: Override config boost factor
            
        Returns:
            Results with boosted scores for seed papers
        """
        if not self.config.use_seed_boosting:
            return results
        
        boost_factor = boost_factor or self.config.boost_factor
        boosted_count = 0
        
        for result in results:
            paper_id = result.get("paper_id", "")
            title = result.get("title", "")
            abstract = result.get("abstract", "")
            
            if self._is_seed_paper(paper_id, title, abstract):
                # Apply boost
                original_score = result.get("final_score") or result.get("score", 0)
                boosted_score = original_score * boost_factor
                
                result["seed_paper"] = True
                result["original_score_before_seed"] = original_score
                result["final_score"] = boosted_score
                result["score"] = boosted_score
                
                boosted_count += 1
                logger.debug(f"[SeedPaperBooster] Boosted paper {paper_id}: {original_score:.4f} -> {boosted_score:.4f}")
        
        if boosted_count > 0:
            logger.info(f"[SeedPaperBooster] Applied seed boosting to {boosted_count}/{len(results)} papers")
            
            # Re-sort by updated scores
            results.sort(key=lambda x: x.get("final_score", x.get("score", 0)), reverse=True)
        
        return results
    
    def add_seed_papers(
        self,
        domain: str,
        arxiv_ids: Optional[List[str]] = None,
        dois: Optional[List[str]] = None,
        title_keywords: Optional[List[str]] = None
    ):
        """
        Dynamically add seed papers to the booster.
        
        Args:
            domain: Domain name (e.g., "nlp_summarization")
            arxiv_ids: List of arXiv IDs to add
            dois: List of DOIs to add
            title_keywords: List of title keywords to add
        """
        if domain not in self.seed_papers:
            self.seed_papers[domain] = {}
        
        if arxiv_ids:
            if "arxiv_ids" not in self.seed_papers[domain]:
                self.seed_papers[domain]["arxiv_ids"] = []
            self.seed_papers[domain]["arxiv_ids"].extend(arxiv_ids)
            self.arxiv_lookup.update(arxiv_ids)
        
        if dois:
            if "doi" not in self.seed_papers[domain]:
                self.seed_papers[domain]["doi"] = []
            self.seed_papers[domain]["doi"].extend(dois)
            self.doi_lookup.update(dois)
        
        if title_keywords:
            if "keywords" not in self.seed_papers[domain]:
                self.seed_papers[domain]["keywords"] = []
            self.seed_papers[domain]["keywords"].extend(title_keywords)
            self.keyword_lookup.update(k.lower() for k in title_keywords)
        
        logger.info(f"[SeedPaperBooster] Added seed papers to domain '{domain}'")
    
    def get_seed_paper_info(self) -> Dict:
        """Get information about loaded seed papers"""
        info = {
            "total_arxiv_ids": len(self.arxiv_lookup),
            "total_dois": len(self.doi_lookup),
            "total_keywords": len(self.keyword_lookup),
            "domains": list(self.seed_papers.keys()),
            "boost_factor": self.config.boost_factor,
            "enabled": self.config.use_seed_boosting
        }
        return info


def demo():
    """Demo the seed paper booster"""
    booster = SeedPaperBooster()
    
    print(f"\n{'='*80}")
    print(f"Seed Paper Booster")
    print(f"{'='*80}")
    
    info = booster.get_seed_paper_info()
    print(f"\nConfiguration:")
    print(f"  Enabled: {info['enabled']}")
    print(f"  Boost factor: {info['boost_factor']}x")
    print(f"  Total arXiv IDs: {info['total_arxiv_ids']}")
    print(f"  Total DOIs: {info['total_dois']}")
    print(f"  Total title keywords: {info['total_keywords']}")
    print(f"\nDomains: {', '.join(info['domains'])}")
    
    print(f"\nSample seed papers (NLP Summarization):")
    nlp_seeds = INFLUENTIAL_PAPERS.get("nlp_summarization", {})
    if "arxiv_ids" in nlp_seeds:
        print(f"  arXiv IDs: {', '.join(nlp_seeds['arxiv_ids'][:3])}...")
    if "keywords" in nlp_seeds:
        print(f"  Keywords: {nlp_seeds['keywords'][0]}")
    
    # Test matching
    print(f"\n{'='*80}")
    print(f"Testing seed paper matching")
    print(f"{'='*80}")
    
    test_cases = [
        ("arXiv:1704.04368", "Some title about summarization", True),
        ("random_id_12345", "BART: Denoising Sequence-to-Sequence Pre-training", True),
        ("random_id_67890", "Some random paper", False)
    ]
    
    for paper_id, title, expected in test_cases:
        is_seed = booster._is_seed_paper(paper_id, title)
        status = "✓" if is_seed == expected else "✗"
        print(f"{status} Paper: {title[:50]}... | Seed: {is_seed} (expected: {expected})")


if __name__ == "__main__":
    demo()

