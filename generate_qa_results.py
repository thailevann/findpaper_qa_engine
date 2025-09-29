#!/usr/bin/env python3
"""
Script to generate qa_results.jsonl from qa_nlp.jsonl
Uses the existing QA system to generate answers
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Any
import requests
import sys

class QAResultsGenerator:
    def __init__(self, base_dir: str, api_url: str = "http://localhost:8000"):
        self.base_dir = Path(base_dir)
        self.api_url = api_url
        self.qa_nlp_file = self.base_dir / "qa_nlp.jsonl"
        self.qa_results_file = self.base_dir / "qa_results.jsonl"
        
    def load_qa_nlp(self) -> List[Dict[str, Any]]:
        """Load data from qa_nlp.jsonl"""
        questions = []
        
        print(f"Loading questions from: {self.qa_nlp_file}")
        
        with open(self.qa_nlp_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    questions.append(data)
                    print(f"Loaded question {data.get('idx', line_num)}")
                except json.JSONDecodeError as e:
                    print(f"JSON error at line {line_num}: {e}")
                    continue
        
        print(f"Total loaded {len(questions)} questions")
        return questions
    
    def call_qa_api(self, question: str) -> Dict[str, Any]:
        """Call QA API to get answer"""
        try:
            # Call QA API with proper payload structure
            response = requests.post(
                f"{self.api_url}/qa",
                json={
                    "query": question,
                    "limit": 50,
                    "max_themes": 5,
                    "model": None
                },
                timeout=120  # 2 minute timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
            return None
        except Exception as e:
            print(f"Unknown error: {e}")
            return None
    
    def process_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a question and generate answer"""
        idx = question_data.get('idx')
        question = question_data.get('question', '')
        
        if not idx or not question:
            print(f"Missing required information for question: {question_data}")
            return None
        
        print(f"\nProcessing question {idx}: {question[:100]}...")
        
        # Measure start time
        start_time = time.time()
        
        # Call QA API
        api_response = self.call_qa_api(question)
        
        # Measure end time
        elapsed_time = time.time() - start_time
        
        if api_response is None:
            print(f"Cannot get answer for question {idx}")
            return None
        
        # Create result
        result = {
            "idx": idx,
            "question": question,
            "response": api_response,
            "elapsed_time_sec": elapsed_time
        }
        
        print(f"Processed question {idx} in {elapsed_time:.2f} seconds")
        return result
    
    def save_results(self, results: List[Dict[str, Any]]):
        """Save results to qa_results.jsonl file"""
        print(f"\nSaving results to: {self.qa_results_file}")
        
        with open(self.qa_results_file, 'w', encoding='utf-8') as f:
            for result in results:
                if result:  # Only save valid results
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        print(f"Saved {len([r for r in results if r])} results")
    
    def generate_all(self):
        """Generate all QA results"""
        print("Starting qa_results.jsonl generation...")
        
        # Check if API is running
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code != 200:
                print(f"Warning: API may not be working properly (status: {response.status_code})")
        except:
            print("Warning: Cannot connect to API. Make sure QA system is running.")
        
        # Load questions
        questions = self.load_qa_nlp()
        if not questions:
            print("No questions found!")
            return
        
        # Process each question
        results = []
        total_processed = 0
        total_successful = 0
        
        for question_data in questions:
            try:
                result = self.process_question(question_data)
                results.append(result)
                
                if result:
                    total_successful += 1
                
                total_processed += 1
                
                # Save temporary results every 5 questions
                if total_processed % 5 == 0:
                    self.save_results(results)
                    print(f"Processed {total_processed} questions, successful {total_successful}...")
                    
            except Exception as e:
                print(f"Error processing question {question_data.get('idx', 'unknown')}: {e}")
                results.append(None)
                total_processed += 1
                continue
        
        # Save final results
        self.save_results(results)
        
        print(f"\nCompleted! Processed {total_processed} questions, successful {total_successful}.")
        print(f"Results saved in: {self.qa_results_file}")

def main():
    # Path to ScholarQABench-base directory
    base_dir = "evaluation/ScholarQABench-base"
    
    # API URL (can be changed)
    api_url = "http://localhost:8000"
    
    # Check if directory exists
    if not os.path.exists(base_dir):
        print(f"Directory not found: {base_dir}")
        return
    
    # Check if qa_nlp.jsonl exists
    qa_nlp_file = os.path.join(base_dir, "qa_nlp.jsonl")
    if not os.path.exists(qa_nlp_file):
        print(f"File not found: {qa_nlp_file}")
        return
    
    # Create generator and process
    generator = QAResultsGenerator(base_dir, api_url)
    generator.generate_all()

if __name__ == "__main__":
    main()
