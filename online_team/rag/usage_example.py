"""
Usage example for the optimized paper search pipeline
"""
import asyncio
from typing import List, Dict, Any

from .parallel_search import ParallelSearchPipeline, SearchPipelineConfig
from .keyword_search import KeywordSearchConfig
from .semantic_search import SemanticSearchConfig
from .reranker import RerankerConfig
from ..preprocess.query_processor_enhanced import EnhancedQueryProcessor, QueryProcessorConfig


async def main():
    """Example usage of the optimized search pipeline"""
    
    # Configuration for different components
    keyword_config = KeywordSearchConfig(
        top_k=50,
        title_boost=5.0,
        abstract_boost=3.0,
        multi_match_boost=2.0
    )
    
    semantic_config = SemanticSearchConfig(
        top_k=50,
        knn_num_candidates=100,
        vector_fields=["title_embedding", "abstract_embedding", "chunks.embedding"]
    )
    
    reranker_config = RerankerConfig(
        top_final=20,
        alpha=1.0,  # Weight for semantic scores
        beta=1.0,   # Weight for keyword scores
        use_crossencoder=True,
        crossencoder_model="cross-encoder/ms-marco-MiniLM-L-6-v2",  # Smaller model for speed
        batch_size=32,
        use_distil=True  # Use DistilCrossEncoder for faster inference
    )
    
    pipeline_config = SearchPipelineConfig(
        keyword_config=keyword_config,
        semantic_config=semantic_config,
        reranker_config=reranker_config,
        use_parallel_search=True,
        use_multi_field_semantic=True,
        enable_reranking=True,
        search_timeout=30.0,
        rerank_timeout=60.0
    )
    
    # Initialize the pipeline
    pipeline = ParallelSearchPipeline(
        es_url="http://localhost:9200",
        text_index="papers_text",
        vector_index="papers_vectors",
        config=pipeline_config
    )
    
    # Initialize query processor
    query_processor_config = QueryProcessorConfig(
        enable_caching=True,
        cache_ttl=3600,  # 1 hour
        enable_fallback=True,
        gemini_timeout=30.0,
        use_regex_fallback=True
    )
    
    query_processor = EnhancedQueryProcessor(config=query_processor_config)
    
    # Example query
    query = "Deep learning papers about transformers from 2020 to 2023 in NeurIPS"
    
    print(f"Processing query: {query}")
    
    # Step 1: Process query
    processed_query, raw_content = query_processor.process_query(query)
    print(f"Rewritten query: {processed_query.rewritten_query}")
    print(f"Keyword query: {processed_query.keyword_query}")
    print(f"Filters: {processed_query.search_filters}")
    
    # Step 2: Generate embeddings (you would use your embedding model here)
    # This is a placeholder - replace with your actual embedding generation
    query_embeddings = [
        [0.1] * 384,  # Placeholder embedding for title
        [0.2] * 384,  # Placeholder embedding for abstract
    ]
    
    # Step 3: Run the search pipeline
    results = await pipeline.search_with_reranking(
        query_text=processed_query.rewritten_query,
        query_embeddings=query_embeddings,
        filters=processed_query.search_filters,
        top_k=50,
        top_final=20
    )
    
    # Step 4: Display results
    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   Paper ID: {result['paper_id']}")
        print(f"   Score: {result['final_score']:.4f}")
        print(f"   Evidence: {result['evidence'][:100]}...")
        print()
    
    # Get pipeline information
    pipeline_info = pipeline.get_pipeline_info()
    print("Pipeline Configuration:")
    for key, value in pipeline_info.items():
        print(f"  {key}: {value}")
    
    # Get query processor information
    processor_info = query_processor.get_processor_info()
    print("\nQuery Processor Configuration:")
    for key, value in processor_info.items():
        print(f"  {key}: {value}")


def example_without_reranking():
    """Example using the pipeline without CrossEncoder reranking for maximum speed"""
    
    # Fast configuration without CrossEncoder
    fast_config = SearchPipelineConfig(
        reranker_config=RerankerConfig(
            use_crossencoder=False,  # Disable CrossEncoder for speed
            top_final=20
        ),
        use_parallel_search=True,
        enable_reranking=False  # Skip reranking entirely
    )
    
    pipeline = ParallelSearchPipeline(config=fast_config)
    
    # This would be much faster but with lower quality results
    print("Fast configuration without CrossEncoder reranking")


def example_custom_configuration():
    """Example with custom configuration for specific use cases"""
    
    # High-quality configuration
    high_quality_config = SearchPipelineConfig(
        keyword_config=KeywordSearchConfig(top_k=100),
        semantic_config=SemanticSearchConfig(top_k=100, knn_num_candidates=200),
        reranker_config=RerankerConfig(
            top_final=50,
            use_crossencoder=True,
            crossencoder_model="cross-encoder/ms-marco-MiniLM-L-12-v2",  # Larger model
            batch_size=16
        ),
        search_timeout=60.0,
        rerank_timeout=120.0
    )
    
    # Balanced configuration
    balanced_config = SearchPipelineConfig(
        keyword_config=KeywordSearchConfig(top_k=50),
        semantic_config=SemanticSearchConfig(top_k=50),
        reranker_config=RerankerConfig(
            top_final=20,
            use_crossencoder=True,
            use_distil=True,  # Use smaller model
            batch_size=32
        )
    )
    
    # Speed-optimized configuration
    speed_config = SearchPipelineConfig(
        keyword_config=KeywordSearchConfig(top_k=30),
        semantic_config=SemanticSearchConfig(top_k=30, knn_num_candidates=50),
        reranker_config=RerankerConfig(
            top_final=10,
            use_crossencoder=False  # No CrossEncoder
        ),
        search_timeout=15.0
    )
    
    print("Custom configurations created for different use cases")


if __name__ == "__main__":
    # Run the main example
    asyncio.run(main())
    
    # Show other examples
    example_without_reranking()
    example_custom_configuration()


