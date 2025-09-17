#!/usr/bin/env python3
"""
Simple test for ScholarQA backend API with response counting.
"""

import requests
import json
import time

API_BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(method, endpoint, data=None):
    """Test an endpoint and return the response."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, json=data, timeout=10)
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ {endpoint} failed: {e}")
        return None

def main():
    print("=" * 60)
    print("SCHOLARQA BACKEND API TEST")
    print("=" * 60)
    
    # Wait for server
    print("⏳ Waiting for server...")
    for i in range(15):
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Server is ready!")
                break
        except:
            pass
        print(f"   Attempt {i+1}/15...")
        time.sleep(2)
    else:
        print("❌ Server not ready")
        return
    
    # Test health endpoint multiple times
    print("\n🏥 Testing health endpoint (3 times)...")
    for i in range(3):
        result = test_endpoint("GET", "/health")
        if result:
            print(f"   Health check {i+1}: ✅")
            counts = result.get('response_counts', {})
            print(f"   Total requests: {counts.get('total_requests', 0)}")
        time.sleep(1)
    
    # Test embed endpoint
    print("\n🔤 Testing embed endpoint...")
    data = {"text": "This is a test text for embedding."}
    result = test_endpoint("POST", "/embed", data)
    if result:
        print(f"✅ Embed successful: vector size={len(result.get('embedding', []))}")
    
    # Test filter quotes endpoint
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
    result = test_endpoint("POST", "/filter-quotes", data)
    if result:
        print(f"✅ Filter quotes successful: filtered={len(result.get('filtered_passages', []))}")
    
    # Test ScholarQA pipeline endpoint
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
            }
        ],
        "retrieval_top_k": 50,
        "rerank_top_k": 20
    }
    result = test_endpoint("POST", "/scholarqa-pipeline", data)
    if result:
        structured_report = result.get('structured_report', {})
        metadata = structured_report.get('metadata', {})
        print(f"✅ ScholarQA pipeline successful:")
        print(f"   Sections: {metadata.get('total_sections', 0)}")
        print(f"   Quotes: {metadata.get('total_quotes', 0)}")
        print(f"   Papers: {metadata.get('total_papers', 0)}")
        print(f"   Comparison tables: {metadata.get('comparison_tables_count', 0)}")
    
    # Final health check to see all response counts
    print("\n📊 Final response counts:")
    result = test_endpoint("GET", "/health")
    if result:
        counts = result.get('response_counts', {})
        print("Response counts:")
        for endpoint, count in counts.items():
            if endpoint != "uptime":
                print(f"  {endpoint}: {count}")
    
    print("\n✅ All tests completed!")
    print("Check the server logs for detailed request/response information.")

if __name__ == "__main__":
    main()
