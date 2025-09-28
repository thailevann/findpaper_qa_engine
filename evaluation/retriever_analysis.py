"""
Comprehensive analysis of retriever performance and requirements
Identifies limitations and proposes improvements based on evaluation results
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any, Tuple
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RetrieverAnalyzer:
    """Analyzes retriever performance and identifies improvement opportunities"""
    
    def __init__(self, results_df: pd.DataFrame):
        self.results_df = results_df
        self.successful_results = results_df[results_df['success'] == True]
        
    def analyze_performance_patterns(self) -> Dict[str, Any]:
        """Analyze performance patterns across different query types"""
        if len(self.successful_results) == 0:
            return {"error": "No successful results to analyze"}
        
        analysis = {}
        
        # 1. Performance by category
        if 'category' in self.successful_results.columns:
            category_analysis = self.successful_results.groupby('category').agg({
                'num_results': 'mean',
                'total_time': 'mean',
                'keyword_coverage': 'mean',
                'avg_score': 'mean',
                'title_relevance': 'mean',
                'abstract_relevance': 'mean'
            }).round(3)
            analysis['by_category'] = category_analysis.to_dict()
        
        # 2. Time vs Performance correlation
        time_performance = self.successful_results[['total_time', 'avg_score', 'keyword_coverage']].corr()
        analysis['time_performance_correlation'] = time_performance.to_dict()
        
        # 3. Score distribution analysis
        score_stats = {
            'high_performing_queries': len(self.successful_results[self.successful_results['avg_score'] > 0.7]),
            'medium_performing_queries': len(self.successful_results[(self.successful_results['avg_score'] >= 0.4) & 
                                                                   (self.successful_results['avg_score'] <= 0.7)]),
            'low_performing_queries': len(self.successful_results[self.successful_results['avg_score'] < 0.4])
        }
        analysis['score_distribution'] = score_stats
        
        # 4. Keyword coverage analysis
        coverage_stats = {
            'excellent_coverage': len(self.successful_results[self.successful_results['keyword_coverage'] > 0.8]),
            'good_coverage': len(self.successful_results[(self.successful_results['keyword_coverage'] >= 0.5) & 
                                                        (self.successful_results['keyword_coverage'] <= 0.8)]),
            'poor_coverage': len(self.successful_results[self.successful_results['keyword_coverage'] < 0.5])
        }
        analysis['coverage_distribution'] = coverage_stats
        
        # 5. Relevance analysis
        relevance_stats = {
            'high_title_relevance': len(self.successful_results[self.successful_results['title_relevance'] > 0.7]),
            'high_abstract_relevance': len(self.successful_results[self.successful_results['abstract_relevance'] > 0.7]),
            'low_relevance': len(self.successful_results[(self.successful_results['title_relevance'] < 0.3) & 
                                                        (self.successful_results['abstract_relevance'] < 0.3)])
        }
        analysis['relevance_distribution'] = relevance_stats
        
        return analysis
    
    def identify_retriever_requirements(self) -> Dict[str, List[str]]:
        """Identify key requirements for an effective retriever based on analysis"""
        
        requirements = {
            "performance_requirements": [
                "Retrieve relevant documents within 2-5 seconds for real-time applications",
                "Maintain high precision (>0.7) for top-ranked results",
                "Achieve good keyword coverage (>0.6) for domain-specific queries",
                "Provide consistent performance across different query types",
                "Handle both technical and general queries effectively"
            ],
            
            "accuracy_requirements": [
                "High semantic similarity matching for conceptual queries",
                "Effective keyword matching for specific terms and phrases",
                "Good balance between recall and precision",
                "Robust handling of query variations and synonyms",
                "Effective filtering and ranking of retrieved documents"
            ],
            
            "scalability_requirements": [
                "Support for large document collections (millions of papers)",
                "Efficient indexing and search capabilities",
                "Parallel processing for improved throughput",
                "Caching mechanisms for frequently accessed content",
                "Distributed search across multiple indices"
            ],
            
            "robustness_requirements": [
                "Graceful handling of malformed or ambiguous queries",
                "Fallback mechanisms when primary search fails",
                "Error recovery and timeout handling",
                "Consistent results across different query formulations",
                "Handling of domain-specific terminology and jargon"
            ]
        }
        
        return requirements
    
    def identify_current_limitations(self) -> Dict[str, List[str]]:
        """Identify current limitations based on evaluation results"""
        
        limitations = {
            "performance_limitations": [],
            "accuracy_limitations": [],
            "scalability_limitations": [],
            "robustness_limitations": []
        }
        
        if len(self.successful_results) == 0:
            limitations["robustness_limitations"].append("High failure rate - system unable to process queries reliably")
            return limitations
        
        # Analyze performance limitations
        avg_time = self.successful_results['total_time'].mean()
        if avg_time > 5.0:
            limitations["performance_limitations"].append(f"Slow retrieval time (avg: {avg_time:.2f}s) - needs optimization")
        
        # Analyze accuracy limitations
        avg_score = self.successful_results['avg_score'].mean()
        if avg_score < 0.6:
            limitations["accuracy_limitations"].append(f"Low average relevance scores ({avg_score:.3f}) - ranking needs improvement")
        
        avg_coverage = self.successful_results['keyword_coverage'].mean()
        if avg_coverage < 0.6:
            limitations["accuracy_limitations"].append(f"Poor keyword coverage ({avg_coverage:.2f}) - semantic search may be missing relevant terms")
        
        # Analyze consistency issues
        score_std = self.successful_results['avg_score'].std()
        if score_std > 0.3:
            limitations["robustness_limitations"].append(f"High score variance ({score_std:.3f}) - inconsistent performance across queries")
        
        # Analyze category-specific issues
        if 'category' in self.successful_results.columns:
            category_performance = self.successful_results.groupby('category')['avg_score'].mean()
            worst_category = category_performance.idxmin()
            worst_score = category_performance.min()
            if worst_score < 0.5:
                limitations["accuracy_limitations"].append(f"Poor performance on {worst_category} queries ({worst_score:.3f}) - needs category-specific optimization")
        
        # Analyze failure patterns
        failed_queries = self.results_df[self.results_df['success'] == False]
        if len(failed_queries) > 0:
            failure_rate = len(failed_queries) / len(self.results_df)
            if failure_rate > 0.1:
                limitations["robustness_limitations"].append(f"High failure rate ({failure_rate:.1%}) - system reliability issues")
        
        return limitations
    
    def propose_improvements(self) -> Dict[str, List[Dict[str, str]]]:
        """Propose specific improvements based on identified limitations"""
        
        improvements = {
            "retrieval_improvements": [
                {
                    "area": "Hybrid Search Optimization",
                    "description": "Improve the balance between semantic and keyword search",
                    "implementation": "Fine-tune alpha/beta weights in reranker, implement dynamic weight adjustment based on query type",
                    "expected_impact": "Better relevance scores and keyword coverage"
                },
                {
                    "area": "Query Processing Enhancement",
                    "description": "Improve query understanding and expansion",
                    "implementation": "Add query expansion with synonyms, implement domain-specific query rewriting",
                    "expected_impact": "Better handling of technical terminology and query variations"
                },
                {
                    "area": "Reranking Optimization",
                    "description": "Enhance the cross-encoder reranking process",
                    "implementation": "Use larger cross-encoder models, implement multi-stage reranking, add domain-specific fine-tuning",
                    "expected_impact": "Higher precision in top-ranked results"
                }
            ],
            
            "performance_improvements": [
                {
                    "area": "Caching Strategy",
                    "description": "Implement intelligent caching for frequent queries",
                    "implementation": "Cache embeddings, query results, and intermediate processing steps",
                    "expected_impact": "Faster response times for repeated or similar queries"
                },
                {
                    "area": "Parallel Processing",
                    "description": "Optimize parallel search execution",
                    "implementation": "Improve async/await patterns, optimize batch processing, implement connection pooling",
                    "expected_impact": "Reduced latency and improved throughput"
                },
                {
                    "area": "Index Optimization",
                    "description": "Optimize Elasticsearch indices and queries",
                    "implementation": "Tune index settings, optimize query structure, implement index partitioning",
                    "expected_impact": "Faster search execution and better resource utilization"
                }
            ],
            
            "accuracy_improvements": [
                {
                    "area": "Embedding Model Enhancement",
                    "description": "Use domain-specific embedding models",
                    "implementation": "Fine-tune sentence transformers on academic papers, implement multi-lingual support",
                    "expected_impact": "Better semantic understanding of academic content"
                },
                {
                    "area": "Multi-field Search",
                    "description": "Enhance multi-field semantic search",
                    "implementation": "Optimize field weights, implement field-specific embeddings, add citation network features",
                    "expected_impact": "Better coverage of different content types (title, abstract, full text)"
                },
                {
                    "area": "Filtering and Ranking",
                    "description": "Improve document filtering and ranking",
                    "implementation": "Add recency bias, implement citation-based ranking, add quality indicators",
                    "expected_impact": "Higher quality results and better relevance"
                }
            ],
            
            "robustness_improvements": [
                {
                    "area": "Error Handling",
                    "description": "Implement comprehensive error handling and fallbacks",
                    "implementation": "Add timeout handling, implement graceful degradation, add retry mechanisms",
                    "expected_impact": "Higher system reliability and better user experience"
                },
                {
                    "area": "Query Validation",
                    "description": "Add query validation and preprocessing",
                    "implementation": "Validate query format, handle edge cases, implement query sanitization",
                    "expected_impact": "Reduced failure rate and more consistent results"
                },
                {
                    "area": "Monitoring and Logging",
                    "description": "Implement comprehensive monitoring",
                    "implementation": "Add performance metrics, implement query logging, add alerting for failures",
                    "expected_impact": "Better system observability and faster issue resolution"
                }
            ]
        }
        
        return improvements
    
    def generate_analysis_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        
        report = {
            "evaluation_summary": {
                "total_queries": len(self.results_df),
                "successful_queries": len(self.successful_results),
                "failure_rate": (len(self.results_df) - len(self.successful_results)) / len(self.results_df) if len(self.results_df) > 0 else 0,
                "evaluation_timestamp": datetime.now().isoformat()
            },
            
            "performance_analysis": self.analyze_performance_patterns(),
            "retriever_requirements": self.identify_retriever_requirements(),
            "current_limitations": self.identify_current_limitations(),
            "proposed_improvements": self.propose_improvements(),
            
            "key_insights": self._generate_key_insights(),
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_key_insights(self) -> List[str]:
        """Generate key insights from the analysis"""
        insights = []
        
        if len(self.successful_results) == 0:
            insights.append("System has critical reliability issues - immediate attention required")
            return insights
        
        # Performance insights
        avg_time = self.successful_results['total_time'].mean()
        if avg_time > 3.0:
            insights.append(f"Retrieval performance is slow (avg: {avg_time:.2f}s) - optimization needed")
        else:
            insights.append(f"Retrieval performance is acceptable (avg: {avg_time:.2f}s)")
        
        # Accuracy insights
        avg_score = self.successful_results['avg_score'].mean()
        if avg_score > 0.7:
            insights.append(f"High relevance scores achieved (avg: {avg_score:.3f}) - good ranking quality")
        elif avg_score > 0.5:
            insights.append(f"Moderate relevance scores (avg: {avg_score:.3f}) - ranking needs improvement")
        else:
            insights.append(f"Low relevance scores (avg: {avg_score:.3f}) - significant ranking issues")
        
        # Coverage insights
        avg_coverage = self.successful_results['keyword_coverage'].mean()
        if avg_coverage > 0.7:
            insights.append(f"Excellent keyword coverage (avg: {avg_coverage:.2f}) - good semantic understanding")
        elif avg_coverage > 0.5:
            insights.append(f"Good keyword coverage (avg: {avg_coverage:.2f}) - some improvement possible")
        else:
            insights.append(f"Poor keyword coverage (avg: {avg_coverage:.2f}) - semantic search needs enhancement")
        
        # Consistency insights
        score_std = self.successful_results['avg_score'].std()
        if score_std < 0.2:
            insights.append("Consistent performance across queries - system is reliable")
        elif score_std < 0.3:
            insights.append("Moderate performance variance - some queries perform better than others")
        else:
            insights.append("High performance variance - inconsistent results across queries")
        
        return insights
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if len(self.successful_results) == 0:
            recommendations.append("URGENT: Fix system reliability issues before proceeding with optimization")
            return recommendations
        
        # Performance recommendations
        avg_time = self.successful_results['total_time'].mean()
        if avg_time > 3.0:
            recommendations.append("Implement caching and optimize search pipeline for faster response times")
        
        # Accuracy recommendations
        avg_score = self.successful_results['avg_score'].mean()
        if avg_score < 0.6:
            recommendations.append("Focus on improving reranking and cross-encoder performance")
        
        avg_coverage = self.successful_results['keyword_coverage'].mean()
        if avg_coverage < 0.6:
            recommendations.append("Enhance semantic search with better embeddings and query expansion")
        
        # Consistency recommendations
        score_std = self.successful_results['avg_score'].std()
        if score_std > 0.3:
            recommendations.append("Implement query type detection and category-specific optimization")
        
        # General recommendations
        recommendations.extend([
            "Implement comprehensive monitoring and logging for better observability",
            "Add A/B testing framework for evaluating improvements",
            "Consider implementing user feedback mechanisms for continuous improvement",
            "Develop automated testing suite for regression testing"
        ])
        
        return recommendations

def analyze_evaluation_results(results_file: str) -> Dict[str, Any]:
    """Analyze evaluation results from CSV file"""
    
    # Load results
    df = pd.read_csv(results_file)
    
    # Create analyzer
    analyzer = RetrieverAnalyzer(df)
    
    # Generate comprehensive report
    report = analyzer.generate_analysis_report()
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"retriever_analysis_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"Analysis report saved to: {report_file}")
    
    # Print summary
    print("\n" + "="*80)
    print("RETRIEVER ANALYSIS SUMMARY")
    print("="*80)
    
    summary = report["evaluation_summary"]
    print(f"Total queries: {summary['total_queries']}")
    print(f"Successful queries: {summary['successful_queries']}")
    print(f"Failure rate: {summary['failure_rate']:.1%}")
    
    print("\nKey Insights:")
    for insight in report["key_insights"]:
        print(f"- {insight}")
    
    print("\nTop Recommendations:")
    for i, rec in enumerate(report["recommendations"][:5], 1):
        print(f"{i}. {rec}")
    
    return report

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        results_file = sys.argv[1]
        analyze_evaluation_results(results_file)
    else:
        print("Usage: python retriever_analysis.py <results_csv_file>")

