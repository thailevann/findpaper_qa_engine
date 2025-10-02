#!/usr/bin/env python3
"""
Enhanced script to generate qa_evaluations.jsonl from qa_results.jsonl and key_ingredients
Uses GPT-4o to evaluate answers and calculates comprehensive metrics for every row
"""

import json
import os
import time
import statistics
from pathlib import Path
from typing import Dict, List, Any, Tuple
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class QAEvaluationsGeneratorWithMetrics:
    def __init__(self, base_dir: str, openai_api_key: str = None):
        self.base_dir = Path(base_dir)
        self.qa_results_file = self.base_dir / "qa_results.jsonl"
        self.qa_evaluations_file = self.base_dir / "qa_evaluations.jsonl"
        self.metrics_summary_file = self.base_dir / "metrics_summary.json"
        self.key_ingredients_dir = self.base_dir / "key_ingredients"
        
        # Initialize OpenAI client
        if openai_api_key:
            self.client = OpenAI(api_key=openai_api_key)
        else:
            # Try to get from environment variable
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.client = OpenAI(api_key=api_key)
            else:
                raise ValueError("Need to provide OpenAI API key")
    
    def load_qa_results(self) -> List[Dict[str, Any]]:
        """Load data from qa_results.jsonl"""
        results = []
        
        print(f"Loading results from: {self.qa_results_file}")
        
        with open(self.qa_results_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    results.append(data)
                    print(f"Loaded result for question {data.get('idx', line_num)}")
                except json.JSONDecodeError as e:
                    print(f"JSON error at line {line_num}: {e}")
                    continue
        
        print(f"Total loaded {len(results)} results")
        return results
    
    def load_key_ingredients(self, idx: int, key_ingredients_id: str) -> str:
        """Load key_ingredients file content"""
        file_path = self.key_ingredients_dir / f"{idx}_{key_ingredients_id}.txt"
        
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return ""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def create_evaluation_prompt(self, question: str, system_answer: str, 
                               evidence: str, filtered_passages: List[str]) -> str:
        """Create prompt for GPT-4o evaluation"""
        prompt = f"""
You are an expert QA system evaluator. Please evaluate the system's answer based on the provided evidence.

**Question:** {question}

**System Answer:**
{system_answer}

**Evidence (Key Ingredients):**
{evidence}

**Passages used by system:**
{json.dumps(filtered_passages, ensure_ascii=False, indent=2)}

**Evaluation Requirements:**

1. **Answer Evaluation** - Evaluate the system's answer:
   - correctness_score (0-1): Accuracy of information
   - coverage_score (0-1): Coverage of requirements in evidence
   - reasoning_score (0-1): Quality of reasoning and logic
   - summary: Brief comment about the answer

2. **Passages Evaluation** - Evaluate the passages used:
   - relevance_score (0-1): Relevance to the question
   - completeness_score (0-1): Completeness of information
   - summary: Brief comment about the passages

3. **Time Feedback** - Comment on response time:
   - "fast" (< 10s), "acceptable" (10-30s), or "slow" (> 30s)

Please return the result in JSON format:
{{
    "answer_evaluation": {{
        "correctness_score": 0.0-1.0,
        "coverage_score": 0.0-1.0,
        "reasoning_score": 0.0-1.0,
        "summary": "brief comment"
    }},
    "passages_evaluation": {{
        "relevance_score": 0.0-1.0,
        "completeness_score": 0.0-1.0,
        "summary": "brief comment"
    }},
    "time_feedback": "fast/acceptable/slow"
}}
"""
        return prompt
    
    def evaluate_with_gpt4o(self, prompt: str) -> Dict[str, Any]:
        """Call GPT-4o for evaluation"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert QA system evaluator. Please evaluate objectively and accurately."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Parse JSON response
            content = response.choices[0].message.content.strip()
            
            # Find JSON in response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)
            else:
                print(f"Cannot parse JSON from response: {content}")
                return None
                
        except Exception as e:
            print(f"Error calling GPT-4o: {e}")
            return None
    
    def calculate_row_metrics(self, evaluation: Dict[str, Any], elapsed_time: float) -> Dict[str, Any]:
        """Calculate comprehensive metrics for a single evaluation row"""
        metrics = {}
        
        # Extract evaluation scores
        answer_eval = evaluation.get('answer_evaluation', {})
        passages_eval = evaluation.get('passages_evaluation', {})
        time_feedback = evaluation.get('time_feedback', 'unknown')
        
        # Basic scores
        metrics['correctness_score'] = answer_eval.get('correctness_score', 0.0)
        metrics['coverage_score'] = answer_eval.get('coverage_score', 0.0)
        metrics['reasoning_score'] = answer_eval.get('reasoning_score', 0.0)
        metrics['relevance_score'] = passages_eval.get('relevance_score', 0.0)
        metrics['completeness_score'] = passages_eval.get('completeness_score', 0.0)
        
        # Composite scores
        metrics['answer_quality_score'] = (
            metrics['correctness_score'] + 
            metrics['coverage_score'] + 
            metrics['reasoning_score']
        ) / 3.0
        
        metrics['passage_quality_score'] = (
            metrics['relevance_score'] + 
            metrics['completeness_score']
        ) / 2.0
        
        metrics['overall_quality_score'] = (
            metrics['answer_quality_score'] + 
            metrics['passage_quality_score']
        ) / 2.0
        
        # Performance metrics
        metrics['elapsed_time_sec'] = elapsed_time
        metrics['time_category'] = time_feedback
        
        # Time-based quality metrics
        if elapsed_time < 10:
            metrics['time_efficiency_score'] = 1.0
        elif elapsed_time < 30:
            metrics['time_efficiency_score'] = 0.7
        else:
            metrics['time_efficiency_score'] = 0.3
        
        # Quality-efficiency composite
        metrics['quality_efficiency_score'] = (
            metrics['overall_quality_score'] * 0.7 + 
            metrics['time_efficiency_score'] * 0.3
        )
        
        # Score categories
        metrics['answer_quality_category'] = self._categorize_score(metrics['answer_quality_score'])
        metrics['passage_quality_category'] = self._categorize_score(metrics['passage_quality_score'])
        metrics['overall_quality_category'] = self._categorize_score(metrics['overall_quality_score'])
        
        return metrics
    
    def _categorize_score(self, score: float) -> str:
        """Categorize score into quality levels"""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        else:
            return "poor"
    
    def process_question(self, result_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a question and create evaluations for both key_ingredients with metrics"""
        idx = result_data.get('idx')
        question = result_data.get('question', '')
        response = result_data.get('response', {})
        elapsed_time = result_data.get('elapsed_time_sec', 0)
        
        if not idx or not question:
            print(f"Missing required information for question: {result_data}")
            return []
        
        print(f"\nEvaluating question {idx}: {question[:100]}...")
        
        evaluations = []
        
        # Process both key_ingredients (1 and 2)
        for key_ingredients_id in ["1", "2"]:
            print(f"  Evaluating with key_ingredients {key_ingredients_id}...")
            
            # Load key_ingredients
            evidence = self.load_key_ingredients(idx, key_ingredients_id)
            if not evidence:
                print(f"  Key_ingredients {key_ingredients_id} not found")
                continue
            
            # Get information from response
            qa_result = response.get('qa_result', {})
            system_answer = qa_result.get('final_report', '')
            filtered_passages = qa_result.get('filtered_passages', [])
            
            # Create evaluation prompt
            prompt = self.create_evaluation_prompt(
                question, system_answer, evidence, filtered_passages
            )
            
            # Call GPT-4o for evaluation
            evaluation_result = self.evaluate_with_gpt4o(prompt)
            
            if evaluation_result:
                # Calculate metrics for this row
                row_metrics = self.calculate_row_metrics(evaluation_result, elapsed_time)
                
                # Create evaluation record with metrics
                evaluation = {
                    "idx": idx,
                    "key_ingredients_id": key_ingredients_id,
                    "rewritten_query": qa_result.get('query', question),
                    "system_final_report": system_answer,
                    "evidence": evidence,
                    "filtered_passages": filtered_passages,
                    "elapsed_time_sec": elapsed_time,
                    "evaluation": evaluation_result,
                    "metrics": row_metrics
                }
                
                evaluations.append(evaluation)
                print(f"  Evaluated key_ingredients {key_ingredients_id} - Overall Quality: {row_metrics['overall_quality_category']}")
            else:
                print(f"  Cannot evaluate key_ingredients {key_ingredients_id}")
        
        return evaluations
    
    def calculate_aggregate_metrics(self, all_evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregate metrics across all evaluations"""
        if not all_evaluations:
            return {}
        
        # Extract all metrics
        all_metrics = [eval_data.get('metrics', {}) for eval_data in all_evaluations if eval_data.get('metrics')]
        
        if not all_metrics:
            return {}
        
        aggregate = {}
        
        # Score statistics
        score_fields = [
            'correctness_score', 'coverage_score', 'reasoning_score',
            'relevance_score', 'completeness_score', 'answer_quality_score',
            'passage_quality_score', 'overall_quality_score', 'time_efficiency_score',
            'quality_efficiency_score'
        ]
        
        for field in score_fields:
            scores = [m.get(field, 0) for m in all_metrics if m.get(field) is not None]
            if scores:
                aggregate[f'{field}_mean'] = statistics.mean(scores)
                aggregate[f'{field}_median'] = statistics.median(scores)
                aggregate[f'{field}_std'] = statistics.stdev(scores) if len(scores) > 1 else 0
                aggregate[f'{field}_min'] = min(scores)
                aggregate[f'{field}_max'] = max(scores)
        
        # Time statistics
        elapsed_times = [eval_data.get('elapsed_time_sec', 0) for eval_data in all_evaluations]
        if elapsed_times:
            aggregate['time_mean'] = statistics.mean(elapsed_times)
            aggregate['time_median'] = statistics.median(elapsed_times)
            aggregate['time_std'] = statistics.stdev(elapsed_times) if len(elapsed_times) > 1 else 0
        
        # Quality distribution
        quality_categories = ['excellent', 'good', 'fair', 'poor']
        for category in quality_categories:
            count = sum(1 for m in all_metrics if m.get('overall_quality_category') == category)
            aggregate[f'overall_quality_{category}_count'] = count
            aggregate[f'overall_quality_{category}_percentage'] = (count / len(all_metrics)) * 100
        
        # Time category distribution
        time_categories = ['fast', 'acceptable', 'slow']
        for category in time_categories:
            count = sum(1 for m in all_metrics if m.get('time_category') == category)
            aggregate[f'time_{category}_count'] = count
            aggregate[f'time_{category}_percentage'] = (count / len(all_metrics)) * 100
        
        # Overall statistics
        aggregate['total_evaluations'] = len(all_evaluations)
        aggregate['total_questions'] = len(set(eval_data.get('idx') for eval_data in all_evaluations))
        aggregate['successful_evaluations'] = len(all_metrics)
        aggregate['success_rate'] = (len(all_metrics) / len(all_evaluations)) * 100 if all_evaluations else 0
        
        return aggregate
    
    def save_evaluations(self, evaluations: List[Dict[str, Any]]):
        """Save evaluation results to qa_evaluations.jsonl"""
        print(f"\nSaving evaluation results to: {self.qa_evaluations_file}")
        
        with open(self.qa_evaluations_file, 'w', encoding='utf-8') as f:
            for evaluation in evaluations:
                if evaluation:  # Only save valid results
                    f.write(json.dumps(evaluation, ensure_ascii=False) + '\n')
        
        print(f"Saved {len([e for e in evaluations if e])} evaluations")
    
    def save_metrics_summary(self, aggregate_metrics: Dict[str, Any]):
        """Save metrics summary to JSON file"""
        print(f"\nSaving metrics summary to: {self.metrics_summary_file}")
        
        with open(self.metrics_summary_file, 'w', encoding='utf-8') as f:
            json.dump(aggregate_metrics, f, indent=2, ensure_ascii=False)
        
        print("Metrics summary saved successfully")
    
    def print_metrics_summary(self, aggregate_metrics: Dict[str, Any]):
        """Print a human-readable metrics summary"""
        print("\n" + "="*60)
        print("EVALUATION METRICS SUMMARY")
        print("="*60)
        
        print(f"Total Evaluations: {aggregate_metrics.get('total_evaluations', 0)}")
        print(f"Total Questions: {aggregate_metrics.get('total_questions', 0)}")
        print(f"Success Rate: {aggregate_metrics.get('success_rate', 0):.1f}%")
        
        print("\nOVERALL QUALITY SCORES:")
        print(f"  Mean: {aggregate_metrics.get('overall_quality_score_mean', 0):.3f}")
        print(f"  Median: {aggregate_metrics.get('overall_quality_score_median', 0):.3f}")
        print(f"  Std Dev: {aggregate_metrics.get('overall_quality_score_std', 0):.3f}")
        
        print("\nQUALITY DISTRIBUTION:")
        for category in ['excellent', 'good', 'fair', 'poor']:
            count = aggregate_metrics.get(f'overall_quality_{category}_count', 0)
            percentage = aggregate_metrics.get(f'overall_quality_{category}_percentage', 0)
            print(f"  {category.capitalize()}: {count} ({percentage:.1f}%)")
        
        print("\nPERFORMANCE METRICS:")
        print(f"  Average Response Time: {aggregate_metrics.get('time_mean', 0):.2f}s")
        print(f"  Median Response Time: {aggregate_metrics.get('time_median', 0):.2f}s")
        
        print("\nTIME DISTRIBUTION:")
        for category in ['fast', 'acceptable', 'slow']:
            count = aggregate_metrics.get(f'time_{category}_count', 0)
            percentage = aggregate_metrics.get(f'time_{category}_percentage', 0)
            print(f"  {category.capitalize()}: {count} ({percentage:.1f}%)")
        
        print("\nDETAILED SCORES:")
        score_fields = [
            ('correctness_score', 'Correctness'),
            ('coverage_score', 'Coverage'),
            ('reasoning_score', 'Reasoning'),
            ('relevance_score', 'Relevance'),
            ('completeness_score', 'Completeness')
        ]
        
        for field, name in score_fields:
            mean = aggregate_metrics.get(f'{field}_mean', 0)
            print(f"  {name}: {mean:.3f}")
        
        print("="*60)
    
    def generate_all(self):
        """Generate all evaluations with comprehensive metrics"""
        print("Starting qa_evaluations.jsonl generation with metrics...")
        
        # Load QA results
        results = self.load_qa_results()
        if not results:
            print("No QA results found!")
            return
        
        # Process each question
        all_evaluations = []
        total_processed = 0
        total_successful = 0
        
        for result_data in results:
            try:
                evaluations = self.process_question(result_data)
                all_evaluations.extend(evaluations)
                
                if evaluations:
                    total_successful += len(evaluations)
                
                total_processed += 1
                
                # Save temporary results every 3 questions
                if total_processed % 3 == 0:
                    self.save_evaluations(all_evaluations)
                    print(f"Processed {total_processed} questions, created {total_successful} evaluations...")
                    
                # Sleep a bit to avoid rate limits
                time.sleep(1)
                    
            except Exception as e:
                print(f"Error processing question {result_data.get('idx', 'unknown')}: {e}")
                total_processed += 1
                continue
        
        # Save final results
        self.save_evaluations(all_evaluations)
        
        # Calculate and save aggregate metrics
        print("\nCalculating aggregate metrics...")
        aggregate_metrics = self.calculate_aggregate_metrics(all_evaluations)
        self.save_metrics_summary(aggregate_metrics)
        self.print_metrics_summary(aggregate_metrics)
        
        print(f"\nCompleted! Processed {total_processed} questions, created {total_successful} evaluations.")
        print(f"Results saved in: {self.qa_evaluations_file}")
        print(f"Metrics summary saved in: {self.metrics_summary_file}")

def main():
    # Path to ScholarQABench-base directory
    base_dir = "evaluation/ScholarQABench-base"
    
    # Check if directory exists
    if not os.path.exists(base_dir):
        print(f"Directory not found: {base_dir}")
        return
    
    # Check if qa_results.jsonl exists
    qa_results_file = os.path.join(base_dir, "qa_results.jsonl")
    if not os.path.exists(qa_results_file):
        print(f"File not found: {qa_results_file}")
        print("Please run generate_qa_results.py first!")
        return
    
    # Check OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Need to provide OPENAI_API_KEY environment variable")
        print("Run: export OPENAI_API_KEY='your-api-key'")
        return
    
    # Create generator and process
    generator = QAEvaluationsGeneratorWithMetrics(base_dir, api_key)
    generator.generate_all()

if __name__ == "__main__":
    main()


