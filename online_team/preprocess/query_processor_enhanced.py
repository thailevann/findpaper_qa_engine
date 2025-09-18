"""
Enhanced query processor with caching and fallback mechanisms
"""
import os
import json
import logging
import re
from typing import Tuple, List, Union, Optional, Dict
from collections import namedtuple
from dataclasses import dataclass
from pydantic import BaseModel, Field
from google import genai 
import hashlib
import time

from online_team.llms.prompts import QUERY_DECOMPOSER_PROMPT
from config import get_gemini_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define output structure
LLMProcessedQuery = namedtuple("LLMProcessedQuery",
                               ["rewritten_query", "keyword_query", "search_filters"])


@dataclass
class QueryProcessorConfig:
    """Configuration for query processor"""
    enable_caching: bool = True
    cache_ttl: int = 3600  # Cache TTL in seconds (1 hour)
    enable_fallback: bool = True
    gemini_timeout: float = 30.0  # Gemini API timeout in seconds
    use_regex_fallback: bool = True


class DecomposedQuery(BaseModel):
    earliest_search_year: str = Field(description="The earliest year to search for papers", default="")
    latest_search_year: str = Field(description="The latest year to search for papers", default="")
    venues: str = Field(description="Comma separated list of venues to search for papers", default="")
    authors: Union[List[str], str] = Field(description="List of authors to search for papers", default=[])
    field_of_study: str = Field(description="Comma separated list of field of study to search for papers", default="")
    rewritten_query: str = Field(description="The rewritten simplified query", default="")
    rewritten_query_for_keyword_search: str = Field(description="The rewritten query for keyword search", default="")


