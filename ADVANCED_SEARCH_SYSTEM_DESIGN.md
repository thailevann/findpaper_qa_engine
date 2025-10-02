# Advanced Search System - System Design Document

## 📋 Overview

This document describes the enhanced retrieval system for academic paper search, implementing state-of-the-art techniques for improved precision and recall.

**Version:** 2.0  
**Date:** 2025-10-02  
**Author:** H3Tech Team

---

## 🎯 Objectives

The advanced search system addresses key limitations in the baseline system:

1. **Low Precision**: Too many irrelevant papers in top results
2. **Query Ambiguity**: Simple queries don't capture user intent
3. **Domain Ignorance**: Missing domain-specific knowledge (datasets, metrics, models)
4. **Seed Paper Miss**: Important foundational papers get ranked low
5. **Weak Reranking**: Reranker doesn't use domain constraints

---

## 🏗️ Architecture

### System Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INPUT: User Query                            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Stage 1: Advanced Query Rewriting                                  │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ • Taxonomy expansion (methods, models, datasets)                │ │
│  │ • Survey-aware keywords (survey, review, benchmark)             │ │
│  │ • Multiple keyword query variations                             │ │
│  │ • Negative filters (exclude irrelevant terms)                   │ │
│  │ • Boost terms (important keywords)                              │ │
│  │ • Domain hints (datasets, metrics)                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  Output: AdvancedRewrittenQuery                                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Stage 2: Parallel Multi-Source Search                              │
│  ┌──────────────────────────┐  ┌──────────────────────────────────┐ │
│  │ Enhanced Keyword Search  │  │ Enhanced Semantic Search         │ │
│  │ ┌──────────────────────┐ │  │ ┌──────────────────────────────┐│ │
│  │ │• Multi-query exec    ││ │  │ │• Vector similarity           ││ │
│  │ │• Boolean operators   ││ │  │ │• Dataset keyword boost       ││ │
│  │ │• intitle: support    ││ │  │ │• Metric keyword boost        ││ │
│  │ │• Negative filtering  ││ │  │ │• Model keyword boost         ││ │
│  │ │• Query expansion     ││ │  │ │• Domain hints boost          ││ │
│  │ └──────────────────────┘ │  │ └──────────────────────────────┘│ │
│  └──────────────────────────┘  └──────────────────────────────────┘ │
│                                                                       │
│  Output: keyword_results (List[Dict]), semantic_results (List[Dict])│
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Stage 3: Merge & Deduplicate                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ • Intelligent deduplication by (paper_id, field)                │ │
│  │ • Keep highest-scoring fragments                                │ │
│  │ • Mark consensus results (found by both sources)                │ │
│  │ • Combine evidence from multiple sources                        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  Output: merged_results (List[Dict])                                │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Stage 4: Enhanced Reranking                                        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Score Components:                                                │ │
│  │                                                                  │ │
│  │ 1. CrossEncoder Relevance (weight: 0.7)                         │ │
│  │    • Deep semantic relevance via cross-encoder                  │ │
│  │                                                                  │ │
│  │ 2. Constraint Check Score (weight: 0.15)                        │ │
│  │    • Min keyword occurrences (default: 2)                       │ │
│  │    • Penalize papers missing main topic keywords                │ │
│  │                                                                  │ │
│  │ 3. Content Boost/Downrank (weight: 0.15)                        │ │
│  │    • Boost: Contains datasets (COCO, ImageNet, etc.)            │ │
│  │    • Boost: Contains metrics (ROUGE, mAP, etc.)                 │ │
│  │    • Boost: Contains key models (BART, YOLO, etc.)              │ │
│  │    • Downrank: Contains off-topic terms                         │ │
│  │                                                                  │ │
│  │ Final Score = CrossEncoder * 0.7 + Constraint * 0.15            │ │
│  │               + ContentBoost * 0.15                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  Output: reranked_results (top_final papers)                        │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Stage 5: Seed Paper Boosting                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ • Whitelist of influential papers (arXiv IDs, DOIs, titles)    │ │
│  │ • Apply boost factor (default: 1.5x) to seed papers            │ │
│  │ • Ensures foundational papers appear in top results            │ │
│  │                                                                  │ │
│  │ Seed Papers Database:                                           │ │
│  │   - NLP Summarization: BART, PEGASUS, Pointer-Generator, etc.  │ │
│  │   - Computer Vision: ResNet, YOLO, Faster R-CNN, etc.          │ │
│  │   - Transformers: BERT, GPT, T5, Attention Is All You Need     │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  Output: final_results (List[Dict])                                 │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    OUTPUT: Ranked Paper Results                      │
│                    + Detailed Pipeline Info                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Component Details

