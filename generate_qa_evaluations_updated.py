#!/usr/bin/env python3
"""
Script to generate qa_evaluations.jsonl from qa_results.jsonl and key_ingredients
Uses GPT-4o to evaluate answers
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Any
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class QAEvaluationsGenerator:
    def __init__(self, base_dir: str, openai_api_key: str = None):
        self.base_dir = Path(base_dir)
        self.qa_results_file = self.base_dir / "qa_results.jsonl"
        self.qa_evaluations_file = self.base_dir / "qa_evaluations.jsonl"
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
    
    def process_question(self, result_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a question and create evaluations for both key_ingredients"""
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
                # Create evaluation record
                evaluation = {
                    "idx": idx,
                    "key_ingredients_id": key_ingredients_id,
                    "rewritten_query": qa_result.get('query', question),
                    "system_final_report": system_answer,
                    "evidence": evidence,
                    "filtered_passages": filtered_passages,
                    "elapsed_time_sec": elapsed_time,
                    "evaluation": evaluation_result
                }
                
                evaluations.append(evaluation)
                print(f"  Evaluated key_ingredients {key_ingredients_id}")
            else:
                print(f"  Cannot evaluate key_ingredients {key_ingredients_id}")
        
        return evaluations
    
    def save_evaluations(self, evaluations: List[Dict[str, Any]]):
        """Save evaluation results to qa_evaluations.jsonl"""
        print(f"\nSaving evaluation results to: {self.qa_evaluations_file}")
        
        with open(self.qa_evaluations_file, 'w', encoding='utf-8') as f:
            for evaluation in evaluations:
                if evaluation:  # Only save valid results
                    f.write(json.dumps(evaluation, ensure_ascii=False) + '\n')
        
        print(f"Saved {len([e for e in evaluations if e])} evaluations")
    
    def generate_all(self):
        """Generate all evaluations"""
        print("Starting qa_evaluations.jsonl generation...")
        
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
        
        print(f"\nCompleted! Processed {total_processed} questions, created {total_successful} evaluations.")
        print(f"Results saved in: {self.qa_evaluations_file}")

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
    generator = QAEvaluationsGenerator(base_dir, api_key)
    generator.generate_all()

if __name__ == "__main__":
    main()
