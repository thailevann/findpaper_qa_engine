"""
RAGAS-based evaluation system for the FindPaper QA Engine
Evaluates retriever performance and end-to-end system quality
"""

import asyncio
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import json
import time
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    ContextRelevance,
    answer_correctness
)
from ragas.dataset import Dataset
from ragas.testset import TestsetGenerator
from ragas.llms import OpenAI

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

@dataclass
class EvaluationConfig:
    """Configuration for RAGAS evaluation"""
    num_queries: int = 10
    retrieval_top_k: int = 50
    final_top_k: int = 20
    use_crossencoder: bool = True
    enable_reranking: bool = True
    parallel_search: bool = True
    openai_model: str = "gpt-4o-mini"
    evaluation_timeout: float = 300.0  # 5 minutes per query
    save_intermediate_results: bool = True
    output_dir: str = "evaluation_results"

@dataclass
class QueryResult:
    """Result from a single query evaluation"""
    query: str
    ground_truth: str
    retrieved_documents: List[str]
    answer: str
    context_precision: float
    context_recall: float
    ContextRelevance: float
    answer_relevancy: float
    faithfulness: float
    answer_correctness: float
    retrieval_time: float
    total_time: float
    num_retrieved: int
    pipeline_info: Dict[str, Any]
    error_message: Optional[str] = None