class QueryCache:
    """Simple in-memory cache for query processing results"""
    
    def __init__(self, ttl: int = 3600):
        self.cache: Dict[str, Tuple[LLMProcessedQuery, str, float]] = {}
        self.ttl = ttl
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query"""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def get(self, query: str) -> Optional[Tuple[LLMProcessedQuery, str]]:
        """Get cached result if valid"""
        key = self._get_cache_key(query)
        if key in self.cache:
            result, raw_content, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                logger.info(f"Cache hit for query: {query[:50]}...")
                return result, raw_content
            else:
                # Expired, remove from cache
                del self.cache[key]
        return None
    
    def set(self, query: str, result: LLMProcessedQuery, raw_content: str):
        """Cache the result"""
        key = self._get_cache_key(query)
        self.cache[key] = (result, raw_content, time.time())
        logger.info(f"Cached result for query: {query[:50]}...")
    
    def clear(self):
        """Clear all cached results"""
        self.cache.clear()
        logger.info("Query cache cleared")
    
    def size(self) -> int:
        """Get cache size"""
        return len(self.cache)


class RegexQueryProcessor:
    """Fallback regex-based query processor"""
    
    def __init__(self):
        # Common venue patterns
        self.venue_patterns = [
            r'\b(?:in|at|from)\s+([A-Z][a-zA-Z\s]+(?:Conference|Workshop|Symposium|Journal|Proceedings))\b',
            r'\b(?:NeurIPS|ICML|ICLR|AAAI|IJCAI|ACL|EMNLP|NAACL|CVPR|ICCV|ECCV)\b',
            r'\b(?:NIPS|ICML|ICLR|AAAI|IJCAI|ACL|EMNLP|NAACL|CVPR|ICCV|ECCV)\b'
        ]
        
        # Year patterns
        self.year_patterns = [
            r'\b(?:from|since|after)\s+(\d{4})\b',
            r'\b(?:before|until|up\s+to)\s+(\d{4})\b',
            r'\b(\d{4})\s*(?:to|-)\s*(\d{4})\b',
            r'\b(\d{4})\b'
        ]
        
        # Author patterns
        self.author_patterns = [
            r'\b(?:by|author|written\s+by)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b',
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:et\s+al\.?|and\s+others)\b'
        ]
    
    def extract_filters(self, query: str) -> Dict[str, str]:
        """Extract filters using regex patterns"""
        filters = {}
        
        # Extract years
        years = []
        for pattern in self.year_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    years.extend(match)
                else:
                    years.append(match)
        
        if years:
            years = [int(y) for y in years if y.isdigit()]
            if len(years) >= 2:
                filters["year"] = f"{min(years)}-{max(years)}"
            elif len(years) == 1:
                filters["year"] = f"{years[0]}-{years[0]}"
        
        # Extract venues
        venues = []
        for pattern in self.venue_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            venues.extend(matches)
        
        if venues:
            filters["venue"] = ",".join(venues)
        
        # Extract authors
        authors = []
        for pattern in self.author_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            authors.extend(matches)
        
        if authors:
            filters["authors"] = ",".join(authors)
        
        return filters
    
    def process_query(self, query: str) -> Tuple[LLMProcessedQuery, str]:
        """Process query using regex patterns"""
        logger.info("Using regex fallback for query processing")
        
        # Extract filters
        filters = self.extract_filters(query)
        
        # Clean query (remove filter-related terms)
        cleaned_query = query
        for pattern in self.year_patterns + self.venue_patterns + self.author_patterns:
            cleaned_query = re.sub(pattern, "", cleaned_query, flags=re.IGNORECASE)
        
        cleaned_query = re.sub(r'\s+', ' ', cleaned_query).strip()
        
        return LLMProcessedQuery(
            rewritten_query=cleaned_query,
            keyword_query=cleaned_query,
            search_filters=filters
        ), f"Regex fallback processing for: {query}"


class EnhancedQueryProcessor:
    """Enhanced query processor with caching and fallback mechanisms"""
    
    def __init__(self, config: Optional[QueryProcessorConfig] = None):
        self.config = config or QueryProcessorConfig()
        self.client = get_gemini_client()
        self.cache = QueryCache(self.config.cache_ttl) if self.config.enable_caching else None
        self.regex_processor = RegexQueryProcessor() if self.config.use_regex_fallback else None
    
    def decompose_query_with_gemini(self, query: str) -> Tuple[LLMProcessedQuery, str]:
        """
        Send query to Gemini, enforce JSON response, parse into DecomposedQuery
        """
        search_filters = {}
        
        prompt = QUERY_DECOMPOSER_PROMPT + query
        
        try:
            # Call Gemini with timeout
            resp = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            
            # Get response text
            content = resp.text.strip()
            logger.info(f"Raw Gemini output:\n{content}")
            
            # Find JSON in text (Gemini sometimes adds ```json)
            start = content.find("{")
            end = content.rfind("}") + 1
            json_str = content[start:end]
            
            data = json.loads(json_str)
            decomposed_query = {k: str(v) if isinstance(v, int) else v for k, v in data.items()}
            dq = DecomposedQuery(**decomposed_query)
            
            rewritten_query = dq.rewritten_query
            keyword_query = dq.rewritten_query_for_keyword_search
            
            # Build search filters
            if dq.earliest_search_year or dq.latest_search_year:
                earliest = dq.earliest_search_year or "1900"
                latest = dq.latest_search_year or "2030"
                search_filters["year"] = f"{earliest}-{latest}"
            
            if dq.venues:
                search_filters["venue"] = dq.venues
            if dq.field_of_study:
                search_filters["fieldsOfStudy"] = dq.field_of_study
            
            return LLMProcessedQuery(
                rewritten_query=rewritten_query,
                keyword_query=keyword_query,
                search_filters=search_filters
            ), content
            
        except Exception as e:
            logger.error(f"Error while decomposing query with Gemini: {e}")
            raise e
    
    def process_query(self, query: str) -> Tuple[LLMProcessedQuery, str]:
        """
        Process query with caching and fallback mechanisms
        
        Args:
            query: Input query string
            
        Returns:
            Tuple of (LLMProcessedQuery, raw_content)
        """
        # Check cache first
        if self.cache:
            cached_result = self.cache.get(query)
            if cached_result:
                return cached_result
        
        # Try Gemini processing
        try:
            result, raw_content = self.decompose_query_with_gemini(query)
            
            # Cache the result
            if self.cache:
                self.cache.set(query, result, raw_content)
            
            return result, raw_content
            
        except Exception as e:
            logger.error(f"Gemini processing failed: {e}")
            
            # Try regex fallback
            if self.regex_processor:
                try:
                    result, raw_content = self.regex_processor.process_query(query)
                    
                    # Cache the fallback result
                    if self.cache:
                        self.cache.set(query, result, raw_content)
                    
                    return result, raw_content
                    
                except Exception as fallback_error:
                    logger.error(f"Regex fallback also failed: {fallback_error}")
            
            # Ultimate fallback: return original query
            logger.warning("Using ultimate fallback: returning original query")
            fallback_result = LLMProcessedQuery(
                rewritten_query=query,
                keyword_query=query,
                search_filters={}
            )
            
            return fallback_result, f"Fallback processing for: {query}"
    
    def get_cache_stats(self) -> Dict[str, Union[int, bool]]:
        """Get cache statistics"""
        if not self.cache:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "size": self.cache.size(),
            "ttl": self.config.cache_ttl
        }
    
    def clear_cache(self):
        """Clear the query cache"""
        if self.cache:
            self.cache.clear()
    
    def get_processor_info(self) -> Dict[str, Union[str, bool, int, float]]:
        """Get processor configuration information"""
        return {
            "enable_caching": self.config.enable_caching,
            "cache_ttl": self.config.cache_ttl,
            "enable_fallback": self.config.enable_fallback,
            "gemini_timeout": self.config.gemini_timeout,
            "use_regex_fallback": self.config.use_regex_fallback,
            "cache_stats": self.get_cache_stats()
        }


# Backward compatibility function
def decompose_query_with_gemini(query: str) -> Tuple[LLMProcessedQuery, str]:
    """
    Backward compatibility function for existing code
    """
    processor = EnhancedQueryProcessor()
    return processor.process_query(query)


