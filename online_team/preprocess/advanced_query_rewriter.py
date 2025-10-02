"""
Advanced Query Rewriter with taxonomy expansion and survey-aware capabilities.

This module provides intelligent query rewriting that:
1. Expands queries with domain-specific taxonomy
2. Adds survey-aware keywords
3. Generates multiple keyword query variations
4. Identifies domain-specific boost terms
"""

import json
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import openai
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AdvancedRewrittenQuery:
    """Enhanced query structure with multiple expansions"""
    original_query: str
    rewritten_query: str  # Main semantic query with taxonomy expansion
    keyword_queries: List[str]  # Multiple keyword query variations
    exclude_terms: List[str]  # Terms to exclude/downrank
    boost_terms: List[str]  # Terms to boost in results
    domain_hints: List[str]  # Domain-specific hints (e.g., datasets, metrics)
    search_filters: Dict[str, str] = field(default_factory=dict)


# Domain-specific taxonomy templates
TAXONOMY_TEMPLATES = {
    "nlp_summarization": {
        "methods": ["extractive", "abstractive", "hybrid", "query-focused"],
        "models": ["transformer", "BERT", "GPT", "T5", "BART", "PEGASUS", "LED"],
        "approaches": ["neural", "graph-based", "attention", "pre-training", "fine-tuning"],
        "datasets": ["CNN/DailyMail", "XSum", "PubMed", "Multi-News", "arXiv", "Reddit"],
        "metrics": ["ROUGE", "BLEU", "METEOR", "BERTScore", "human evaluation"],
        "keywords": ["survey", "review", "benchmark", "state-of-the-art", "comparison"]
    },
    "machine_learning": {
        "methods": ["supervised", "unsupervised", "reinforcement", "semi-supervised", "few-shot"],
        "models": ["neural network", "SVM", "random forest", "XGBoost", "transformer"],
        "techniques": ["optimization", "regularization", "ensemble", "transfer learning"],
        "metrics": ["accuracy", "F1", "precision", "recall", "AUC"],
        "keywords": ["survey", "benchmark", "evaluation", "comparison", "sota"]
    },
    "computer_vision": {
        "tasks": ["classification", "detection", "segmentation", "tracking", "generation"],
        "models": ["CNN", "ResNet", "YOLO", "U-Net", "Vision Transformer", "CLIP"],
        "datasets": ["ImageNet", "COCO", "Pascal VOC", "Cityscapes"],
        "metrics": ["mAP", "IoU", "accuracy", "FID"],
        "keywords": ["survey", "benchmark", "state-of-the-art"]
    }
}


