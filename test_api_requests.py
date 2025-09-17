#!/usr/bin/env python3
"""
Test script to make requests to the ScholarQA backend API and track response counts.
This script will make various requests to test all endpoints and log the response counts.
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# API base URL
API_BASE_URL = "http://127.0.0.1:8000"

def make_request(method: str, endpoint: str, data: Dict[Any, Any] = None) -> Dict[Any, Any]:
    """Make a request to the API and return the response."""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=30)
        else:
            response = requests.post(url, json=data, timeout=30)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {"error": str(e)}

def test_health_endpoint():
    """Test the health endpoint."""
    print("🏥 Testing health endpoint...")
    result = make_request("GET", "/health")
    if "error" not in result:
        print(f"✅ Health check successful: {result['status']}")
        print(f"   Version: {result['version']}")
        print(f"   Response counts: {result.get('response_counts', {})}")
        return result.get('response_counts', {})
    return {}

def test_embed_endpoint():
    """Test the embed endpoint."""
    print("\n🔤 Testing embed endpoint...")
    data = {"text": "This is a test text for embedding."}
    result = make_request("POST", "/embed", data)
    if "error" not in result:
        print(f"✅ Embed successful: vector size={len(result.get('embedding', []))}")
    return result

def test_filter_quotes_endpoint():
    """Test the filter quotes endpoint."""
    print("\n🔍 Testing filter quotes endpoint...")
    data = {
        "query": "What are transformer architectures?",
        "passages": [
            "Transformer architectures use attention mechanisms.",
            "Attention allows models to focus on relevant parts.",
            "This is unrelated text about cooking."
        ],
        "top_k": 2
    }
    result = make_request("POST", "/filter-quotes", data)
    if "error" not in result:
        print(f"✅ Filter quotes successful: filtered={len(result.get('filtered_passages', []))}")
    return result

def test_generate_themes_endpoint():
    """Test the generate themes endpoint."""
    print("\n🎨 Testing generate themes endpoint...")
    data = {
        "query": "What are transformer architectures?",
        "passages": [
            "Transformer architectures use attention mechanisms to process sequences.",
            "The attention mechanism allows the model to focus on relevant parts of the input.",
            "Transformers have revolutionized natural language processing."
        ],
        "max_themes": 3
    }
    result = make_request("POST", "/generate-themes", data)
    if "error" not in result:
        print(f"✅ Generate themes successful: themes={len(result.get('themes', []))}")
    return result

def test_final_report_endpoint():
    """Test the final report endpoint."""
    print("\n📝 Testing final report endpoint...")
    data = {
        "query": "What are transformer architectures?",
        "themes": [
            {"name": "Background", "quotes": ["Transformers were introduced in 2017."]},
            {"name": "Architecture", "quotes": ["They use attention mechanisms."]}
        ]
    }
    result = make_request("POST", "/final-report", data)
    if "error" not in result:
        print(f"✅ Final report successful: report length={len(result.get('report', ''))}")
    return result

def test_qa_pipeline_endpoint():
    """Test the legacy QA pipeline endpoint."""
    print("\n🔄 Testing legacy QA pipeline endpoint...")
    data = {
        "query": "What are transformer architectures?",
        "ranked_passages": [
            {
                "paper_id": "arxiv:2023.12345",
                "title": "Attention Is All You Need",
                "evidence": "The transformer architecture uses attention mechanisms to process sequences.",
                "cross_score": 0.95,
                "final_score": 0.92
            },
            {
                "paper_id": "arxiv:2023.67890",
                "title": "BERT: Pre-training of Deep Bidirectional Transformers",
                "evidence": "BERT uses bidirectional transformers for language understanding.",
                "cross_score": 0.88,
                "final_score": 0.85
            }
        ],
        "max_themes": 3
    }
    result = make_request("POST", "/qa-pipeline", data)
    if "error" not in result:
        print(f"✅ Legacy QA pipeline successful: themes={len(result.get('themes', []))}")
    return result

def test_scholarqa_pipeline_endpoint():
    """Test the new ScholarQA pipeline endpoint."""
    print("\n🚀 Testing ScholarQA pipeline endpoint...")
    data = {
        "query": "What are transformer architectures?",
        "ranked_passages": [
            {
                "paper_id": "arxiv:2023.12345",
                "title": "Attention Is All You Need",
                "evidence": "The transformer architecture uses attention mechanisms to process sequences effectively.",
                "cross_score": 0.95,
                "final_score": 0.92
            },
            {
                "paper_id": "arxiv:2023.67890",
                "title": "BERT: Pre-training of Deep Bidirectional Transformers",
                "evidence": "BERT uses bidirectional transformers for language understanding tasks.",
                "cross_score": 0.88,
                "final_score": 0.85
            },
            {
                "paper_id": "arxiv:2023.11111",
                "title": "GPT-3: Language Models are Few-Shot Learners",
                "evidence": "GPT-3 demonstrates the power of large-scale transformer models.",
                "cross_score": 0.82,
                "final_score": 0.80
            }
        ],
        "retrieval_top_k": 50,
        "rerank_top_k": 20
    }
    result = make_request("POST", "/scholarqa-pipeline", data)
    if "error" not in result:
        structured_report = result.get('structured_report', {})
        metadata = structured_report.get('metadata', {})
        print(f"✅ ScholarQA pipeline successful:")
        print(f"   Sections: {metadata.get('total_sections', 0)}")
        print(f"   Quotes: {metadata.get('total_quotes', 0)}")
        print(f"   Papers: {metadata.get('total_papers', 0)}")
        print(f"   Comparison tables: {metadata.get('comparison_tables_count', 0)}")
    return result

def wait_for_server():
    """Wait for the server to be ready."""
    print("⏳ Waiting for server to be ready...")
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"   Attempt {attempt + 1}/{max_attempts} - Server not ready yet...")
        time.sleep(2)
    
    print("❌ Server failed to start within timeout period")
    return False

def main():
    """Main test function."""
    print("=" * 80)
    print("SCHOLARQA BACKEND API TEST SUITE")
    print("=" * 80)
    
    # Wait for server to be ready
    if not wait_for_server():
        print("❌ Cannot proceed without server. Make sure to start the backend first.")
        print("   Run: cd scholarqa && python run.ps1")
        sys.exit(1)
    
    # Test all endpoints
    print("\n🧪 Starting API tests...")
    
    # Test health endpoint first
    initial_counts = test_health_endpoint()
    
    # Test individual endpoints
    test_embed_endpoint()
    test_filter_quotes_endpoint()
    test_generate_themes_endpoint()
    test_final_report_endpoint()
    test_qa_pipeline_endpoint()
    test_scholarqa_pipeline_endpoint()
    
    # Check final response counts
    print("\n📊 Final response counts:")
    final_counts = test_health_endpoint()
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    if initial_counts and final_counts:
        print("Response count changes:")
        for endpoint, count in final_counts.items():
            if endpoint != "uptime":
                initial_count = initial_counts.get(endpoint, 0)
                change = count - initial_count
                print(f"  {endpoint}: {initial_count} → {count} (+{change})")
    
    print("\n✅ All API tests completed!")
    print("Check the server logs for detailed request/response information.")

if __name__ == "__main__":
    main()