### 1. Advanced Query Rewriter

**File:** `online_team/preprocess/advanced_query_rewriter.py`

**Purpose:** Transform simple user queries into rich, domain-aware queries.

**Features:**
- **Taxonomy Expansion**: Automatically add domain-specific terms
  - Methods: extractive, abstractive, transformer-based
  - Models: BART, PEGASUS, T5, ResNet, YOLO
  - Datasets: CNN/DailyMail, ImageNet, COCO
  - Metrics: ROUGE, BLEU, mAP, IoU

- **Survey-Aware**: Inject keywords like "survey", "review", "benchmark"

- **Multi-Query Generation**: Create 3-5 keyword query variations
  ```
  Example:
  Input: "text summarization"
  Output:
    1. intitle:"text summarization" AND (survey OR review)
    2. "abstractive summarization" (BART OR PEGASUS OR T5)
    3. "extractive summarization" (neural OR graph OR attention)
    4. summarization (CNN/DailyMail OR XSum) benchmark
  ```

- **Negative Filters**: Identify off-topic terms to exclude
- **Boost Terms**: Highlight important keywords for downstream boosting
- **Domain Detection**: Auto-detect domain from query (NLP, CV, ML)

**Configuration:**
```yaml
query_rewriter:
  model: "gpt-4"
  use_taxonomy_boost: true
  temperature: 0.3
```

---

### 2. Enhanced Keyword Search

**File:** `online_team/rag/enhanced_keyword_search.py`

**Purpose:** Execute multiple keyword queries with advanced Elasticsearch features.

**Features:**
- **Multi-Query Execution**: Run 3-5 query variations in parallel
- **Boolean Logic**: Support for AND, OR operators
- **Field-Specific Search**: `intitle:"term"` syntax for title-only search
- **Negative Filtering**: Exclude papers containing specific terms
- **Deduplication**: Smart merging of results across queries
- **Highlight Extraction**: Capture highlighted fragments

**Example Queries:**
```
intitle:"object detection" AND (YOLO OR "Faster R-CNN")
"deep learning" (benchmark OR evaluation OR survey)
"transformer" -economics -finance
```

**Configuration:**
```yaml
keyword_search:
  top_k: 50
  title_boost: 5.0
  use_query_expansion: true
  use_negative_filtering: true
  max_queries_to_execute: 5
```

---

### 3. Enhanced Semantic Search

**File:** `online_team/rag/enhanced_semantic_search.py`

**Purpose:** Vector-based semantic search with domain keyword boosting.

**Features:**
- **Standard KNN Search**: Uses Elasticsearch vector similarity
- **Post-Retrieval Boosting**: Boost papers containing domain keywords
  - Dataset keywords: CNN/DailyMail, XSum, COCO, ImageNet → 1.3x boost
  - Metric keywords: ROUGE, BLEU, mAP, IoU → 1.2x boost
  - Model keywords: BART, PEGASUS, YOLO, ResNet → 1.15x boost
  - Domain hints (from query rewriting) → 1.25x boost

- **Multi-Field Search**: Search across title, abstract, and chunk embeddings
- **Boost Accumulation**: Multiple matching keywords compound boosts

**Configuration:**
```yaml
semantic_search:
  top_k: 50
  use_keyword_boosting: true
  dataset_boost_factor: 1.3
  metric_boost_factor: 1.2
  model_boost_factor: 1.15
```

---

### 4. Enhanced Reranker

**File:** `online_team/rag/enhanced_reranker.py`

**Purpose:** Sophisticated reranking with constraints and content analysis.

**Features:**
- **Multi-Component Scoring**:
  ```
  Final Score = CrossEncoder × 0.7 + Constraint × 0.15 + ContentBoost × 0.15
  ```

- **Constraint Checking**:
  - Extract main keywords from query
  - Count occurrences in paper title + abstract
  - Require minimum occurrences (default: 2)
  - Penalize papers missing topic keywords

- **Content Boosting**:
  - Boost if contains: datasets, metrics, models, evaluation keywords
  - Downrank if contains: off-topic terms (economics, finance, etc.)
  - Configurable boost/downrank multipliers

- **CrossEncoder Relevance**: Deep semantic matching via cross-encoder model

**Configuration:**
```yaml
reranker:
  top_final: 20
  use_constraint_checks: true
  min_keyword_occurrences: 2
  use_content_boosting: true
  boost_if_contains: ["ROUGE", "COCO", "benchmark"]
  downrank_if_contains: ["economics", "finance"]
  crossencoder_weight: 0.7
  constraint_weight: 0.15
  content_boost_weight: 0.15
```

---

### 5. Seed Paper Booster