ADVANCED_QUERY_REWRITE_PROMPT = """
<task>
You are an expert at rewriting academic search queries to maximize retrieval quality.

Your goal is to expand and enrich the user's query with:
1. **Taxonomy expansion**: Add domain-specific terms, methodologies, models, datasets
2. **Survey awareness**: Include keywords like "survey", "review", "benchmark", "comparison"
3. **Multiple keyword variations**: Generate different keyword query formulations
4. **Negative filters**: Identify irrelevant terms to exclude
5. **Boost terms**: Identify important terms that should boost relevance

Output a JSON with the following structure:
{{
    "rewritten_query": "A comprehensive natural language query with taxonomy expansion",
    "keyword_queries": [
        "Query variation 1 with specific terms",
        "Query variation 2 focusing on different aspect",
        "Query variation 3 with Boolean operators"
    ],
    "exclude_terms": ["term1", "term2"],
    "boost_terms": ["important_term1", "important_term2"],
    "domain_hints": ["dataset_name", "metric_name", "model_name"]
}}
</task>

<guidelines>
1. **rewritten_query**: Should be a comprehensive natural language query that:
   - Includes the main topic with domain context
   - Mentions key methodologies, approaches, or models
   - Explicitly includes "survey", "review", or "research papers" phrasing
   - Adds relevant taxonomy terms in parentheses
   
   Example: "Survey or research papers on text summarization methods in NLP (extractive summarization, abstractive summarization, transformer-based models, pre-training, datasets, evaluation metrics)"

2. **keyword_queries**: Generate 3-5 variations optimized for keyword search:
   - Use Boolean operators (AND, OR) strategically
   - Use intitle:"..." for title-specific terms
   - Combine specific model names, datasets, or metrics
   - Each variation should target a different aspect
   
   Example: 
   - intitle:"text summarization" AND (survey OR review OR benchmark)
   - "abstractive summarization" (transformer OR BART OR PEGASUS OR T5)
   - "extractive summarization" (graph OR neural OR attention)

3. **exclude_terms**: List terms that are likely to bring irrelevant papers:
   - Related but different domains (e.g., "economics" for NLP query)
   - Ambiguous terms that have different meanings
   - Keep list short (3-7 terms max)

4. **boost_terms**: List 5-10 terms that strongly indicate relevance:
   - Well-known datasets for the domain
   - Standard evaluation metrics
   - Important model architectures
   - Key methodology names

5. **domain_hints**: Extract specific entities mentioned or implied:
   - Dataset names (CNN/DailyMail, ImageNet, etc.)
   - Evaluation metrics (ROUGE, BLEU, mAP, etc.)
   - Model architectures (BERT, ResNet, etc.)
</guidelines>

<examples>
<example>
Input: "text summarization in NLP"

Output:
{{
    "rewritten_query": "Survey or research papers on text summarization methods in NLP (extractive summarization, abstractive summarization, transformer-based models, sequence-to-sequence, pre-training, datasets, evaluation metrics)",
    "keyword_queries": [
        "intitle:\\"text summarization\\" AND (extractive OR abstractive OR transformer OR survey)",
        "\\"abstractive summarization\\" (transformer OR BART OR PEGASUS OR T5)",
        "\\"extractive summarization\\" (neural OR graph OR TextRank OR attention)",
        "summarization (survey OR review) NLP benchmark",
        "\\"document summarization\\" (CNN/DailyMail OR XSum OR arXiv)"
    ],
    "exclude_terms": ["economics", "finance", "dialogue segmentation", "bibliometrics", "patent"],
    "boost_terms": ["ROUGE", "CNN/DailyMail", "XSum", "PEGASUS", "BART", "T5", "abstractive", "extractive", "benchmark"],
    "domain_hints": ["CNN/DailyMail", "XSum", "ROUGE", "BART", "PEGASUS", "transformer"]
}}
</example>

<example>
Input: "object detection in images"

Output:
{{
    "rewritten_query": "Survey or research papers on object detection methods in computer vision (convolutional neural networks, region-based methods, single-stage detectors, YOLO, Faster R-CNN, evaluation metrics, benchmark datasets)",
    "keyword_queries": [
        "intitle:\\"object detection\\" AND (survey OR review OR benchmark)",
        "\\"object detection\\" (YOLO OR \\"Faster R-CNN\\" OR RetinaNet OR DETR)",
        "\\"real-time object detection\\" (COCO OR \\"Pascal VOC\\" OR ImageNet)",
        "detection (mAP OR IoU) benchmark computer vision",
        "\\"single-stage detector\\" OR \\"two-stage detector\\" survey"
    ],
    "exclude_terms": ["3D detection", "video tracking", "medical imaging", "satellite", "astronomical"],
    "boost_terms": ["COCO", "Pascal VOC", "mAP", "YOLO", "Faster R-CNN", "RetinaNet", "IoU", "benchmark"],
    "domain_hints": ["COCO", "Pascal VOC", "mAP", "IoU", "YOLO", "Faster R-CNN"]
}}
</example>
</examples>

Now process this query:
<query>
{query}
</query>

Output only valid JSON, no additional text.
"""


