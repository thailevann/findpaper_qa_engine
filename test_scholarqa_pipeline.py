#!/usr/bin/env python3
"""
Test script for the new ScholarQA pipeline.
This script demonstrates the enhanced features and structured output.
"""

import json
import os
from typing import List, Dict, Any

# Mock data for testing
MOCK_RANKED_PASSAGES = [
    {
        "paper_id": "arxiv:2023.12345",
        "title": "Advanced Transformer Architectures for NLP",
        "evidence": "Transformer architectures have revolutionized natural language processing by introducing attention mechanisms that allow models to focus on relevant parts of input sequences. The self-attention mechanism enables parallel processing and captures long-range dependencies effectively.",
        "cross_score": 0.95,
        "final_score": 0.92
    },
    {
        "paper_id": "arxiv:2023.67890",
        "title": "Efficient Attention Mechanisms in Large Language Models",
        "evidence": "Recent advances in attention mechanisms have focused on reducing computational complexity while maintaining performance. Sparse attention patterns and linear attention variants have shown promising results in scaling transformer models to longer sequences.",
        "cross_score": 0.88,
        "final_score": 0.85
    },
    {
        "paper_id": "arxiv:2023.11111",
        "title": "Multi-Modal Transformer Architectures",
        "evidence": "Multi-modal transformers extend the attention mechanism to handle different types of input data simultaneously. These architectures can process text, images, and audio in a unified framework, enabling more comprehensive understanding of complex data.",
        "cross_score": 0.82,
        "final_score": 0.80
    },
    {
        "paper_id": "arxiv:2023.22222",
        "title": "Transformer Optimization Techniques",
        "evidence": "Various optimization techniques have been developed to improve transformer efficiency, including knowledge distillation, pruning, and quantization. These methods help reduce model size and inference time while maintaining competitive performance.",
        "cross_score": 0.79,
        "final_score": 0.77
    },
    {
        "paper_id": "arxiv:2023.33333",
        "title": "Attention Mechanisms in Vision Transformers",
        "evidence": "Vision transformers apply attention mechanisms to image patches, achieving state-of-the-art results in computer vision tasks. The patch-based approach allows transformers to process images as sequences of visual tokens.",
        "cross_score": 0.76,
        "final_score": 0.74
    }
]

