"""
Main pipeline orchestrator that coordinates all components.
"""
from typing import List, Dict, Any, Optional
import logging
from .retriever import PassageRetriever
from .reranker import PassageReranker
from .quote_extractor import QuoteExtractor
from .planner import OutlinePlanner
from .comparison_generator import ComparisonGenerator
from .report_synthesizer import ReportSynthesizer
from ..embedding import embed_texts

logger = logging.getLogger(__name__)


class ScholarQAPipeline:
    """Main pipeline orchestrator following AllenAI ScholarQA best practices."""
    
    def __init__(self, 
                 retrieval_top_k: int = 50,
                 rerank_top_k: int = 20,
                 model: Optional[str] = None):
        """
        Initialize the pipeline with component configurations.
        
        Args:
            retrieval_top_k: Number of passages to retrieve initially
            rerank_top_k: Number of passages to keep after reranking
            model: OpenAI model to use for LLM components
        """
        self.retriever = PassageRetriever(top_k=retrieval_top_k)
        self.reranker = PassageReranker(top_k=rerank_top_k)
        self.quote_extractor = QuoteExtractor(model=model)
        self.planner = OutlinePlanner(model=model)
        self.comparison_generator = ComparisonGenerator(model=model)
        self.report_synthesizer = ReportSynthesizer(model=model)
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
    
    def process_query(self, query: str, ranked_passages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a query through the complete ScholarQA pipeline.
        
        Args:
            query: User query
            ranked_passages: List of ranked passages with metadata
            
        Returns:
            Structured report with sections, quotes, tables, and narrative
        """
        logger.info(f"Starting ScholarQA pipeline for query: {query[:100]}...")
        
        # Initialize processing trace
        processing_trace = {
            "pipeline_start": True,
            "query": query,
            "input_passages": len(ranked_passages)
        }
        
        try:
            # Step 1: Retrieve top passages
            logger.info("Step 1: Retrieving top passages")
            retrieved_passages = self.retriever.retrieve_passages(query, ranked_passages)
            processing_trace["retrieved_passages"] = len(retrieved_passages)
            
            # Step 2: Generate embeddings for reranking
            logger.info("Step 2: Generating embeddings for reranking")
            passages_text = [p["evidence"] for p in retrieved_passages]
            embeddings = embed_texts([query] + passages_text)
            processing_trace["embeddings_generated"] = len(embeddings)
            
            # Step 3: Rerank passages
            logger.info("Step 3: Reranking passages")
            reranked_passages = self.reranker.rerank_passages(query, retrieved_passages, embeddings)
            processing_trace["reranked_passages"] = len(reranked_passages)
            
            # Step 4: Extract relevant quotes with metadata
            logger.info("Step 4: Extracting relevant quotes")
            extracted_quotes = self.quote_extractor.extract_quotes(query, reranked_passages)
            processing_trace["extracted_quotes"] = len(extracted_quotes)
            
            # Step 5: Generate outline and cluster quotes
            logger.info("Step 5: Generating outline and clustering quotes")
            outline_result = self.planner.generate_outline(query, extracted_quotes)
            clustered_quotes = outline_result["clustered_quotes"]
            processing_trace["outline_generated"] = True
            processing_trace["sections_created"] = len(clustered_quotes)
            
            # Step 6: Generate comparison tables
            logger.info("Step 6: Generating comparison tables")
            comparison_tables = self.comparison_generator.generate_comparison_tables(query, clustered_quotes)
            processing_trace["comparison_tables"] = len(comparison_tables)
            
            # Step 7: Synthesize final report
            logger.info("Step 7: Synthesizing final report")
            final_report = self.report_synthesizer.synthesize_report(
                query, clustered_quotes, comparison_tables, processing_trace
            )
            
            # Add pipeline completion info
            processing_trace["pipeline_completed"] = True
            processing_trace["final_sections"] = len(final_report["sections"])
            processing_trace["final_quotes"] = final_report["metadata"]["total_quotes"]
            processing_trace["final_papers"] = final_report["metadata"]["total_papers"]
            
            logger.info(f"Pipeline completed successfully. Generated {len(final_report['sections'])} sections with {final_report['metadata']['total_quotes']} quotes from {final_report['metadata']['total_papers']} papers.")
            
            return final_report
            
        except Exception as e:
            logger.error(f"Error in pipeline processing: {str(e)}")
            processing_trace["error"] = str(e)
            processing_trace["pipeline_failed"] = True
            
            # Return error report
            return {
                "query": query,
                "error": str(e),
                "processing_trace": processing_trace,
                "sections": [],
                "comparison_tables": [],
                "summary": f"Error processing query: {str(e)}",
                "metadata": {
                    "total_sections": 0,
                    "total_quotes": 0,
                    "total_papers": 0,
                    "comparison_tables_count": 0
                }
            }