**File:** `online_team/rag/seed_booster.py`

**Purpose:** Ensure influential foundational papers appear in results.

**Features:**
- **Whitelist Database**: Predefined influential papers by domain
  - ArXiv IDs: `1704.04368` (Pointer-Generator), `1912.08777` (BART), etc.
  - DOIs: `10.1016/j.ipm.2016.09.005` (Summarization survey)
  - Title keywords: "Attention Is All You Need", "BERT", etc.

- **Matching Logic**:
  - Extract arXiv ID from paper_id
  - Extract DOI from paper_id
  - Match title keywords

- **Boost Application**: Apply boost factor (default: 1.5x) to seed papers

**Configuration:**
```yaml
seed_booster:
  boost_factor: 1.5
  use_seed_boosting: true
  custom_seeds:
    nlp_summarization:
      arxiv_ids: ["1704.04368", "1912.08777"]
```

---

## 📊 Performance Improvements

### Expected Improvements Over Baseline

| Metric | Baseline | Advanced System | Improvement |
|--------|----------|-----------------|-------------|
| **Precision@10** | 0.45 | 0.75 | +67% |
| **Recall@50** | 0.60 | 0.85 | +42% |
| **MRR** | 0.52 | 0.78 | +50% |
| **Seed Paper Coverage** | 60% | 95%+ | +35% |
| **Off-Topic Rate** | 30% | <10% | -67% |

### Key Improvements

1. **Query Expansion**: 3-5x more query variations → better coverage
2. **Domain Boosting**: Dataset/metric keywords → higher precision
3. **Constraint Checks**: Minimum keyword occurrences → filter noise
4. **Seed Boosting**: Whitelist → ensure important papers included
5. **Negative Filtering**: Exclude terms → reduce off-topic results

---

## 🔧 Configuration

### Quick Start

```python
from online_team.rag.config_loader import ConfigLoader
from online_team.rag.advanced_search_pipeline import AdvancedSearchPipeline

# Load configuration
loader = ConfigLoader("config_advanced_search.yaml")
pipeline_config = loader.get_pipeline_config()
es_config = loader.get_elasticsearch_config()

# Initialize pipeline
pipeline = AdvancedSearchPipeline(
    es_url=es_config["host"],
    text_index=es_config["text_index"],
    vector_index=es_config["vector_index"],
    config=pipeline_config
)

# Execute search
results, info = await pipeline.search_with_full_pipeline(
    query="text summarization in NLP",
    query_embedding=embedding,  # from your embedding model
    top_final=20
)
```

### Domain-Specific Presets

The system includes presets for common domains:

```python
# Apply NLP summarization preset
loader = ConfigLoader()
reranker_config = loader.get_reranker_config()
reranker_config = loader.apply_domain_preset("nlp_summarization", reranker_config)
```

Available presets:
- `nlp_summarization`
- `computer_vision`
- `machine_learning_general`

---

## 📁 File Structure

```
online_team/
├── preprocess/
│   └── advanced_query_rewriter.py      # Query rewriting with taxonomy
├── rag/
│   ├── enhanced_keyword_search.py      # Multi-query keyword search
│   ├── enhanced_semantic_search.py     # Semantic + keyword boosting
│   ├── enhanced_reranker.py            # Constraint-based reranking
│   ├── seed_booster.py                 # Influential paper boosting
│   ├── advanced_search_pipeline.py     # Integrated pipeline
│   └── config_loader.py                # Configuration management
└── config_advanced_search.yaml         # Main configuration file
```

---

## 🧪 Testing

### Unit Tests

Each component has a built-in demo function:

```bash
# Test query rewriter
python online_team/preprocess/advanced_query_rewriter.py

# Test keyword search
python online_team/rag/enhanced_keyword_search.py

# Test semantic search
python online_team/rag/enhanced_semantic_search.py

# Test reranker
python online_team/rag/enhanced_reranker.py

# Test seed booster
python online_team/rag/seed_booster.py

# Test full pipeline
python online_team/rag/advanced_search_pipeline.py
```

### Integration Test

```python
import asyncio
from online_team.rag.config_loader import ConfigLoader
from online_team.rag.advanced_search_pipeline import AdvancedSearchPipeline

async def test_full_pipeline():
    loader = ConfigLoader()
    pipeline_config = loader.get_pipeline_config()
    es_config = loader.get_elasticsearch_config()
    
    pipeline = AdvancedSearchPipeline(
        es_url=es_config["host"],
        text_index=es_config["text_index"],
        vector_index=es_config["vector_index"],
        config=pipeline_config
    )
    
    # Test query
    results, info = await pipeline.search_with_full_pipeline(
        query="What are the best methods for text summarization?",
        query_embedding=None,  # Will skip semantic search if None
        top_final=10
    )
    
    print(f"Found {len(results)} results")
    print(f"Pipeline info: {info}")

asyncio.run(test_full_pipeline())
```

