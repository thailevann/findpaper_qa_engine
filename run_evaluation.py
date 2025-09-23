#!/usr/bin/env python3
"""
Run comprehensive evaluation of the FindPaper QA Engine retriever
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from evaluation.simple_evaluator import SimpleRetrieverEvaluator
from evaluation.retriever_analysis import analyze_evaluation_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main evaluation function"""
    
    print("="*80)
    print("FINDPAPER QA ENGINE - RETRIEVER EVALUATION")
    print("="*80)
    print(f"Evaluation started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Initialize evaluator
        logger.info("Initializing evaluator...")
        evaluator = SimpleRetrieverEvaluator()
        
        # Run evaluation
        logger.info("Running evaluation on 10 diverse queries...")
        results = await evaluator.run_evaluation()
        
        # Generate report
        logger.info("Generating evaluation report...")
        detailed_df, summary_df = evaluator.generate_report(results)
        
        # Analyze results
        logger.info("Analyzing results and identifying improvements...")
        
        # Save detailed results for analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"evaluation_results_{timestamp}.csv"
        detailed_df.to_csv(results_file, index=False)
        
        # Run analysis
        analysis_report = analyze_evaluation_results(results_file)
        
        print("\n" + "="*80)
        print("EVALUATION COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"Results saved to: {results_file}")
        print(f"Analysis report generated")
        print()
        
        # Print key findings
        print("KEY FINDINGS:")
        print("-" * 40)
        for insight in analysis_report["key_insights"]:
            print(f"• {insight}")
        
        print("\nTOP RECOMMENDATIONS:")
        print("-" * 40)
        for i, rec in enumerate(analysis_report["recommendations"][:5], 1):
            print(f"{i}. {rec}")
        
        return detailed_df, summary_df, analysis_report
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        print(f"\nERROR: Evaluation failed - {e}")
        return None, None, None

if __name__ == "__main__":
    asyncio.run(main())

