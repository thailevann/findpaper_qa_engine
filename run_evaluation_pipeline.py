#!/usr/bin/env python3
"""
Comprehensive script to run the entire evaluation pipeline
1. Generate qa_results.jsonl from qa_nlp.jsonl
2. Generate qa_evaluations.jsonl from qa_results.jsonl and key_ingredients
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check required components"""
    print("🔍 Checking requirements...")
    
    # Check directory
    base_dir = Path("evaluation/ScholarQABench-base")
    if not base_dir.exists():
        print(f"❌ Directory not found: {base_dir}")
        return False
    
    # Check qa_nlp.jsonl file
    qa_nlp_file = base_dir / "qa_nlp.jsonl"
    if not qa_nlp_file.exists():
        print(f"❌ File not found: {qa_nlp_file}")
        return False
    
    # Check key_ingredients directory
    key_ingredients_dir = base_dir / "key_ingredients"
    if not key_ingredients_dir.exists():
        print(f"❌ Directory not found: {key_ingredients_dir}")
        print("Please run process_scholarqa_data.py first!")
        return False
    
    # Check API key
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Warning: OPENAI_API_KEY not found")
        print("   Set: export OPENAI_API_KEY='your-api-key'")
        print("   Or script will stop at evaluation step")
    
    print("✅ All requirements met")
    return True

def run_qa_results():
    """Run script to create qa_results.jsonl"""
    print("\n📝 Step 1: Creating qa_results.jsonl...")
    print("   (Calling QA API to generate answers for questions)")
    
    try:
        result = subprocess.run([
            sys.executable, "generate_qa_results.py"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Successfully created qa_results.jsonl")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating qa_results.jsonl: {e}")
        print(f"   stdout: {e.stdout}")
        print(f"   stderr: {e.stderr}")
        return False

def run_qa_evaluations():
    """Run script to create qa_evaluations.jsonl"""
    print("\n📊 Step 2: Creating qa_evaluations.jsonl...")
    print("   (Using GPT-4o to evaluate answers)")
    
    # Check API key first
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ No OPENAI_API_KEY, skipping evaluation step")
        return False
    
    try:
        result = subprocess.run([
            sys.executable, "generate_qa_evaluations_updated.py"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Successfully created qa_evaluations.jsonl")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating qa_evaluations.jsonl: {e}")
        print(f"   stdout: {e.stdout}")
        print(f"   stderr: {e.stderr}")
        return False

def show_summary():
    """Show results summary"""
    print("\n📋 Results Summary:")
    
    base_dir = Path("evaluation/ScholarQABench-base")
    
    # Check qa_results.jsonl
    qa_results_file = base_dir / "qa_results.jsonl"
    if qa_results_file.exists():
        with open(qa_results_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"   📝 qa_results.jsonl: {len(lines)} answers")
    else:
        print("   📝 qa_results.jsonl: Not found")
    
    # Check qa_evaluations.jsonl
    qa_evaluations_file = base_dir / "qa_evaluations.jsonl"
    if qa_evaluations_file.exists():
        with open(qa_evaluations_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"   📊 qa_evaluations.jsonl: {len(lines)} evaluations")
    else:
        print("   📊 qa_evaluations.jsonl: Not found")
    
    # Check key_ingredients
    key_ingredients_dir = base_dir / "key_ingredients"
    if key_ingredients_dir.exists():
        files = list(key_ingredients_dir.glob("*.txt"))
        print(f"   🔑 key_ingredients: {len(files)} files")

def main():
    print("🚀 Starting ScholarQABench evaluation pipeline...")
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Cannot continue. Please check the requirements above.")
        return
    
    # Step 1: Create qa_results.jsonl
    if not run_qa_results():
        print("\n❌ Cannot create qa_results.jsonl. Stopping pipeline.")
        return
    
    # Step 2: Create qa_evaluations.jsonl
    if not run_qa_evaluations():
        print("\n⚠️  Cannot create qa_evaluations.jsonl.")
        print("   May be due to missing OPENAI_API_KEY or other errors.")
        print("   You can run this script separately later.")
    
    # Show summary
    show_summary()
    
    print("\n🎉 Pipeline completed!")
    print("\n📁 Files created:")
    print("   - evaluation/ScholarQABench-base/qa_results.jsonl")
    print("   - evaluation/ScholarQABench-base/qa_evaluations.jsonl (if API key available)")

if __name__ == "__main__":
    main()
