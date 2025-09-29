#!/usr/bin/env python3
"""
Comprehensive analysis and visualization of evaluation results
"""

import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
import warnings
warnings.filterwarnings('ignore')

# Set style for better plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class EvaluationAnalyzer:
    def __init__(self, base_dir: str = "evaluation/ScholarQABench-base"):
        self.base_dir = Path(base_dir)
        self.qa_results_file = self.base_dir / "qa_results.jsonl"
        self.qa_evaluations_file = self.base_dir / "qa_evaluations.jsonl"
        
    def load_data(self):
        """Load all evaluation data"""
        print("📊 Loading evaluation data...")
        
        # Load QA results
        self.qa_results = []
        with open(self.qa_results_file, 'r', encoding='utf-8') as f:
            for line in f:
                self.qa_results.append(json.loads(line.strip()))
        
        # Load evaluations
        self.evaluations = []
        with open(self.qa_evaluations_file, 'r', encoding='utf-8') as f:
            for line in f:
                self.evaluations.append(json.loads(line.strip()))
        
        print(f"   ✅ Loaded {len(self.qa_results)} QA results")
        print(f"   ✅ Loaded {len(self.evaluations)} evaluations")
        
    def create_performance_summary(self):
        """Create performance summary statistics"""
        print("\n📈 Performance Summary:")
        
        # Response times
        times = [r['elapsed_time_sec'] for r in self.qa_results]
        print(f"   ⏱️  Average response time: {np.mean(times):.2f}s")
        print(f"   ⏱️  Median response time: {np.median(times):.2f}s")
        print(f"   ⏱️  Fastest response: {np.min(times):.2f}s")
        print(f"   ⏱️  Slowest response: {np.max(times):.2f}s")
        
        # Success rate
        successful = len([r for r in self.qa_results if r.get('response')])
        print(f"   ✅ Success rate: {successful}/{len(self.qa_results)} ({successful/len(self.qa_results)*100:.1f}%)")
        
    def create_evaluation_summary(self):
        """Create evaluation metrics summary"""
        print("\n📊 Evaluation Metrics Summary:")
        
        # Extract scores
        correctness_scores = []
        coverage_scores = []
        reasoning_scores = []
        relevance_scores = []
        completeness_scores = []
        
        for eval_data in self.evaluations:
            evaluation = eval_data.get('evaluation', {})
            
            # Answer evaluation
            answer_eval = evaluation.get('answer_evaluation', {})
            if 'correctness_score' in answer_eval:
                correctness_scores.append(answer_eval['correctness_score'])
            if 'coverage_score' in answer_eval:
                coverage_scores.append(answer_eval['coverage_score'])
            if 'reasoning_score' in answer_eval:
                reasoning_scores.append(answer_eval['reasoning_score'])
            
            # Passages evaluation
            passages_eval = evaluation.get('passages_evaluation', {})
            if 'relevance_score' in passages_eval:
                relevance_scores.append(passages_eval['relevance_score'])
            if 'completeness_score' in passages_eval:
                completeness_scores.append(passages_eval['completeness_score'])
        
        # Calculate statistics
        metrics = {
            'Correctness': correctness_scores,
            'Coverage': coverage_scores,
            'Reasoning': reasoning_scores,
            'Relevance': relevance_scores,
            'Completeness': completeness_scores
        }
        
        for metric_name, scores in metrics.items():
            if scores:
                print(f"   📈 {metric_name}: {np.mean(scores):.3f} ± {np.std(scores):.3f} (n={len(scores)})")
        
        return metrics
    
    def create_visualizations(self, metrics):
        """Create comprehensive visualizations"""
        print("\n📊 Creating visualizations...")
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('ScholarQABench Evaluation Analysis', fontsize=16, fontweight='bold')
        
        # 1. Response Time Distribution
        times = [r['elapsed_time_sec'] for r in self.qa_results]
        axes[0, 0].hist(times, bins=15, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, 0].set_title('Response Time Distribution')
        axes[0, 0].set_xlabel('Time (seconds)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].axvline(np.mean(times), color='red', linestyle='--', label=f'Mean: {np.mean(times):.1f}s')
        axes[0, 0].legend()
        
        # 2. Evaluation Scores Box Plot
        score_data = []
        score_labels = []
        for metric_name, scores in metrics.items():
            if scores:
                score_data.append(scores)
                score_labels.append(metric_name)
        
        if score_data:
            axes[0, 1].boxplot(score_data, labels=score_labels)
            axes[0, 1].set_title('Evaluation Scores Distribution')
            axes[0, 1].set_ylabel('Score')
            axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 3. Average Scores Bar Chart
        avg_scores = [np.mean(scores) for scores in score_data if scores]
        axes[0, 2].bar(score_labels[:len(avg_scores)], avg_scores, color='lightgreen', alpha=0.7)
        axes[0, 2].set_title('Average Evaluation Scores')
        axes[0, 2].set_ylabel('Average Score')
        axes[0, 2].set_ylim(0, 1)
        for i, v in enumerate(avg_scores):
            axes[0, 2].text(i, v + 0.01, f'{v:.3f}', ha='center', va='bottom')
        
        # 4. Key Ingredients Comparison
        key_ingredients_1_scores = []
        key_ingredients_2_scores = []
        
        for eval_data in self.evaluations:
            evaluation = eval_data.get('evaluation', {})
            answer_eval = evaluation.get('answer_evaluation', {})
            if 'correctness_score' in answer_eval:
                if eval_data.get('key_ingredients_id') == '1':
                    key_ingredients_1_scores.append(answer_eval['correctness_score'])
                else:
                    key_ingredients_2_scores.append(answer_eval['correctness_score'])
        
        if key_ingredients_1_scores and key_ingredients_2_scores:
            axes[1, 0].boxplot([key_ingredients_1_scores, key_ingredients_2_scores], 
                              labels=['Most Important', 'Nice to Have'])
            axes[1, 0].set_title('Correctness by Key Ingredients Type')
            axes[1, 0].set_ylabel('Correctness Score')
        
        # 5. Response Time vs Correctness
        time_correctness = []
        for i, result in enumerate(self.qa_results):
            # Find corresponding evaluation
            for eval_data in self.evaluations:
                if eval_data.get('idx') == result.get('idx'):
                    evaluation = eval_data.get('evaluation', {})
                    answer_eval = evaluation.get('answer_evaluation', {})
                    if 'correctness_score' in answer_eval:
                        time_correctness.append({
                            'time': result['elapsed_time_sec'],
                            'correctness': answer_eval['correctness_score']
                        })
                        break
        
        if time_correctness:
            times = [tc['time'] for tc in time_correctness]
            correctness = [tc['correctness'] for tc in time_correctness]
            axes[1, 1].scatter(times, correctness, alpha=0.6, color='purple')
            axes[1, 1].set_title('Response Time vs Correctness')
            axes[1, 1].set_xlabel('Response Time (s)')
            axes[1, 1].set_ylabel('Correctness Score')
            
            # Add trend line
            z = np.polyfit(times, correctness, 1)
            p = np.poly1d(z)
            axes[1, 1].plot(times, p(times), "r--", alpha=0.8)
        
        # 6. Score Correlation Heatmap
        if len(score_data) >= 2:
            # Create correlation matrix
            score_df = pd.DataFrame({
                label: scores for label, scores in zip(score_labels, score_data) if scores
            })
            correlation_matrix = score_df.corr()
            
            im = axes[1, 2].imshow(correlation_matrix, cmap='coolwarm', vmin=-1, vmax=1)
            axes[1, 2].set_title('Score Correlations')
            axes[1, 2].set_xticks(range(len(correlation_matrix.columns)))
            axes[1, 2].set_yticks(range(len(correlation_matrix.columns)))
            axes[1, 2].set_xticklabels(correlation_matrix.columns, rotation=45)
            axes[1, 2].set_yticklabels(correlation_matrix.columns)
            
            # Add correlation values
            for i in range(len(correlation_matrix.columns)):
                for j in range(len(correlation_matrix.columns)):
                    text = axes[1, 2].text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}',
                                         ha="center", va="center", color="black")
            
            plt.colorbar(im, ax=axes[1, 2])
        
        plt.tight_layout()
        plt.savefig('evaluation_analysis.png', dpi=300, bbox_inches='tight')
        print("   📊 Saved visualization: evaluation_analysis.png")
        
        return fig
    
    def create_detailed_report(self):
        """Create detailed analysis report"""
        print("\n📋 Creating detailed report...")
        
        report = {
            "summary": {
                "total_questions": len(self.qa_results),
                "total_evaluations": len(self.evaluations),
                "success_rate": len([r for r in self.qa_results if r.get('response')]) / len(self.qa_results) * 100,
                "average_response_time": np.mean([r['elapsed_time_sec'] for r in self.qa_results])
            },
            "performance_metrics": {},
            "evaluation_metrics": {},
            "recommendations": []
        }
        
        # Performance metrics
        times = [r['elapsed_time_sec'] for r in self.qa_results]
        report["performance_metrics"] = {
            "average_time": np.mean(times),
            "median_time": np.median(times),
            "min_time": np.min(times),
            "max_time": np.max(times),
            "std_time": np.std(times)
        }
        
        # Evaluation metrics
        metrics = self.create_evaluation_summary()
        for metric_name, scores in metrics.items():
            if scores:
                report["evaluation_metrics"][metric_name] = {
                    "mean": np.mean(scores),
                    "median": np.median(scores),
                    "std": np.std(scores),
                    "min": np.min(scores),
                    "max": np.max(scores)
                }
        
        # Generate recommendations
        if report["evaluation_metrics"].get("Correctness", {}).get("mean", 0) < 0.7:
            report["recommendations"].append("Consider improving answer accuracy - correctness score is below 0.7")
        
        if report["performance_metrics"]["average_time"] > 45:
            report["recommendations"].append("Response time is high - consider optimizing the QA pipeline")
        
        if report["evaluation_metrics"].get("Coverage", {}).get("mean", 0) < 0.6:
            report["recommendations"].append("Improve coverage of requirements in answers")
        
        # Save report
        with open('evaluation_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print("   📄 Saved detailed report: evaluation_report.json")
        return report
    
    def run_analysis(self):
        """Run complete analysis"""
        print("🚀 Starting comprehensive evaluation analysis...")
        
        # Load data
        self.load_data()
        
        # Create summaries
        self.create_performance_summary()
        metrics = self.create_evaluation_summary()
        
        # Create visualizations
        self.create_visualizations(metrics)
        
        # Create detailed report
        report = self.create_detailed_report()
        
        print("\n✅ Analysis completed!")
        print("📁 Generated files:")
        print("   - evaluation_analysis.png (visualizations)")
        print("   - evaluation_report.json (detailed report)")
        
        return report

def main():
    analyzer = EvaluationAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()

