import json
import logging
import re
import time
import hashlib
from typing import Tuple, List, Union, Optional, Dict
from collections import namedtuple
from dataclasses import dataclass
from pydantic import BaseModel, Field
import openai

from online_team.llms.prompts import QUERY_DECOMPOSER_PROMPT
import config  # import để openai.api_key đã được set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define output structure
LLMProcessedQuery = namedtuple("LLMProcessedQuery",
                               ["rewritten_query", "keyword_query", "search_filters"])


@dataclass
class QueryProcessorConfig:
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour
    enable_fallback: bool = True
    use_regex_fallback: bool = True


class DecomposedQuery(BaseModel):
    earliest_search_year: str = Field(default="")
    latest_search_year: str = Field(default="")
    venues: str = Field(default="")
    authors: Union[List[str], str] = Field(default=[])
    field_of_study: str = Field(default="")
    rewritten_query: str = Field(default="")
    rewritten_query_for_keyword_search: str = Field(default="")


class QueryCache:
    def __init__(self, ttl: int = 3600):
        self.cache: Dict[str, Tuple[LLMProcessedQuery, str, float]] = {}
        self.ttl = ttl
    
    def _get_cache_key(self, query: str) -> str:
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def get(self, query: str) -> Optional[Tuple[LLMProcessedQuery, str]]:
        key = self._get_cache_key(query)
        if key in self.cache:
            result, raw_content, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                logger.info(f"Cache hit for query: {query[:50]}...")
                return result, raw_content
            else:
                del self.cache[key]
        return None
    
    def set(self, query: str, result: LLMProcessedQuery, raw_content: str):
        key = self._get_cache_key(query)
        self.cache[key] = (result, raw_content, time.time())
        logger.info(f"Cached result for query: {query[:50]}...")

    # <-- Thêm method này
    def size(self) -> int:
        return len(self.cache)



class RegexQueryProcessor:
    # Giữ nguyên logic regex fallback như cũ
    def __init__(self):
        self.venue_patterns = [
            r'\b(?:in|at|from)\s+([A-Z][a-zA-Z\s]+(?:Conference|Workshop|Symposium|Journal|Proceedings))\b',
            r'\b(?:NeurIPS|ICML|ICLR|AAAI|IJCAI|ACL|EMNLP|NAACL|CVPR|ICCV|ECCV)\b'
        ]
        self.year_patterns = [
            r'\b(?:from|since|after)\s+(\d{4})\b',
            r'\b(?:before|until|up\s+to)\s+(\d{4})\b',
            r'\b(\d{4})\s*(?:to|-)\s*(\d{4})\b',
            r'\b(\d{4})\b'
        ]
        self.author_patterns = [
            r'\b(?:by|author|written\s+by)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b',
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:et\s+al\.?|and\s+others)\b'
        ]
    
    def extract_filters(self, query: str) -> Dict[str, str]:
        filters = {}
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
        
        venues = []
        for pattern in self.venue_patterns:
            venues.extend(re.findall(pattern, query, re.IGNORECASE))
        if venues:
            filters["venue"] = ",".join(venues)
        
        authors = []
        for pattern in self.author_patterns:
            authors.extend(re.findall(pattern, query, re.IGNORECASE))
        if authors:
            filters["authors"] = ",".join(authors)
        
        return filters
    
    def process_query(self, query: str) -> Tuple[LLMProcessedQuery, str]:
        logger.info("Using regex fallback for query processing")
        filters = self.extract_filters(query)
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
    def __init__(self, config: Optional[QueryProcessorConfig] = None):
        self.config = config or QueryProcessorConfig()
        self.cache = QueryCache(self.config.cache_ttl) if self.config.enable_caching else None
        self.regex_processor = RegexQueryProcessor() if self.config.use_regex_fallback else None
    
    def decompose_query_with_gpt(self, query: str) -> Tuple[LLMProcessedQuery, str]:
        search_filters = {}
        prompt = QUERY_DECOMPOSER_PROMPT + query
        try:
            # Ask model to produce JSON only in the assistant message to make parsing easier
            messages = [
                {"role": "system", "content": "You are a JSON generator. Respond ONLY with a single valid JSON object that matches the expected schema. Do not include any extra explanation."},
                {"role": "user", "content": prompt}
            ]
            resp = openai.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0
            )
            content = resp.choices[0].message.content
            if content is None:
                content = ""
            content = content.strip()
            logger.info(f"Raw GPT output:\n{content}")
            # Try to parse the whole content as JSON first (best case)
            try:
                data = json.loads(content)
            except Exception:
                # Fallback: extract a balanced JSON object substring from the content
                def _extract_json(s: str) -> Optional[str]:
                    start_idx = s.find('{')
                    if start_idx == -1:
                        return None
                    depth = 0
                    for i in range(start_idx, len(s)):
                        if s[i] == '{':
                            depth += 1
                        elif s[i] == '}':
                            depth -= 1
                            if depth == 0:
                                return s[start_idx:i+1]
                    return None

                json_str = _extract_json(content)
                if not json_str:
                    # nothing parseable
                    logger.error("Failed to extract JSON substring from LLM output")
                    raise ValueError("No JSON found in LLM output")
                data = json.loads(json_str)
            decomposed_query = {k: str(v) if isinstance(v, int) else v for k, v in data.items()}
            dq = DecomposedQuery(**decomposed_query)
            
            rewritten_query = dq.rewritten_query
            keyword_query = dq.rewritten_query_for_keyword_search
            
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
            logger.error(f"Error while decomposing query with GPT: {e}")
            logger.debug("Full GPT output (for debugging): %s", locals().get('content', None))
            raise e
    
    def process_query(self, query: str) -> Tuple[LLMProcessedQuery, str]:
        if self.cache:
            cached_result = self.cache.get(query)
            if cached_result:
                return cached_result
        
        try:
            result, raw_content = self.decompose_query_with_gpt(query)
            if self.cache:
                self.cache.set(query, result, raw_content)
            return result, raw_content
        except Exception as e:
            logger.error(f"GPT processing failed: {e}")
            if self.regex_processor:
                try:
                    result, raw_content = self.regex_processor.process_query(query)
                    if self.cache:
                        self.cache.set(query, result, raw_content)
                    return result, raw_content
                except Exception as fallback_error:
                    logger.error(f"Regex fallback also failed: {fallback_error}")
            fallback_result = LLMProcessedQuery(
                rewritten_query=query,
                keyword_query=query,
                search_filters={}
            )
            return fallback_result, f"Fallback processing for: {query}"
    
    def get_cache_stats(self) -> Dict[str, Union[int, bool]]:
        if not self.cache:
            return {"enabled": False}
        return {"enabled": True, "size": self.cache.size(), "ttl": self.config.cache_ttl}
    
    def clear_cache(self):
        if self.cache:
            self.cache.clear()
    
    def get_processor_info(self) -> Dict[str, Union[str, bool, int, float]]:
        return {
            "enable_caching": self.config.enable_caching,
            "cache_ttl": self.config.cache_ttl,
            "enable_fallback": self.config.enable_fallback,
            "use_regex_fallback": self.config.use_regex_fallback,
            "cache_stats": self.get_cache_stats()
        }


# Backward compatibility
def decompose_query_with_gpt(query: str) -> Tuple[LLMProcessedQuery, str]:
    processor = EnhancedQueryProcessor()
    return processor.process_query(query)