def test_scholarqa_pipeline():
    """Test the new ScholarQA pipeline with mock data."""
    
    # Import the pipeline function
    try:
        from scholarqa.app.qa import process_scholarqa_pipeline
    except ImportError as e:
        print(f"Error importing ScholarQA pipeline: {e}")
        print("Make sure you're running from the correct directory and all dependencies are installed.")
        return
    
    # Test query
    query = "What are the latest advances in transformer architectures?"
    
    print("=" * 80)
    print("SCHOLARQA PIPELINE TEST")
    print("=" * 80)
    print(f"Query: {query}")
    print(f"Number of passages: {len(MOCK_RANKED_PASSAGES)}")
    print()
    
    try:
        # Process through the new pipeline
        print("Processing through ScholarQA pipeline...")
        result = process_scholarqa_pipeline(
            query=query,
            ranked_passages=MOCK_RANKED_PASSAGES,
            model="gpt-4o-mini",  # or None to use default
            retrieval_top_k=50,
            rerank_top_k=20
        )
        
        # Display results
        print("✅ Pipeline completed successfully!")
        print()
        
        # Summary
        print("📋 SUMMARY:")
        print("-" * 40)
        print(result.get("summary", "No summary available"))
        print()
        
        # Metadata
        metadata = result.get("metadata", {})
        print("📊 METADATA:")
        print("-" * 40)
        print(f"Total sections: {metadata.get('total_sections', 0)}")
        print(f"Total quotes: {metadata.get('total_quotes', 0)}")
        print(f"Total papers: {metadata.get('total_papers', 0)}")
        print(f"Comparison tables: {metadata.get('comparison_tables_count', 0)}")
        print()
        
        # Sections
        sections = result.get("sections", [])
        print("📑 SECTIONS:")
        print("-" * 40)
        for i, section in enumerate(sections, 1):
            print(f"{i}. {section.get('name', 'Unnamed')}")
            print(f"   Description: {section.get('description', 'No description')}")
            print(f"   Quotes: {section.get('quote_count', 0)}")
            print(f"   Papers: {len(section.get('papers_referenced', []))}")
            
            # Show first quote with metadata
            quotes = section.get("quotes", [])
            if quotes:
                first_quote = quotes[0]
                print(f"   Sample quote: {first_quote.get('quote_text', '')[:100]}...")
                print(f"   From: {first_quote.get('title', 'Unknown')} ({first_quote.get('paper_id', 'Unknown')})")
                print(f"   Score: {first_quote.get('score', 0):.3f}")
            print()
        
        # Comparison tables
        comparison_tables = result.get("comparison_tables", [])
        if comparison_tables:
            print("📊 COMPARISON TABLES:")
            print("-" * 40)
            for i, table in enumerate(comparison_tables, 1):
                print(f"{i}. Section: {table.get('section', 'Unknown')}")
                print(f"   Headers: {table.get('headers', [])}")
                print(f"   Papers compared: {table.get('paper_count', 0)}")
                print()
        
        # Processing trace
        processing_trace = result.get("processing_trace", {})
        print("🔍 PROCESSING TRACE:")
        print("-" * 40)
        print(f"Pipeline completed: {processing_trace.get('pipeline_completed', False)}")
        print(f"Input passages: {processing_trace.get('input_passages', 0)}")
        print(f"Retrieved passages: {processing_trace.get('retrieved_passages', 0)}")
        print(f"Reranked passages: {processing_trace.get('reranked_passages', 0)}")
        print(f"Extracted quotes: {processing_trace.get('extracted_quotes', 0)}")
        print(f"Sections created: {processing_trace.get('sections_created', 0)}")
        print(f"Comparison tables: {processing_trace.get('comparison_tables', 0)}")
        print()
        
        # Save full result to file
        output_file = "scholarqa_test_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"💾 Full result saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error processing pipeline: {str(e)}")
        print("This might be due to missing OpenAI API key or other configuration issues.")
        print("Make sure to set OPENAI_API_KEY environment variable.")

def test_legacy_pipeline():
    """Test the legacy pipeline for comparison."""
    
    try:
        from scholarqa.app.qa import process_qa_pipeline
    except ImportError as e:
        print(f"Error importing legacy pipeline: {e}")
        return
    
    print("=" * 80)
    print("LEGACY PIPELINE TEST (for comparison)")
    print("=" * 80)
    
    query = "What are the latest advances in transformer architectures?"
    
    try:
        result = process_qa_pipeline(
            query=query,
            ranked_passages=MOCK_RANKED_PASSAGES,
            model="gpt-4o-mini",
            max_themes=5
        )
        
        print("✅ Legacy pipeline completed!")
        print(f"Themes: {len(result.get('themes', []))}")
        print(f"Filtered passages: {len(result.get('filtered_passages', []))}")
        print(f"Final report length: {len(result.get('final_report', ''))}")
        
        # Save legacy result
        output_file = "legacy_test_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"💾 Legacy result saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error in legacy pipeline: {str(e)}")

if __name__ == "__main__":
    print("ScholarQA Pipeline Test Suite")
    print("=" * 80)
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY environment variable not set.")
        print("   The pipeline will fail without a valid API key.")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        print()
    
    # Test new pipeline
    test_scholarqa_pipeline()
    
    print("\n" + "=" * 80)
    
    # Test legacy pipeline for comparison
    test_legacy_pipeline()
    
    print("\n" + "=" * 80)
    print("Test completed!")
    print("Check the generated JSON files for detailed results.")

