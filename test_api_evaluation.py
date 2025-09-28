"""
Minimal API-based evaluation script for the FindPaper QA Engine
Tests the system by making HTTP requests to the running API
"""

import requests
import json
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIEvaluator:
    """API-based evaluator for testing the system via HTTP requests"""
    
    def __init__(self, base_url="http://localhost:9000"):
        self.base_url = base_url
        
    def create_test_queries(self):
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
            }
        ]
        
        return test_queries
    
    def test_health_endpoint(self):
        """Test if the API is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("API is running and healthy")
                return True
            else:
                logger.error(f"API health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to API: {e}")
            return False
    
    def evaluate_single_query(self, query_data):
        """Evaluate a single query via API"""
        query = query_data["query"]
        category = query_data["category"]
        expected_keywords = query_data["expected_keywords"]
        
        logger.info(f"Evaluating query: {query[:100]}...")
        start_time = time.time()
        
        try:
            # Test the search_passsages endpoint
            payload = {
                "query": query,
                "limit": 20
            }
            
            response = requests.post(
                f"{self.base_url}/search_passsages",
                json=payload,
                timeout=60
            )
            
            total_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Analyze results
                analysis = self._analyze_api_results(query, expected_keywords, data)
                
                return {
                    "query": query,
                    "category": category,
                    "expected_keywords": expected_keywords,
                    "num_results": data.get("matched_count", 0),
                    "total_time": total_time,
                    "response_data": data,
                    "analysis": analysis,
                    "success": True,
                    "error": None
                }
            else:
                return {
                    "query": query,
                    "category": category,
                    "expected_keywords": expected_keywords,
                    "num_results": 0,
                    "total_time": total_time,
                    "response_data": {},
                    "analysis": {},
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error evaluating query: {e}")
            return {
                "query": query,
                "category": category,
                "expected_keywords": expected_keywords,
                "num_results": 0,
                "total_time": time.time() - start_time,
                "response_data": {},
                "analysis": {},
                "success": False,
                "error": str(e)
            }
    
    def _analyze_api_results(self, query, expected_keywords, response_data):
        """Analyze API response results"""
        matched_papers = response_data.get("matched_papers", [])
        
        if not matched_papers:
            return {
                "keyword_coverage": 0.0,
                "avg_score": 0.0,
                "title_relevance": 0.0,
                "abstract_relevance": 0.0,
                "top_titles": [],
                "score_distribution": {}
            }
        
        # Extract scores
        scores = [paper.get("final_score", 0) for paper in matched_papers]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Analyze keyword coverage
        all_text = " ".join([paper.get("title", "") + " " + paper.get("evidence", "") for paper in matched_papers])
        keyword_coverage = sum(1 for keyword in expected_keywords if keyword.lower() in all_text.lower()) / len(expected_keywords)
        
        # Analyze title relevance
        titles = [paper.get("title", "") for paper in matched_papers]
        title_relevance = sum(1 for title in titles if any(keyword.lower() in title.lower() for keyword in expected_keywords)) / len(titles)
        
        # Analyze abstract relevance
        abstracts = [paper.get("evidence", "") for paper in matched_papers]
        abstract_relevance = sum(1 for abstract in abstracts if any(keyword.lower() in abstract.lower() for keyword in expected_keywords)) / len(abstracts)
        
        # Get top titles
        top_titles = [paper.get("title", "") for paper in matched_papers[:5]]
        
        # Score distribution
        high_scores = sum(1 for s in scores if s > 0.8)
        medium_scores = sum(1 for s in scores if 0.5 <= s <= 0.8)
        low_scores = sum(1 for s in scores if s < 0.5)
        
        score_distribution = {
            "high (>0.8)": high_scores,
            "medium (0.5-0.8)": medium_scores,
            "low (<0.5)": low_scores
        }
        
        return {
            "keyword_coverage": keyword_coverage,
            "avg_score": avg_score,
            "title_relevance": title_relevance,
            "abstract_relevance": abstract_relevance,
            "top_titles": top_titles,
            "score_distribution": score_distribution
        }
    
    def run_evaluation(self):
        """Run complete evaluation on all test queries"""
        logger.info("Starting API-based retriever evaluation...")
        
        # Check if API is running
        if not self.test_health_endpoint():
            logger.error("API is not running. Please start the server first.")
            return []
        
        test_queries = self.create_test_queries()
        results = []
        
        for i, query_data in enumerate(test_queries):
            logger.info(f"Processing query {i+1}/{len(test_queries)}")
            result = self.evaluate_single_query(query_data)
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
    
    def generate_report(self, results):
        """Generate comprehensive evaluation report"""
        logger.info("Generating evaluation report...")
        
        # Calculate summary statistics
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]
        
        if successful_results:
            avg_num_results = sum(r["num_results"] for r in successful_results) / len(successful_results)
            avg_time = sum(r["total_time"] for r in successful_results) / len(successful_results)
            avg_keyword_coverage = sum(r["analysis"]["keyword_coverage"] for r in successful_results) / len(successful_results)
            avg_score = sum(r["analysis"]["avg_score"] for r in successful_results) / len(successful_results)
            avg_title_relevance = sum(r["analysis"]["title_relevance"] for r in successful_results) / len(successful_results)
            avg_abstract_relevance = sum(r["analysis"]["abstract_relevance"] for r in successful_results) / len(successful_results)
        else:
            avg_num_results = avg_time = avg_keyword_coverage = avg_score = avg_title_relevance = avg_abstract_relevance = 0
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"api_evaluation_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to: {results_file}")
        
        # Print summary
        print("\n" + "="*80)
        print("API-BASED RETRIEVER EVALUATION SUMMARY")
        print("="*80)
        print(f"Total queries: {len(results)}")
        print(f"Successful queries: {len(successful_results)}")
        print(f"Failed queries: {len(failed_results)}")
        
        if successful_results:
            print(f"\nAverage results per query: {avg_num_results:.1f}")
            print(f"Average time per query: {avg_time:.2f}s")
            print(f"Average keyword coverage: {avg_keyword_coverage:.2f}")
            print(f"Average relevance score: {avg_score:.3f}")
            print(f"Average title relevance: {avg_title_relevance:.2f}")
            print(f"Average abstract relevance: {avg_abstract_relevance:.2f}")
        
        # Generate insights
        insights = self._generate_insights(successful_results, failed_results)
        print("\nKEY INSIGHTS:")
        for insight in insights:
            print(f"• {insight}")
        
        # Generate recommendations
        recommendations = self._generate_recommendations(successful_results, failed_results)
        print("\nRECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        
        return results, {
            "total_queries": len(results),
            "successful_queries": len(successful_results),
            "failed_queries": len(failed_results),
            "avg_num_results": avg_num_results,
            "avg_time": avg_time,
            "avg_keyword_coverage": avg_keyword_coverage,
            "avg_score": avg_score,
            "avg_title_relevance": avg_title_relevance,
            "avg_abstract_relevance": avg_abstract_relevance
        }
    
    def _generate_insights(self, successful_results, failed_results):
        """Generate key insights from the analysis"""
        insights = []
        
        if not successful_results:
            insights.append("System has critical reliability issues - immediate attention required")
            return insights
        
        # Performance insights
        avg_time = sum(r["total_time"] for r in successful_results) / len(successful_results)
        if avg_time > 3.0:
            insights.append(f"Retrieval performance is slow (avg: {avg_time:.2f}s) - optimization needed")
        else:
            insights.append(f"Retrieval performance is acceptable (avg: {avg_time:.2f}s)")
        
        # Accuracy insights
        avg_score = sum(r["analysis"]["avg_score"] for r in successful_results) / len(successful_results)
        if avg_score > 0.7:
            insights.append(f"High relevance scores achieved (avg: {avg_score:.3f}) - good ranking quality")
        elif avg_score > 0.5:
            insights.append(f"Moderate relevance scores (avg: {avg_score:.3f}) - ranking needs improvement")
        else:
            insights.append(f"Low relevance scores (avg: {avg_score:.3f}) - significant ranking issues")
        
        # Coverage insights
        avg_coverage = sum(r["analysis"]["keyword_coverage"] for r in successful_results) / len(successful_results)
        if avg_coverage > 0.7:
            insights.append(f"Excellent keyword coverage (avg: {avg_coverage:.2f}) - good semantic understanding")
        elif avg_coverage > 0.5:
            insights.append(f"Good keyword coverage (avg: {avg_coverage:.2f}) - some improvement possible")
        else:
            insights.append(f"Poor keyword coverage (avg: {avg_coverage:.2f}) - semantic search needs enhancement")
        
        # Failure insights
        if failed_results:
            failure_rate = len(failed_results) / (len(successful_results) + len(failed_results))
            insights.append(f"System reliability issues - {failure_rate:.1%} failure rate")
        
        return insights
    
    def _generate_recommendations(self, successful_results, failed_results):
        """Generate actionable recommendations"""
        recommendations = []
        
        if not successful_results:
            recommendations.append("URGENT: Fix system reliability issues before proceeding with optimization")
            return recommendations
        
        # Performance recommendations
        avg_time = sum(r["total_time"] for r in successful_results) / len(successful_results)
        if avg_time > 3.0:
            recommendations.append("Implement caching and optimize search pipeline for faster response times")
        
        # Accuracy recommendations
        avg_score = sum(r["analysis"]["avg_score"] for r in successful_results) / len(successful_results)
        if avg_score < 0.6:
            recommendations.append("Focus on improving reranking and cross-encoder performance")
        
        avg_coverage = sum(r["analysis"]["keyword_coverage"] for r in successful_results) / len(successful_results)
        if avg_coverage < 0.6:
            recommendations.append("Enhance semantic search with better embeddings and query expansion")
        
        # General recommendations
        recommendations.extend([
            "Implement comprehensive monitoring and logging for better observability",
            "Add A/B testing framework for evaluating improvements",
            "Consider implementing user feedback mechanisms for continuous improvement",
            "Develop automated testing suite for regression testing"
        ])
        
        return recommendations

def main():
    """Main evaluation function"""
    print("="*80)
    print("FINDPAPER QA ENGINE - API-BASED RETRIEVER EVALUATION")
    print("="*80)
    print(f"Evaluation started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Initialize evaluator
        logger.info("Initializing API evaluator...")
        evaluator = APIEvaluator()
        
        # Run evaluation
        logger.info("Running evaluation on 5 diverse queries...")
        results = evaluator.run_evaluation()
        
        # Generate report
        logger.info("Generating evaluation report...")
        results_data, summary = evaluator.generate_report(results)
        
        print("\n" + "="*80)
        print("EVALUATION COMPLETED SUCCESSFULLY")
        print("="*80)
        
        return results_data, summary
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        print(f"\nERROR: Evaluation failed - {e}")
        return None, None

if __name__ == "__main__":
    main()

