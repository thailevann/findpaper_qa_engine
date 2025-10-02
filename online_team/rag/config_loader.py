"""
Configuration Loader for Advanced Search Pipeline

Loads configuration from YAML file and creates appropriate config objects.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Optional

from online_team.rag.enhanced_keyword_search import EnhancedKeywordSearchConfig
from online_team.rag.enhanced_semantic_search import EnhancedSemanticSearchConfig
from online_team.rag.enhanced_reranker import EnhancedRerankerConfig
from online_team.rag.seed_booster import SeedPaperConfig
from online_team.rag.advanced_search_pipeline import AdvancedSearchPipelineConfig

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ConfigLoader:
    """Load and manage advanced search pipeline configuration"""
    
    def __init__(self, config_path: str = "config_advanced_search.yaml"):
        """
        Initialize config loader.
        
        Args:
            config_path: Path to YAML config file
        """
        self.config_path = Path(config_path)
        self.config_data = None
        self.load_config()
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = yaml.safe_load(f)
            logger.info(f"[ConfigLoader] Loaded configuration from {self.config_path}")
        except FileNotFoundError:
            logger.warning(f"[ConfigLoader] Config file not found: {self.config_path}, using defaults")
            self.config_data = {}
        except Exception as e:
            logger.error(f"[ConfigLoader] Error loading config: {e}, using defaults")
            self.config_data = {}
    
    def get_keyword_config(self) -> EnhancedKeywordSearchConfig:
        """Get keyword search configuration"""
        kw_config = self.config_data.get("keyword_search", {})
        
        return EnhancedKeywordSearchConfig(
            top_k=kw_config.get("top_k", 50),
            title_boost=kw_config.get("title_boost", 5.0),
            abstract_boost=kw_config.get("abstract_boost", 3.0),
            multi_match_boost=kw_config.get("multi_match_boost", 1.0),
            use_query_expansion=kw_config.get("use_query_expansion", True),
            use_negative_filtering=kw_config.get("use_negative_filtering", True),
            aggregation_strategy=kw_config.get("aggregation_strategy", "union"),
            max_queries_to_execute=kw_config.get("max_queries_to_execute", 5)
        )
    
    def get_semantic_config(self) -> EnhancedSemanticSearchConfig:
        """Get semantic search configuration"""
        sem_config = self.config_data.get("semantic_search", {})
        
        return EnhancedSemanticSearchConfig(
            top_k=sem_config.get("top_k", 50),
            knn_num_candidates=sem_config.get("knn_num_candidates", 50),
            vector_fields=sem_config.get("vector_fields", [
                "title_embedding",
                "abstract_embedding",
                "chunks.embedding"
            ]),
            use_keyword_boosting=sem_config.get("use_keyword_boosting", True),
            dataset_boost_factor=sem_config.get("dataset_boost_factor", 1.3),
            metric_boost_factor=sem_config.get("metric_boost_factor", 1.2),
            model_boost_factor=sem_config.get("model_boost_factor", 1.15),
            min_boost_occurrences=sem_config.get("min_boost_occurrences", 1)
        )
    
    def get_reranker_config(self) -> EnhancedRerankerConfig:
        """Get reranker configuration"""
        rerank_config = self.config_data.get("reranker", {})
        
        return EnhancedRerankerConfig(
            top_final=rerank_config.get("top_final", 20),
            crossencoder_model=rerank_config.get("crossencoder_model"),
            batch_size=rerank_config.get("batch_size", 32),
            use_distil=rerank_config.get("use_distil", False),
            use_crossencoder=rerank_config.get("use_crossencoder", True),
            max_candidates_for_rerank=rerank_config.get("max_candidates_for_rerank", 300),
            use_constraint_checks=rerank_config.get("use_constraint_checks", True),
            min_keyword_occurrences=rerank_config.get("min_keyword_occurrences", 2),
            use_content_boosting=rerank_config.get("use_content_boosting", True),
            boost_if_contains=rerank_config.get("boost_if_contains", []),
            downrank_if_contains=rerank_config.get("downrank_if_contains", []),
            crossencoder_weight=rerank_config.get("crossencoder_weight", 0.7),
            constraint_weight=rerank_config.get("constraint_weight", 0.15),
            content_boost_weight=rerank_config.get("content_boost_weight", 0.15)
        )
    
    def get_seed_config(self) -> SeedPaperConfig:
        """Get seed paper booster configuration"""
        seed_config = self.config_data.get("seed_booster", {})
        
        return SeedPaperConfig(
            boost_factor=seed_config.get("boost_factor", 1.5),
            use_seed_boosting=seed_config.get("use_seed_boosting", True),
            seed_papers=seed_config.get("custom_seeds", {})
        )
    
    def get_pipeline_config(self) -> AdvancedSearchPipelineConfig:
        """Get complete pipeline configuration"""
        pipeline_config = self.config_data.get("pipeline", {})
        
        return AdvancedSearchPipelineConfig(
            keyword_config=self.get_keyword_config(),
            semantic_config=self.get_semantic_config(),
            reranker_config=self.get_reranker_config(),
            seed_config=self.get_seed_config(),
            use_parallel_search=pipeline_config.get("use_parallel_search", True),
            use_query_rewriting=pipeline_config.get("use_query_rewriting", True),
            use_seed_boosting=pipeline_config.get("use_seed_boosting", True),
            search_timeout=pipeline_config.get("search_timeout", 30.0),
            rerank_timeout=pipeline_config.get("rerank_timeout", 60.0),
            max_results_before_rerank=pipeline_config.get("max_results_before_rerank", 150)
        )
    
    def get_elasticsearch_config(self) -> Dict:
        """Get Elasticsearch configuration"""
        es_config = self.config_data.get("elasticsearch", {})
        
        return {
            "host": es_config.get("host", "http://localhost:9200"),
            "text_index": es_config.get("text_index", "papers_text"),
            "vector_index": es_config.get("vector_index", "papers_vectors"),
            "request_timeout": es_config.get("request_timeout", 120)
        }
    
    def get_domain_preset(self, domain: str) -> Optional[Dict]:
        """
        Get domain-specific preset configuration.
        
        Args:
            domain: Domain name (e.g., "nlp_summarization")
            
        Returns:
            Dict with boost_terms and exclude_terms, or None if not found
        """
        presets = self.config_data.get("domain_presets", {})
        return presets.get(domain)
    
    def apply_domain_preset(self, domain: str, reranker_config: EnhancedRerankerConfig) -> EnhancedRerankerConfig:
        """
        Apply domain preset to reranker config.
        
        Args:
            domain: Domain name
            reranker_config: Existing reranker config to modify
            
        Returns:
            Updated reranker config
        """
        preset = self.get_domain_preset(domain)
        
        if preset:
            # Merge boost terms
            existing_boosts = set(reranker_config.boost_if_contains)
            preset_boosts = set(preset.get("boost_terms", []))
            reranker_config.boost_if_contains = list(existing_boosts | preset_boosts)
            
            # Merge exclude terms
            existing_excludes = set(reranker_config.downrank_if_contains)
            preset_excludes = set(preset.get("exclude_terms", []))
            reranker_config.downrank_if_contains = list(existing_excludes | preset_excludes)
            
            logger.info(f"[ConfigLoader] Applied domain preset: {domain}")
        
        return reranker_config


def demo():
    """Demo the config loader"""
    loader = ConfigLoader()
    
    print(f"\n{'='*80}")
    print(f"Configuration Loader Demo")
    print(f"{'='*80}")
    
    # Get all configs
    keyword_config = loader.get_keyword_config()
    semantic_config = loader.get_semantic_config()
    reranker_config = loader.get_reranker_config()
    seed_config = loader.get_seed_config()
    pipeline_config = loader.get_pipeline_config()
    es_config = loader.get_elasticsearch_config()
    
    print(f"\nKeyword Search Config:")
    print(f"  top_k: {keyword_config.top_k}")
    print(f"  use_query_expansion: {keyword_config.use_query_expansion}")
    print(f"  use_negative_filtering: {keyword_config.use_negative_filtering}")
    
    print(f"\nSemantic Search Config:")
    print(f"  top_k: {semantic_config.top_k}")
    print(f"  use_keyword_boosting: {semantic_config.use_keyword_boosting}")
    print(f"  dataset_boost_factor: {semantic_config.dataset_boost_factor}")
    
    print(f"\nReranker Config:")
    print(f"  top_final: {reranker_config.top_final}")
    print(f"  use_constraint_checks: {reranker_config.use_constraint_checks}")
    print(f"  min_keyword_occurrences: {reranker_config.min_keyword_occurrences}")
    print(f"  boost_if_contains: {len(reranker_config.boost_if_contains)} terms")
    print(f"  downrank_if_contains: {len(reranker_config.downrank_if_contains)} terms")
    
    print(f"\nSeed Booster Config:")
    print(f"  boost_factor: {seed_config.boost_factor}")
    print(f"  use_seed_boosting: {seed_config.use_seed_boosting}")
    
    print(f"\nPipeline Config:")
    print(f"  use_parallel_search: {pipeline_config.use_parallel_search}")
    print(f"  use_query_rewriting: {pipeline_config.use_query_rewriting}")
    print(f"  use_seed_boosting: {pipeline_config.use_seed_boosting}")
    
    print(f"\nElasticsearch Config:")
    print(f"  host: {es_config['host']}")
    print(f"  text_index: {es_config['text_index']}")
    print(f"  vector_index: {es_config['vector_index']}")
    
    # Test domain preset
    print(f"\n{'='*80}")
    print(f"Testing Domain Presets")
    print(f"{'='*80}")
    
    nlp_preset = loader.get_domain_preset("nlp_summarization")
    if nlp_preset:
        print(f"\nNLP Summarization Preset:")
        print(f"  Boost terms: {', '.join(nlp_preset.get('boost_terms', [])[:5])}...")
        print(f"  Exclude terms: {', '.join(nlp_preset.get('exclude_terms', []))}")


if __name__ == "__main__":
    demo()

