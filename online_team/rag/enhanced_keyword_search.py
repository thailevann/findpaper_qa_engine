"""
Enhanced Keyword Search with query expansion and negative filtering.

Features:
1. Multiple keyword query execution with different strategies
2. Negative term filtering to exclude irrelevant results
3. Boolean query support (AND, OR, intitle:, etc.)
4. Result aggregation and deduplication
"""

from elasticsearch import Elasticsearch
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class EnhancedKeywordSearchConfig:
    """Configuration for enhanced keyword search"""
    top_k: int = 50
    title_boost: float = 5.0
    abstract_boost: float = 3.0
    multi_match_boost: float = 1.0
    use_query_expansion: bool = True
    use_negative_filtering: bool = True
    aggregation_strategy: str = "union"  # "union" or "intersection"
    max_queries_to_execute: int = 5  # Limit on keyword query variations


class EnhancedKeywordSearch:
    """
    Enhanced keyword search with multiple query strategies and filtering.
    """
    
    def __init__(
        self,
        es_url: str = "http://localhost:9200",
        index_name: str = "papers_text",
        config: Optional[EnhancedKeywordSearchConfig] = None
    ):
        self.es = Elasticsearch(es_url, request_timeout=120)
        self.index_name = index_name
        self.config = config or EnhancedKeywordSearchConfig()
    
    def _parse_special_query(self, query_text: str) -> Dict:
        """
        Parse special query syntax like intitle:"term" AND/OR operators.
        Returns a structured ES query.
        """
        # Check for intitle: syntax
        if "intitle:" in query_text.lower():
            # Parse intitle:"text" patterns
            import re
            intitle_pattern = r'intitle:\s*["\']([^"\']+)["\']|intitle:(\S+)'
            intitle_matches = re.findall(intitle_pattern, query_text, re.IGNORECASE)
            
            should_clauses = []
            must_clauses = []
            
            # Add intitle matches
            for match in intitle_matches:
                title_term = match[0] if match[0] else match[1]
                must_clauses.append({
                    "match_phrase": {
                        "title": {
                            "query": title_term,
                            "boost": self.config.title_boost * 2  # Extra boost for explicit title search
                        }
                    }
                })
            
            # Remove intitle: parts for remaining query
            remaining_query = re.sub(intitle_pattern, "", query_text, flags=re.IGNORECASE)
            
            # Parse AND/OR logic in remaining query
            if " AND " in remaining_query.upper():
                and_terms = re.split(r'\s+AND\s+', remaining_query, flags=re.IGNORECASE)
                for term in and_terms:
                    term = term.strip().strip('"').strip("'")
                    if term and term.upper() not in ["AND", "OR"]:
                        must_clauses.append({
                            "multi_match": {
                                "query": term,
                                "fields": ["title^2", "abstract"]
                            }
                        })
            
            if " OR " in remaining_query.upper():
                or_terms = re.split(r'\s+OR\s+', remaining_query, flags=re.IGNORECASE)
                for term in or_terms:
                    term = term.strip().strip('"').strip("'")
                    if term and term.upper() not in ["AND", "OR"]:
                        should_clauses.append({
                            "multi_match": {
                                "query": term,
                                "fields": ["title^2", "abstract"]
                            }
                        })
            
            # If no explicit AND/OR, treat remaining as should match
            if not should_clauses and not (" AND " in remaining_query.upper() or " OR " in remaining_query.upper()):
                remaining_query = remaining_query.strip()
                if remaining_query:
                    should_clauses.append({
                        "multi_match": {
                            "query": remaining_query,
                            "fields": ["title^2", "abstract"]
                        }
                    })
            
            return {
                "bool": {
                    "must": must_clauses,
                    "should": should_clauses,
                    "minimum_should_match": 1 if should_clauses and not must_clauses else 0
                }
            }
        
        # Handle standard AND/OR without intitle
        elif " AND " in query_text.upper() or " OR " in query_text.upper():
            import re
            must_clauses = []
            should_clauses = []
            
            if " AND " in query_text.upper():
                and_terms = re.split(r'\s+AND\s+', query_text, flags=re.IGNORECASE)
                for term in and_terms:
                    term = term.strip().strip('"').strip("'")
                    if term and term.upper() not in ["AND", "OR"]:
                        must_clauses.append({
                            "multi_match": {
                                "query": term,
                                "fields": ["title^3", "abstract"]
                            }
                        })
            
            if " OR " in query_text.upper():
                or_terms = re.split(r'\s+OR\s+', query_text, flags=re.IGNORECASE)
                for term in or_terms:
                    term = term.strip().strip('"').strip("'")
                    if term and term.upper() not in ["AND", "OR"]:
                        should_clauses.append({
                            "multi_match": {
                                "query": term,
                                "fields": ["title^3", "abstract"]
                            }
                        })
            
            return {
                "bool": {
                    "must": must_clauses,
                    "should": should_clauses,
                    "minimum_should_match": 1 if should_clauses and not must_clauses else 0
                }
            }
        
        # Default: simple multi-match
        return {
            "multi_match": {
                "query": query_text,
                "fields": ["title^3", "abstract"],
                "type": "best_fields"
            }
        }
    
    def _build_query_with_exclusions(
        self,
        query_text: str,
        exclude_terms: Optional[List[str]] = None,
        filters: Optional[Dict[str, str]] = None
    ) -> Dict:
        """Build ES query with negative filtering"""
        
        # Parse query structure
        parsed_query = self._parse_special_query(query_text)
        
        # Build bool query with must_not for exclusions
        must_not_clauses = []
        if exclude_terms and self.config.use_negative_filtering:
            for term in exclude_terms:
                must_not_clauses.append({
                    "multi_match": {
                        "query": term,
                        "fields": ["title", "abstract"],
                        "type": "phrase"
                    }
                })
        
        # Wrap in bool query
        body = {
            "size": self.config.top_k,
            "_source": ["paper_id", "title", "abstract"],
            "query": {
                "bool": {
                    "must": [parsed_query],
                    "must_not": must_not_clauses
                }
            },
            "highlight": {
                "fields": {
                    "title": {"number_of_fragments": 1},
                    "abstract": {"number_of_fragments": 3}
                }
            }
        }
        
        # Apply additional filters
        if filters:
            for field, value in filters.items():
                if ":" in str(value):
                    gte, lte = value.split(":")
                    body["query"]["bool"]["must"].append({
                        "range": {field: {"gte": gte, "lte": lte}}
                    })
                else:
                    body["query"]["bool"]["must"].append({
                        "term": {field: value}
                    })
        
        return body
    
    def search_single_query(
        self,
        query_text: str,
        exclude_terms: Optional[List[str]] = None,
        filters: Optional[Dict[str, str]] = None,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """Execute a single keyword query"""
        top_k = top_k or self.config.top_k
        
        body = self._build_query_with_exclusions(query_text, exclude_terms, filters)
        body["size"] = top_k
        
        logger.debug(f"[EnhancedKeywordSearch] Query: {query_text[:100]}")
        
        try:
            res = self.es.search(index=self.index_name, body=body)
            hits = res["hits"]["hits"]
            
            results = []
            for hit in hits:
                src = hit.get("_source", {})
                pid = src.get("paper_id")
                highlight = hit.get("highlight", {})
                score = hit.get("_score", 0)
                
                # Extract highlighted fragments
                if "title" in highlight:
                    for frag in highlight["title"]:
                        results.append({
                            "paper_id": pid,
                            "field": "title",
                            "text": frag,
                            "highlight": highlight["title"],
                            "score": score,
                            "source": "enhanced_keyword"
                        })
                
                if "abstract" in highlight:
                    for frag in highlight["abstract"]:
                        results.append({
                            "paper_id": pid,
                            "field": "abstract",
                            "text": frag,
                            "highlight": highlight["abstract"],
                            "score": score,
                            "source": "enhanced_keyword"
                        })
            
            logger.info(f"[EnhancedKeywordSearch] Query '{query_text[:50]}...' returned {len(results)} fragments from {len(set(r['paper_id'] for r in results))} papers")
            return results
            
        except Exception as e:
            logger.error(f"[EnhancedKeywordSearch] Error executing query '{query_text[:50]}...': {e}")
            return []
    
    def search_multi_query(
        self,
        query_texts: List[str],
        exclude_terms: Optional[List[str]] = None,
        filters: Optional[Dict[str, str]] = None,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        Execute multiple keyword queries and aggregate results.
        
        Args:
            query_texts: List of keyword query variations
            exclude_terms: Terms to exclude from results
            filters: Additional search filters
            top_k: Number of top results per query
            
        Returns:
            Aggregated and deduplicated results
        """
        top_k = top_k or self.config.top_k
        
        # Limit number of queries to execute
        if len(query_texts) > self.config.max_queries_to_execute:
            logger.warning(f"[EnhancedKeywordSearch] Limiting queries from {len(query_texts)} to {self.config.max_queries_to_execute}")
            query_texts = query_texts[:self.config.max_queries_to_execute]
        
        all_results = []
        seen_fragments = set()  # For deduplication: (paper_id, field, text_snippet)
        
        for i, query_text in enumerate(query_texts, 1):
            logger.info(f"[EnhancedKeywordSearch] Executing query {i}/{len(query_texts)}: {query_text[:60]}...")
            
            results = self.search_single_query(
                query_text=query_text,
                exclude_terms=exclude_terms,
                filters=filters,
                top_k=top_k
            )
            
            # Deduplicate based on paper_id + field + text snippet
            for result in results:
                # Create a unique key for this fragment
                text_snippet = result["text"][:100]  # Use first 100 chars for dedup
                fragment_key = (result["paper_id"], result["field"], text_snippet)
                
                if fragment_key not in seen_fragments:
                    seen_fragments.add(fragment_key)
                    # Mark which query found this
                    result["query_index"] = i
                    result["query_text"] = query_text[:50]
                    all_results.append(result)
        
        # Sort by score
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # Limit to top_k final results
        final_results = all_results[:top_k * 2]  # Allow more results for downstream reranking
        
        unique_papers = len(set(r["paper_id"] for r in final_results))
        logger.info(f"[EnhancedKeywordSearch] Multi-query search completed: {len(final_results)} fragments from {unique_papers} unique papers")
        
        return final_results
    
    def search(
        self,
        query_texts: List[str],
        exclude_terms: Optional[List[str]] = None,
        filters: Optional[Dict[str, str]] = None,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        Main search interface supporting both single and multi-query.
        
        Args:
            query_texts: Single query string or list of query variations
            exclude_terms: Terms to filter out
            filters: Additional search filters
            top_k: Number of results to return
        """
        # Handle both single string and list inputs
        if isinstance(query_texts, str):
            query_texts = [query_texts]
        
        if not query_texts:
            logger.warning("[EnhancedKeywordSearch] No queries provided")
            return []
        
        # Single query optimization
        if len(query_texts) == 1:
            return self.search_single_query(query_texts[0], exclude_terms, filters, top_k)
        
        # Multi-query execution
        return self.search_multi_query(query_texts, exclude_terms, filters, top_k)


def demo():
    """Demo the enhanced keyword search"""
    config = EnhancedKeywordSearchConfig(
        top_k=20,
        use_query_expansion=True,
        use_negative_filtering=True
    )
    
    searcher = EnhancedKeywordSearch(config=config)
    
    # Test queries
    keyword_queries = [
        'intitle:"text summarization" AND (extractive OR abstractive)',
        '"abstractive summarization" (BART OR PEGASUS OR T5)',
        'summarization survey NLP'
    ]
    
    exclude_terms = ["economics", "finance", "dialogue segmentation"]
    
    print(f"\n{'='*80}")
    print(f"Testing Enhanced Keyword Search")
    print(f"{'='*80}")
    print(f"\nKeyword Queries:")
    for i, q in enumerate(keyword_queries, 1):
        print(f"  {i}. {q}")
    print(f"\nExclude Terms: {', '.join(exclude_terms)}")
    
    results = searcher.search(
        query_texts=keyword_queries,
        exclude_terms=exclude_terms,
        top_k=20
    )
    
    print(f"\n{'='*80}")
    print(f"Results: {len(results)} fragments from {len(set(r['paper_id'] for r in results))} papers")
    print(f"{'='*80}")
    
    for i, result in enumerate(results[:5], 1):
        print(f"\n{i}. Paper: {result['paper_id']}")
        print(f"   Field: {result['field']}")
        print(f"   Score: {result['score']:.4f}")
        print(f"   Query: {result.get('query_text', 'N/A')}")
        print(f"   Text: {result['text'][:150]}...")


if __name__ == "__main__":
    demo()

