#!/usr/bin/env python3
"""
Test script to verify the FindPaper QA Engine integration
"""
import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_qa_endpoint():
    """Test the integrated QA endpoint"""
    print("\nTesting QA endpoint...")
    
    test_query = {
        "query": "What are the latest advances in machine learning?",
        "limit": 10,
        "max_themes": 3,
        "model": None
    }
    
    try:
        response = requests.post(f"{BASE_URL}/qa", json=test_query)
        if response.status_code == 200:
            print("✅ QA endpoint test passed")
            result = response.json()
            print(f"Query: {result['original_query']}")
            print(f"Found {result['finding_info']['total_passages_found']} passages")
            print(f"Selected {result['qa_result']['processing_info']['selected_quotes']} quotes")
            print(f"Generated {result['qa_result']['processing_info']['themes_generated']} themes")
            print(f"Final report length: {len(result['qa_result']['final_report'])} characters")
        else:
            print(f"❌ QA endpoint test failed: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ QA endpoint error: {e}")

def test_scholarqa_endpoints():
    """Test individual ScholarQA endpoints"""
    print("\nTesting ScholarQA endpoints...")
    
    # Test QA pipeline endpoint
    test_data = {
        "query": "What is artificial intelligence?",
        "ranked_passages": [
            {
                "paper_id": "test_1",
                "title": "Test Paper 1",
                "evidence": "Artificial intelligence is the simulation of human intelligence in machines.",
                "cross_score": 0.8,
                "final_score": 0.9
            },
            {
                "paper_id": "test_2", 
                "title": "Test Paper 2",
                "evidence": "Machine learning is a subset of artificial intelligence.",
                "cross_score": 0.7,
                "final_score": 0.8
            }
        ],
        "max_themes": 2
    }
    
    try:
        response = requests.post(f"{BASE_URL}/qa-pipeline", json=test_data)
        if response.status_code == 200:
            print("✅ ScholarQA pipeline endpoint test passed")
            result = response.json()
            print(f"Generated {len(result['themes'])} themes")
            print(f"Final report length: {len(result['final_report'])} characters")
        else:
            print(f"❌ ScholarQA pipeline endpoint test failed: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ ScholarQA pipeline endpoint error: {e}")

if __name__ == "__main__":
    print("🚀 Starting FindPaper QA Engine Integration Tests")
    print("=" * 50)
    
    test_health()
    test_qa_endpoint()
    test_scholarqa_endpoints()
    
    print("\n" + "=" * 50)
    print("🏁 Integration tests completed")
    print("\nNote: Make sure the server is running with: python app.py")