class FindPaperRAGASEvaluator:
    """RAGAS evaluator for the FindPaper QA Engine"""
    
    def __init__(self, config: EvaluationConfig):
        self.config = config
        self.setup_directories()
        self.initialize_components()
        
    def setup_directories(self):
        """Create output directories"""
        os.makedirs(self.config.output_dir, exist_ok=True)
        os.makedirs(f"{self.config.output_dir}/intermediate", exist_ok=True)
        
    def initialize_components(self):
        """Initialize the search pipeline and models"""
        logger.info("Initializing evaluation components...")
        
        # Initialize search pipeline
        keyword_config = KeywordSearchConfig(
            top_k=self.config.retrieval_top_k,
            title_boost=5.0,
            abstract_boost=3.0,
            multi_match_boost=2.0
        )
        
        semantic_config = SemanticSearchConfig(
            top_k=self.config.retrieval_top_k,
            knn_num_candidates=self.config.retrieval_top_k,
            vector_fields=["title_embedding", "abstract_embedding", "chunks.embedding"]
        )
        
        reranker_config = RerankerConfig(
            top_final=self.config.final_top_k,
            alpha=1.0,
            beta=1.0,
            use_crossencoder=self.config.use_crossencoder,
            crossencoder_model=CROSS_ENCODER_MODEL,
            batch_size=32,
            use_distil=True
        )
        
        pipeline_config = SearchPipelineConfig(
            keyword_config=keyword_config,
            semantic_config=semantic_config,
            reranker_config=reranker_config,
            use_parallel_search=self.config.parallel_search,
            use_multi_field_semantic=True,
            enable_reranking=self.config.enable_reranking,
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
        
        # Initialize OpenAI for RAGAS
        self.openai_llm = OpenAI(model=self.config.openai_model)
        
        logger.info("Components initialized successfully")
        
    def create_test_queries(self) -> List[Dict[str, str]]:
        """Create diverse test queries for evaluation"""
        test_queries = [
            {
                "query": "What are the latest advances in transformer architecture for natural language processing?",
                "ground_truth": "Recent advances in transformer architecture include innovations like attention mechanisms, positional encoding improvements, and efficiency optimizations for NLP tasks."
            },
            {
                "query": "How do large language models handle few-shot learning and in-context learning?",
                "ground_truth": "Large language models demonstrate few-shot learning capabilities through in-context learning, where they can adapt to new tasks by providing examples in the input context."
            },
            {
                "query": "What are the main challenges in training large-scale neural networks?",
                "ground_truth": "Main challenges include computational resources, memory constraints, gradient instability, and the need for distributed training strategies."
            },
            {
                "query": "How does reinforcement learning from human feedback (RLHF) work in language models?",
                "ground_truth": "RLHF involves training language models using human preferences through reinforcement learning, typically using techniques like PPO to align model outputs with human values."
            },
            {
                "query": "What are the current approaches to reducing hallucination in large language models?",
                "ground_truth": "Approaches include training on high-quality data, using retrieval-augmented generation, implementing fact-checking mechanisms, and fine-tuning with human feedback."
            },
            {
                "query": "How do vision-language models process and understand multimodal inputs?",
                "ground_truth": "Vision-language models use transformer architectures with specialized encoders for images and text, employing cross-modal attention mechanisms to understand relationships between visual and textual information."
            },
            {
                "query": "What are the key techniques for efficient inference in large language models?",
                "ground_truth": "Key techniques include model quantization, pruning, knowledge distillation, and architectural optimizations like sparse attention patterns."
            },
            {
                "query": "How do retrieval-augmented generation (RAG) systems improve language model performance?",
                "ground_truth": "RAG systems enhance language models by retrieving relevant information from external knowledge bases and incorporating it into the generation process, improving factual accuracy and reducing hallucination."
            },
            {
                "query": "What are the main evaluation metrics for assessing language model quality?",
                "ground_truth": "Key metrics include perplexity, BLEU, ROUGE, BERTScore, and human evaluation metrics like fluency, coherence, and factual accuracy."
            },
            {
                "query": "How do contrastive learning methods improve representation learning in NLP?",
                "ground_truth": "Contrastive learning methods train models to distinguish between positive and negative pairs, improving the quality of learned representations by pulling similar examples together and pushing dissimilar ones apart."
            }
        ]
        
        return test_queries[:self.config.num_queries]
        
    async def evaluate_single_query(self, query_data: Dict[str, str]) -> QueryResult:
        """Evaluate a single query using RAGAS metrics"""
        query = query_data["query"]
        ground_truth = query_data["ground_truth"]
        
        logger.info(f"Evaluating query: {query[:100]}...")
        start_time = time.time()
        
        try:
            # Step 1: Retrieve documents using our system
            retrieval_start = time.time()
            
            # Process query
            processed, raw_content = self.query_processor.process_query(query)
            
            # Generate embeddings
            query_embeddings = [
                self.model.encode(query, normalize_embeddings=True).tolist(),
                self.model.encode(processed.rewritten_query or query, normalize_embeddings=True).tolist()
            ]
            
            # Convert filters
            filters = {}
            if "year" in processed.search_filters:
                start_year, end_year = processed.search_filters["year"].split("-")
                filters["update_date"] = f"{start_year}-01-01:{end_year}-12-31"
            if "venue" in processed.search_filters:
                filters["venue"] = processed.search_filters["venue"]
            if "fieldsOfStudy" in processed.search_filters:
                filters["fieldsOfStudy"] = processed.search_filters["fieldsOfStudy"]
            
            # Run search pipeline
            final_results = await self.pipeline.search_with_reranking(
                query_text=processed.rewritten_query or query,
                query_embeddings=query_embeddings,
                filters=filters,
                top_k=self.config.retrieval_top_k,
                top_final=self.config.final_top_k
            )
            
            retrieval_time = time.time() - retrieval_start
            
            # Extract retrieved documents
            retrieved_documents = [result["evidence"] for result in final_results]
            
            # Step 2: Generate answer using a simple approach (for RAGAS evaluation)
            # In a real scenario, this would be your QA pipeline
            answer = self._generate_simple_answer(query, retrieved_documents)
            
            # Step 3: Evaluate using RAGAS
            evaluation_start = time.time()
            
            # Create dataset for RAGAS
            dataset = Dataset.from_dict({
                "question": [query],
                "answer": [answer],
                "contexts": [retrieved_documents],
                "ground_truth": [ground_truth]
            })
            
            # Run RAGAS evaluation
            result = evaluate(
                dataset,
                metrics=[
                    context_precision,
                    context_recall,
                    ContextRelevance,
                    answer_relevancy,
                    faithfulness,
                    answer_correctness
                ],
                llm=self.openai_llm
            )
            
            evaluation_time = time.time() - evaluation_start
            total_time = time.time() - start_time
            
            # Extract metrics
            metrics = result.to_pandas().iloc[0]
            
            return QueryResult(
                query=query,
                ground_truth=ground_truth,
                retrieved_documents=retrieved_documents,
                answer=answer,
                context_precision=float(metrics.get('context_precision', 0.0)),
                context_recall=float(metrics.get('context_recall', 0.0)),
                ContextRelevance=float(metrics.get('ContextRelevance', 0.0)),
                answer_relevancy=float(metrics.get('answer_relevancy', 0.0)),
                faithfulness=float(metrics.get('faithfulness', 0.0)),
                answer_correctness=float(metrics.get('answer_correctness', 0.0)),
                retrieval_time=retrieval_time,
                total_time=total_time,
                num_retrieved=len(retrieved_documents),
                pipeline_info=self.pipeline.get_pipeline_info()
            )
            
        except Exception as e:
            logger.error(f"Error evaluating query: {e}")
            return QueryResult(
                query=query,
                ground_truth=ground_truth,
                retrieved_documents=[],
                answer="",
                context_precision=0.0,
                context_recall=0.0,
                ContextRelevance=0.0,
                answer_relevancy=0.0,
                faithfulness=0.0,
                answer_correctness=0.0,
                retrieval_time=0.0,
                total_time=time.time() - start_time,
                num_retrieved=0,
                pipeline_info={},
                error_message=str(e)
            )
    
    def _generate_simple_answer(self, query: str, contexts: List[str]) -> str:
        """Generate a simple answer for RAGAS evaluation"""
        if not contexts:
            return "No relevant information found."
        
        # Simple concatenation approach for evaluation
        # In practice, you'd use your full QA pipeline
        combined_context = " ".join(contexts[:5])  # Use top 5 contexts
        return f"Based on the retrieved information: {combined_context[:500]}..."
    
    async def run_evaluation(self) -> List[QueryResult]:
        """Run complete evaluation on all test queries"""
        logger.info(f"Starting evaluation with {self.config.num_queries} queries")
        
        test_queries = self.create_test_queries()
        results = []
        
        for i, query_data in enumerate(test_queries):
            logger.info(f"Processing query {i+1}/{len(test_queries)}")
            
            try:
                result = await asyncio.wait_for(
                    self.evaluate_single_query(query_data),
                    timeout=self.config.evaluation_timeout
                )
                results.append(result)
                
                # Save intermediate results
                if self.config.save_intermediate_results:
                    self._save_intermediate_result(result, i+1)
                    
            except asyncio.TimeoutError:
                logger.error(f"Query {i+1} timed out after {self.config.evaluation_timeout}s")
                results.append(QueryResult(
                    query=query_data["query"],
                    ground_truth=query_data["ground_truth"],
                    retrieved_documents=[],
                    answer="",
                    context_precision=0.0,
                    context_recall=0.0,
                    ContextRelevance=0.0,
                    answer_relevancy=0.0,
                    faithfulness=0.0,
                    answer_correctness=0.0,
                    retrieval_time=0.0,
                    total_time=self.config.evaluation_timeout,
                    num_retrieved=0,
                    pipeline_info={},
                    error_message="Timeout"
                ))
        
        return results
    
    def _save_intermediate_result(self, result: QueryResult, query_num: int):
        """Save intermediate result to file"""
        filename = f"{self.config.output_dir}/intermediate/query_{query_num:02d}.json"
        with open(filename, 'w') as f:
            json.dump(asdict(result), f, indent=2, default=str)
    
    def generate_report(self, results: List[QueryResult]) -> pd.DataFrame:
        """Generate comprehensive evaluation report"""
        logger.info("Generating evaluation report...")
        
        # Convert results to DataFrame
        data = []
        for result in results:
            data.append({
                'query_id': results.index(result) + 1,
                'query': result.query,
                'ground_truth': result.ground_truth,
                'answer': result.answer,
                'num_retrieved': result.num_retrieved,
                'context_precision': result.context_precision,
                'context_recall': result.context_recall,
                'ContextRelevance': result.ContextRelevance,
                'answer_relevancy': result.answer_relevancy,
                'faithfulness': result.faithfulness,
                'answer_correctness': result.answer_correctness,
                'retrieval_time': result.retrieval_time,
                'total_time': result.total_time,
                'error_message': result.error_message
            })
        
        df = pd.DataFrame(data)
        
        # Calculate summary statistics
        summary_stats = {
            'metric': [
                'context_precision', 'context_recall', 'ContextRelevance',
                'answer_relevancy', 'faithfulness', 'answer_correctness'
            ],
            'mean': [
                df['context_precision'].mean(),
                df['context_recall'].mean(),
                df['ContextRelevance'].mean(),
                df['answer_relevancy'].mean(),
                df['faithfulness'].mean(),
                df['answer_correctness'].mean()
            ],
            'std': [
                df['context_precision'].std(),
                df['context_recall'].std(),
                df['ContextRelevance'].std(),
                df['answer_relevancy'].std(),
                df['faithfulness'].std(),
                df['answer_correctness'].std()
            ],
            'min': [
                df['context_precision'].min(),
                df['context_recall'].min(),
                df['ContextRelevance'].min(),
                df['answer_relevancy'].min(),
                df['faithfulness'].min(),
                df['answer_correctness'].min()
            ],
            'max': [
                df['context_precision'].max(),
                df['context_recall'].max(),
                df['ContextRelevance'].max(),
                df['answer_relevancy'].max(),
                df['faithfulness'].max(),
                df['answer_correctness'].max()
            ]
        }
        
        summary_df = pd.DataFrame(summary_stats)
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        detailed_file = f"{self.config.output_dir}/detailed_results_{timestamp}.csv"
        summary_file = f"{self.config.output_dir}/summary_stats_{timestamp}.csv"
        
        df.to_csv(detailed_file, index=False)
        summary_df.to_csv(summary_file, index=False)
        
        logger.info(f"Detailed results saved to: {detailed_file}")
        logger.info(f"Summary statistics saved to: {summary_file}")
        
        # Print summary
        print("\n" + "="*80)
        print("RAGAS EVALUATION SUMMARY")
        print("="*80)
        print(f"Total queries evaluated: {len(results)}")
        print(f"Average retrieval time: {df['retrieval_time'].mean():.2f}s")
        print(f"Average total time: {df['total_time'].mean():.2f}s")
        print(f"Average documents retrieved: {df['num_retrieved'].mean():.1f}")
        print("\nRAGAS Metrics:")
        print(summary_df.to_string(index=False))
        
        return df, summary_df

async def main():
    """Main evaluation function"""
    config = EvaluationConfig(
        num_queries=10,
        retrieval_top_k=50,
        final_top_k=20,
        use_crossencoder=True,
        enable_reranking=True,
        parallel_search=True,
        openai_model="gpt-4o-mini",
        evaluation_timeout=300.0,
        save_intermediate_results=True,
        output_dir="evaluation_results"
    )
    
    evaluator = FindPaperRAGASEvaluator(config)
    
    # Run evaluation
    results = await evaluator.run_evaluation()
    
    # Generate report
    detailed_df, summary_df = evaluator.generate_report(results)
    
    return detailed_df, summary_df

if __name__ == "__main__":
    asyncio.run(main())