class AdvancedQueryRewriter:
    """Advanced query rewriter with domain-aware expansion"""
    
    def __init__(self, model: str = "gpt-4", use_taxonomy_boost: bool = True):
        """
        Initialize the advanced query rewriter.
        
        Args:
            model: OpenAI model to use
            use_taxonomy_boost: Whether to use taxonomy templates for expansion
        """
        self.model = model
        self.use_taxonomy_boost = use_taxonomy_boost
        
    def detect_domain(self, query: str) -> Optional[str]:
        """Detect the domain of the query for taxonomy selection"""
        query_lower = query.lower()
        
        # NLP/Summarization
        if any(term in query_lower for term in ["summarization", "summary", "abstractive", "extractive", "text generation"]):
            return "nlp_summarization"
        
        # Computer Vision
        if any(term in query_lower for term in ["detection", "segmentation", "classification", "image", "visual", "video"]):
            return "computer_vision"
        
        # General ML
        if any(term in query_lower for term in ["machine learning", "deep learning", "neural network", "model", "training"]):
            return "machine_learning"
        
        return None
    
    def get_taxonomy_context(self, query: str) -> str:
        """Get relevant taxonomy context for the query"""
        domain = self.detect_domain(query)
        
        if not domain or not self.use_taxonomy_boost:
            return ""
        
        taxonomy = TAXONOMY_TEMPLATES.get(domain, {})
        context_parts = []
        
        for category, terms in taxonomy.items():
            context_parts.append(f"{category.replace('_', ' ').title()}: {', '.join(terms)}")
        
        return "\n".join(context_parts)
    
    def rewrite_query(self, query: str, filters: Optional[Dict[str, str]] = None) -> Tuple[AdvancedRewrittenQuery, str]:
        """
        Rewrite query using GPT-4 with advanced taxonomy expansion.
        
        Args:
            query: Original user query
            filters: Optional search filters (year, venue, etc.)
            
        Returns:
            Tuple of (AdvancedRewrittenQuery, raw_response)
        """
        # Add taxonomy context if available
        taxonomy_context = self.get_taxonomy_context(query)
        
        prompt = ADVANCED_QUERY_REWRITE_PROMPT.format(query=query)
        
        if taxonomy_context:
            prompt += f"\n\n<taxonomy_context>\nRelevant domain taxonomy:\n{taxonomy_context}\n</taxonomy_context>"
        
        try:
            resp = openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Slightly creative but consistent
                max_tokens=1500
            )
            
            content = resp.choices[0].message.content.strip()
            logger.info(f"[AdvancedQueryRewriter] Raw GPT output:\n{content}")
            
            # Extract JSON
            start = content.find("{")
            end = content.rfind("}") + 1
            json_str = content[start:end]
            
            data = json.loads(json_str)
            
            # Build AdvancedRewrittenQuery
            rewritten = AdvancedRewrittenQuery(
                original_query=query,
                rewritten_query=data.get("rewritten_query", query),
                keyword_queries=data.get("keyword_queries", [query]),
                exclude_terms=data.get("exclude_terms", []),
                boost_terms=data.get("boost_terms", []),
                domain_hints=data.get("domain_hints", []),
                search_filters=filters or {}
            )
            
            logger.info(f"[AdvancedQueryRewriter] Successfully rewrote query with {len(rewritten.keyword_queries)} keyword variations")
            
            return rewritten, content
            
        except Exception as e:
            logger.error(f"[AdvancedQueryRewriter] Error rewriting query: {e}")
            
            # Fallback: simple expansion
            fallback = AdvancedRewrittenQuery(
                original_query=query,
                rewritten_query=f"{query} (survey OR review OR research)",
                keyword_queries=[query],
                exclude_terms=[],
                boost_terms=[],
                domain_hints=[],
                search_filters=filters or {}
            )
            
            return fallback, str(e)
    
    def rewrite_query_batch(self, queries: List[str], filters: Optional[Dict[str, str]] = None) -> List[Tuple[AdvancedRewrittenQuery, str]]:
        """Rewrite multiple queries (sequential for now, can be parallelized)"""
        results = []
        for query in queries:
            result = self.rewrite_query(query, filters)
            results.append(result)
        return results


def demo():
    """Demo the advanced query rewriter"""
    rewriter = AdvancedQueryRewriter()
    
    test_queries = [
        "text summarization in NLP",
        "object detection methods",
        "transformer architectures for NLP"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Original Query: {query}")
        print(f"{'='*80}")
        
        rewritten, raw = rewriter.rewrite_query(query)
        
        print(f"\nRewritten Query: {rewritten.rewritten_query}")
        print(f"\nKeyword Queries ({len(rewritten.keyword_queries)}):")
        for i, kq in enumerate(rewritten.keyword_queries, 1):
            print(f"  {i}. {kq}")
        
        print(f"\nExclude Terms: {', '.join(rewritten.exclude_terms)}")
        print(f"Boost Terms: {', '.join(rewritten.boost_terms)}")
        print(f"Domain Hints: {', '.join(rewritten.domain_hints)}")


if __name__ == "__main__":
    demo()

