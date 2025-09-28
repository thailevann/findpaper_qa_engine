"""
Generate CSV report from the evaluation results
"""

import json
import csv
from datetime import datetime
import os

def generate_csv_report():
    """Generate CSV report from the latest evaluation results"""
    
    # Find the latest results file
    result_files = [f for f in os.listdir('.') if f.startswith('api_evaluation_results_') and f.endswith('.json')]
    if not result_files:
        print("No evaluation results found!")
        return
    
    latest_file = max(result_files)
    print(f"Processing results from: {latest_file}")
    
    # Load results
    with open(latest_file, 'r') as f:
        results = json.load(f)
    
    # Generate detailed CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"retriever_evaluation_report_{timestamp}.csv"
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow([
            'Query_ID', 'Query', 'Category', 'Expected_Keywords',
            'Rewritten_Query', 'Keyword_Query', 'Gemini_Filters',
            'Num_Results', 'Total_Time_s', 'Success', 'Error_Message',
            'Keyword_Coverage', 'Avg_Score', 'Title_Relevance', 'Abstract_Relevance',
            'Top_Titles', 'Score_Distribution', 'Pipeline_Info'
        ])
        
        # Write data rows
        for i, result in enumerate(results, 1):
            analysis = result.get('analysis', {})
            response_data = result.get('response_data', {})
            
            writer.writerow([
                i,
                result.get('query', ''),
                result.get('category', ''),
                ', '.join(result.get('expected_keywords', [])),
                response_data.get('rewritten_query', ''),
                response_data.get('keyword_query', ''),
                str(response_data.get('gemini_filters', {})),
                result.get('num_results', 0),
                result.get('total_time', 0),
                result.get('success', False),
                result.get('error', ''),
                analysis.get('keyword_coverage', 0),
                analysis.get('avg_score', 0),
                analysis.get('title_relevance', 0),
                analysis.get('abstract_relevance', 0),
                ' | '.join(analysis.get('top_titles', [])),
                str(analysis.get('score_distribution', {})),
                str(response_data.get('pipeline_info', {}))
            ])
    
    print(f"Detailed CSV report saved to: {csv_file}")
    
    # Generate summary CSV
    summary_csv = f"retriever_evaluation_summary_{timestamp}.csv"
    
    with open(summary_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Calculate summary statistics
        successful_results = [r for r in results if r.get('success', False)]
        
        if successful_results:
            avg_num_results = sum(r.get('num_results', 0) for r in successful_results) / len(successful_results)
            avg_time = sum(r.get('total_time', 0) for r in successful_results) / len(successful_results)
            avg_keyword_coverage = sum(r.get('analysis', {}).get('keyword_coverage', 0) for r in successful_results) / len(successful_results)
            avg_score = sum(r.get('analysis', {}).get('avg_score', 0) for r in successful_results) / len(successful_results)
            avg_title_relevance = sum(r.get('analysis', {}).get('title_relevance', 0) for r in successful_results) / len(successful_results)
            avg_abstract_relevance = sum(r.get('analysis', {}).get('abstract_relevance', 0) for r in successful_results) / len(successful_results)
        else:
            avg_num_results = avg_time = avg_keyword_coverage = avg_score = avg_title_relevance = avg_abstract_relevance = 0
        
        # Write summary
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total_Queries', len(results)])
        writer.writerow(['Successful_Queries', len(successful_results)])
        writer.writerow(['Failed_Queries', len(results) - len(successful_results)])
        writer.writerow(['Success_Rate', f"{len(successful_results)/len(results)*100:.1f}%" if results else "0%"])
        writer.writerow(['Avg_Results_Per_Query', f"{avg_num_results:.1f}"])
        writer.writerow(['Avg_Time_Per_Query_s', f"{avg_time:.2f}"])
        writer.writerow(['Avg_Keyword_Coverage', f"{avg_keyword_coverage:.3f}"])
        writer.writerow(['Avg_Relevance_Score', f"{avg_score:.3f}"])
        writer.writerow(['Avg_Title_Relevance', f"{avg_title_relevance:.3f}"])
        writer.writerow(['Avg_Abstract_Relevance', f"{avg_abstract_relevance:.3f}"])
        writer.writerow(['Evaluation_Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    
    print(f"Summary CSV report saved to: {summary_csv}")
    
    return csv_file, summary_csv

if __name__ == "__main__":
    generate_csv_report()