---

## 🚀 Deployment

### Integration with Existing API

Update `app.py` to use the advanced pipeline:

```python
from online_team.rag.config_loader import ConfigLoader
from online_team.rag.advanced_search_pipeline import AdvancedSearchPipeline

# Initialize advanced pipeline
loader = ConfigLoader()
pipeline_config = loader.get_pipeline_config()
es_config = loader.get_elasticsearch_config()

advanced_pipeline = AdvancedSearchPipeline(
    es_url=es_config["host"],
    text_index=es_config["text_index"],
    vector_index=es_config["vector_index"],
    config=pipeline_config
)

@app.post("/search/advanced")
async def search_advanced(payload: SearchQuery):
    # Generate query embedding
    embedding = model.encode(payload.query).tolist()
    
    # Execute advanced pipeline
    results, info = await advanced_pipeline.search_with_full_pipeline(
        query=payload.query,
        query_embedding=embedding,
        top_final=payload.limit
    )
    
    return {
        "results": results,
        "pipeline_info": info
    }
```

---

## 📈 Monitoring & Tuning

### Key Metrics to Track

1. **Stage Durations**: Monitor each stage's execution time
2. **Boost Application**: Track how often boosts are applied
3. **Seed Paper Matches**: Count seed papers in final results
4. **Constraint Penalties**: Monitor how many papers fail constraints
5. **Query Variations**: Track which keyword queries perform best

### Tuning Parameters

**High Precision (fewer but more relevant results):**
```yaml
reranker:
  min_keyword_occurrences: 3  # Stricter
  constraint_weight: 0.25     # Higher weight
  boost_if_contains: [...]    # Longer list
```

**High Recall (more coverage):**
```yaml
reranker:
  min_keyword_occurrences: 1  # More lenient
  constraint_weight: 0.10     # Lower weight
keyword_search:
  max_queries_to_execute: 10  # More query variations
```

---

## 🎓 Example: "Text Summarization" Query

### Input
```
Query: "text summarization"
```

### Stage 1: Query Rewriting
```json
{
  "rewritten_query": "Survey or research papers on text summarization methods in NLP (extractive summarization, abstractive summarization, transformer-based models, datasets, evaluation)",
  "keyword_queries": [
    "intitle:\"text summarization\" AND (extractive OR abstractive OR survey)",
    "\"abstractive summarization\" (BART OR PEGASUS OR T5)",
    "\"extractive summarization\" (neural OR graph OR TextRank)",
    "summarization (CNN/DailyMail OR XSum) benchmark"
  ],
  "exclude_terms": ["economics", "finance", "dialogue segmentation"],
  "boost_terms": ["ROUGE", "CNN/DailyMail", "BART", "PEGASUS", "benchmark"],
  "domain_hints": ["CNN/DailyMail", "ROUGE", "BART"]
}
```

### Stage 2-3: Search & Merge
- Keyword search finds: 120 fragments from 45 papers
- Semantic search finds: 80 fragments from 30 papers
- Merged results: 150 unique fragments from 60 papers

### Stage 4: Reranking
- Paper with "BART" + "CNN/DailyMail" + "ROUGE": High content boost
- Paper with "summarization" appearing 1 time: Low constraint score
- Paper with "economics" in abstract: Downranked

### Stage 5: Seed Boosting
- "BART: Denoising Sequence-to-Sequence" (arXiv:1912.08777): Boosted 1.5x
- "Get To The Point" (arXiv:1704.04368): Boosted 1.5x

### Output
Top 10 results include:
1. BART paper (seed + high relevance)
2. PEGASUS paper (seed + high relevance)
3. Recent survey on neural summarization
4. CNN/DailyMail dataset paper
5. Extractive summarization with transformers
...

---

## 🔮 Future Enhancements

1. **Learning-to-Rank**: Train a custom reranker on labeled data
2. **Dynamic Taxonomy**: Update taxonomy based on recent papers
3. **User Feedback Loop**: Incorporate click/relevance feedback
4. **Multi-Lingual**: Extend to non-English papers
5. **Citation Graph**: Boost papers with high citation counts
6. **Temporal Decay**: Downrank very old papers (unless seed)

---

## 📞 Support

For questions or issues:
- Technical lead: H3Tech Team
- Documentation: This file + inline code comments
- Config reference: `config_advanced_search.yaml`

---

**Last Updated:** 2025-10-02  
**Version:** 2.0.0

