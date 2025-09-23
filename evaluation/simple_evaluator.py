"""
Simplified evaluation script for the FindPaper QA Engine
Tests the retriever component with diverse queries and analyzes performance
"""

import asyncio
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import json
import time
from datetime import datetime
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our system components
from app import retrieve_papers_optimized, PaperQuery
from online_team.preprocess.query_processor_enhanced import EnhancedQueryProcessor, QueryProcessorConfig
from online_team.rag.parallel_search import ParallelSearchPipeline, SearchPipelineConfig
from online_team.rag.keyword_search import KeywordSearchConfig
from online_team.rag.semantic_search import SemanticSearchConfig
from online_team.rag.reranker import RerankerConfig
from sentence_transformers import SentenceTransformer
from config import CROSS_ENCODER_MODEL, SEMANTIC_MODEL
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleRetrieverEvaluator:
    """Simple evaluator for testing retriever performance"""
    
    def __init__(self):
        self.initialize_components()
        
    def initialize_components(self):
        """Initialize the search pipeline and models"""
        logger.info("Initializing evaluation components...")
        
        # Initialize search pipeline
        keyword_config = KeywordSearchConfig(
            top_k=50,
            title_boost=5.0,
            abstract_boost=3.0,
            multi_match_boost=2.0
        )
        
        semantic_config = SemanticSearchConfig(
            top_k=50,
            knn_num_candidates=50,
            vector_fields=["title_embedding", "abstract_embedding", "chunks.embedding"]
        )
        
        reranker_config = RerankerConfig(
            top_final=20,
            alpha=1.0,
            beta=1.0,
            use_crossencoder=True,
            crossencoder_model=CROSS_ENCODER_MODEL,
            batch_size=32,
            use_distil=True
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
        
        self.pipeline = ParallelSearchPipeline(
            es_url=os.getenv("ES_HOST", "http://localhost:9200"),
            text_index=os.getenv("ES_INDEX", "papers_text"),
            vector_index=os.getenv("ES_VECTOR_INDEX", "papers_vectors"),
            config=pipeline_config
        )
        
        # Initialize query processor
        query_processor_config = QueryProcessorConfig(
            enable_caching=True,
            cache_ttl=3600,
            enable_fallback=True,
            gemini_timeout=30.0,
            use_regex_fallback=True
        )
        self.query_processor = EnhancedQueryProcessor(config=query_processor_config)
        
        # Initialize embedding model
        self.model = SentenceTransformer(SEMANTIC_MODEL)
        
        logger.info("Components initialized successfully")
        
    def create_test_queries(self) -> List[Dict[str, str]]:
        """Create diverse test queries for evaluation"""
        test_queries = [
            {
                "query": "What are the latest advances in transformer architecture for natural language processing?",
                "category": "technical",
                "expected_keywords": ["transformer", "attention", "NLP", "architecture"]
            },
            {
                "query": "How do large language models handle few-shot learning and in-context learning?",
                "category": "technical",
                "expected_keywords": ["few-shot", "in-context", "learning", "language models"]
            },
            {
                "query": "What are the main challenges in training large-scale neural networks?",
                "category": "technical",
                "expected_keywords": ["training", "neural networks", "challenges", "large-scale"]
            },
            {
                "query": "How does reinforcement learning from human feedback (RLHF) work in language models?",
                "category": "technical",
                "expected_keywords": ["RLHF", "reinforcement learning", "human feedback", "language models"]
            },
            {
                "query": "What are the current approaches to reducing hallucination in large language models?",
                "category": "technical",
                "expected_keywords": ["hallucination", "language models", "reducing", "approaches"]
            },
            {
                "query": "How do vision-language models process and understand multimodal inputs?",
                "category": "technical",
                "expected_keywords": ["vision-language", "multimodal", "transformer", "attention"]
            },
            {
                "query": "What are the key techniques for efficient inference in large language models?",
                "category": "technical",
                "expected_keywords": ["inference", "efficiency", "quantization", "optimization"]
            },
            {
                "query": "How do retrieval-augmented generation (RAG) systems improve language model performance?",
                "category": "technical",
                "expected_keywords": ["RAG", "retrieval", "augmented", "generation"]
            },
            {
                "query": "What are the main evaluation metrics for assessing language model quality?",
                "category": "evaluation",
                "expected_keywords": ["evaluation", "metrics", "BLEU", "ROUGE", "perplexity"]
            },
            {
                "query": "How do contrastive learning methods improve representation learning in NLP?",
                "category": "technical",
                "expected_keywords": ["contrastive learning", "representation", "NLP", "embeddings"]
            }
        ]
        
        return test_queries
        
    async def evaluate_single_query(self, query_data: Dict[str, str]) -> Dict[str, Any]:
        """Evaluate a single query"""
        query = query_data["query"]
        category = query_data["category"]
        expected_keywords = query_data["expected_keywords"]
        
        logger.info(f"Evaluating query: {query[:100]}...")
        start_time = time.time()
        
        try:
            # Step 1: Process query
            processed, raw_content = self.query_processor.process_query(query)
            
            # Step 2: Generate embeddings
            query_embeddings = [
                self.model.encode(query, normalize_embeddings=True).tolist(),
                self.model.encode(processed.rewritten_query or query, normalize_embeddings=True).tolist()
            ]
            
            # Step 3: Convert filters
            filters = {}
            if "year" in processed.search_filters:
                start_year, end_year = processed.search_filters["year"].split("-")
                filters["update_date"] = f"{start_year}-01-01:{end_year}-12-31"
            if "venue" in processed.search_filters:
                filters["venue"] = processed.search_filters["venue"]
            if "fieldsOfStudy" in processed.search_filters:
                filters["fieldsOfStudy"] = processed.search_filters["fieldsOfStudy"]
            
            # Step 4: Run search pipeline
            final_results = await self.pipeline.search_with_reranking(
                query_text=processed.rewritten_query or query,
                query_embeddings=query_embeddings,
                filters=filters,
                top_k=50,
                top_final=20
            )
            
            total_time = time.time() - start_time
            
            # Step 5: Analyze results
            analysis = self._analyze_results(query, expected_keywords, final_results)
            
            return {
                "query": query,
                "category": category,
                "expected_keywords": expected_keywords,
                "rewritten_query": processed.rewritten_query,
                "keyword_query": processed.keyword_query,
                "gemini_filters": processed.search_filters,
                "num_results": len(final_results),
                "total_time": total_time,
                "results": final_results,
                "analysis": analysis,
                "pipeline_info": self.pipeline.get_pipeline_info(),
                "success": True,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error evaluating query: {e}")
            return {
                "query": query,
                "category": category,
                "expected_keywords": expected_keywords,
                "rewritten_query": None,
                "keyword_query": None,
                "gemini_filters": {},
                "num_results": 0,
                "total_time": time.time() - start_time,
                "results": [],
                "analysis": {},
                "pipeline_info": {},
                "success": False,
                "error": str(e)
            }
    
    def _analyze_results(self, query: str, expected_keywords: List[str], results: List[Dict]) -> Dict[str, Any]:
        """Analyze retrieval results"""
        if not results:
            return {
                "keyword_coverage": 0.0,
                "avg_score": 0.0,
                "score_std": 0.0,
                "title_relevance": 0.0,
                "abstract_relevance": 0.0,
                "top_titles": [],
                "score_distribution": {}
            }
        
        # Extract scores
        scores = [r.get("final_score", 0) for r in results]
        avg_score = np.mean(scores)
        score_std = np.std(scores)
        
        # Analyze keyword coverage in titles and abstracts
        all_text = " ".join([r.get("title", "") + " " + r.get("evidence", "") for r in results])
        keyword_coverage = sum(1 for keyword in expected_keywords if keyword.lower() in all_text.lower()) / len(expected_keywords)
        
        # Analyze title relevance
        titles = [r.get("title", "") for r in results]
        title_relevance = sum(1 for title in titles if any(keyword.lower() in title.lower() for keyword in expected_keywords)) / len(titles)
        
        # Analyze abstract relevance
        abstracts = [r.get("evidence", "") for r in results]
        abstract_relevance = sum(1 for abstract in abstracts if any(keyword.lower() in abstract.lower() for keyword in expected_keywords)) / len(abstracts)
        
        # Get top titles
        top_titles = [r.get("title", "") for r in results[:5]]
        
        # Score distribution
        score_ranges = {
            "high (>0.8)": sum(1 for s in scores if s > 0.8),
            "medium (0.5-0.8)": sum(1 for s in scores if 0.5 <= s <= 0.8),
            "low (<0.5)": sum(1 for s in scores if s < 0.5)
        }
        
        return {
            "keyword_coverage": keyword_coverage,
            "avg_score": avg_score,
            "score_std": score_std,
            "title_relevance": title_relevance,
            "abstract_relevance": abstract_relevance,
            "top_titles": top_titles,
            "score_distribution": score_ranges
        }
    
    async def run_evaluation(self) -> List[Dict[str, Any]]:
        """Run complete evaluation on all test queries"""
        logger.info("Starting retriever evaluation...")
        
        test_queries = self.create_test_queries()
        results = []
        
        for i, query_data in enumerate(test_queries):
            logger.info(f"Processing query {i+1}/{len(test_queries)}")
            result = await self.evaluate_single_query(query_data)
            results.append(result)
            
            # Print immediate feedback
            if result["success"]:
                analysis = result["analysis"]
                print(f"Query {i+1}: {result['num_results']} results, "
                      f"avg score: {analysis['avg_score']:.3f}, "
                      f"keyword coverage: {analysis['keyword_coverage']:.2f}, "
                      f"time: {result['total_time']:.2f}s")
            else:
                print(f"Query {i+1}: FAILED - {result['error']}")
        
        return results
    
    def generate_report(self, results: List[Dict[str, Any]]) -> pd.DataFrame:
        """Generate comprehensive evaluation report"""
        logger.info("Generating evaluation report...")
        
        # Convert results to DataFrame
        data = []
        for i, result in enumerate(results):
            if result["success"]:
                analysis = result["analysis"]
                data.append({
                    'query_id': i + 1,
                    'query': result['query'],
                    'category': result['category'],
                    'rewritten_query': result['rewritten_query'],
                    'keyword_query': result['keyword_query'],
                    'num_results': result['num_results'],
                    'total_time': result['total_time'],
                    'keyword_coverage': analysis['keyword_coverage'],
                    'avg_score': analysis['avg_score'],
                    'score_std': analysis['score_std'],
                    'title_relevance': analysis['title_relevance'],
                    'abstract_relevance': analysis['abstract_relevance'],
                    'success': True,
                    'error': None
                })
            else:
                data.append({
                    'query_id': i + 1,
                    'query': result['query'],
                    'category': result['category'],
                    'rewritten_query': None,
                    'keyword_query': None,
                    'num_results': 0,
                    'total_time': result['total_time'],
                    'keyword_coverage': 0.0,
                    'avg_score': 0.0,
                    'score_std': 0.0,
                    'title_relevance': 0.0,
                    'abstract_relevance': 0.0,
                    'success': False,
                    'error': result['error']
                })
        
        df = pd.DataFrame(data)
        
        # Calculate summary statistics
        successful_results = df[df['success'] == True]
        
        if len(successful_results) > 0:
            summary_stats = {
                'metric': [
                    'avg_num_results', 'avg_time', 'avg_keyword_coverage',
                    'avg_score', 'avg_title_relevance', 'avg_abstract_relevance'
                ],
                'value': [
                    successful_results['num_results'].mean(),
                    successful_results['total_time'].mean(),
                    successful_results['keyword_coverage'].mean(),
                    successful_results['avg_score'].mean(),
                    successful_results['title_relevance'].mean(),
                    successful_results['abstract_relevance'].mean()
                ]
            }
            
            summary_df = pd.DataFrame(summary_stats)
        else:
            summary_df = pd.DataFrame({'metric': ['no_successful_queries'], 'value': [0]})
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        detailed_file = f"evaluation_results_{timestamp}.csv"
        summary_file = f"evaluation_summary_{timestamp}.csv"
        
        df.to_csv(detailed_file, index=False)
        summary_df.to_csv(summary_file, index=False)
        
        logger.info(f"Detailed results saved to: {detailed_file}")
        logger.info(f"Summary statistics saved to: {summary_file}")
        
        # Print summary
        print("\n" + "="*80)
        print("RETRIEVER EVALUATION SUMMARY")
        print("="*80)
        print(f"Total queries: {len(results)}")
        print(f"Successful queries: {len(successful_results)}")
        print(f"Failed queries: {len(results) - len(successful_results)}")
        
        if len(successful_results) > 0:
            print(f"\nAverage results per query: {successful_results['num_results'].mean():.1f}")
            print(f"Average time per query: {successful_results['total_time'].mean():.2f}s")
            print(f"Average keyword coverage: {successful_results['keyword_coverage'].mean():.2f}")
            print(f"Average relevance score: {successful_results['avg_score'].mean():.3f}")
            print(f"Average title relevance: {successful_results['title_relevance'].mean():.2f}")
            print(f"Average abstract relevance: {successful_results['abstract_relevance'].mean():.2f}")
            
            print("\nSummary Statistics:")
            print(summary_df.to_string(index=False))
        
        return df, summary_df

async def main():
    """Main evaluation function"""
    evaluator = SimpleRetrieverEvaluator()
    
    # Run evaluation
    results = await evaluator.run_evaluation()
    
    # Generate report
    detailed_df, summary_df = evaluator.generate_report(results)
    
    return detailed_df, summary_df

if __name__ == "__main__":
    asyncio.run(main())

