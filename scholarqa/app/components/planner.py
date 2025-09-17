"""
Planning component for generating structured outlines and clustering quotes.
"""
from typing import List, Dict, Any
import logging
import os
import json
from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

load_dotenv()
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

logger = logging.getLogger(__name__)


class OutlinePlanner:
    """Component responsible for planning and clustering quotes into structured outlines."""
    
    def __init__(self, model: str = None):
        self.model = model or DEFAULT_OPENAI_MODEL
        self.client = self._get_openai_client()
    
    def _get_openai_client(self) -> "OpenAI":
        if OpenAI is None:
            raise RuntimeError("openai package is not installed. Add 'openai' to requirements and set OPENAI_API_KEY.")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in environment.")
        return OpenAI(api_key=api_key)
    
    def generate_outline(self, query: str, quotes: List[Dict[str, Any]], 
                       max_sections: int = 6) -> Dict[str, Any]:
        """
        Generate a structured outline and cluster quotes into sections.
        
        Args:
            query: User query
            quotes: List of extracted quotes with metadata
            max_sections: Maximum number of sections to generate
            
        Returns:
            Dictionary containing outline structure and clustered quotes
        """
        logger.info(f"Generating outline for {len(quotes)} quotes")
        
        if not quotes:
            return {
                "outline": [],
                "clustered_quotes": {},
                "processing_trace": {"step": "outline_generation", "quotes_processed": 0}
            }
        
        # Prepare quotes for LLM
        quotes_text = []
        for i, quote in enumerate(quotes):
            quotes_text.append(f"[{i+1}] {quote['quote_text']}")
        
        # System prompt for outline generation
        system_prompt = (
            "You are an expert research assistant. Given a user question and extracted quotes from research papers, "
            "generate a structured outline that organizes the quotes into logical sections. "
            "Always include these standard sections when relevant: Background, Methods, Results, Discussion, Open Questions. "
            "Group quotes that belong to the same topic or theme together. "
            "Return a JSON structure with sections and quote assignments."
        )
        
        user_prompt = (
            f"User question: {query}\n\n"
            f"Extracted quotes:\n"
            + "\n\n".join(quotes_text) +
            f"\n\nInstructions:\n"
            f"- Generate at most {max_sections} logical sections\n"
            f"- Always include 'Background' as the first section if relevant\n"
            f"- Assign each quote (by number) to appropriate sections\n"
            f"- Return JSON: {{\"sections\": [{{\"name\": str, \"description\": str, \"quote_indices\": [int, ...]}}]}}"
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content or '{"sections": []}'
            outline_data = json.loads(content)
            
            # Process outline and cluster quotes
            sections = outline_data.get("sections", [])
            clustered_quotes = {}
            
            for section in sections:
                section_name = section.get("name", "Unnamed Section")
                section_description = section.get("description", "")
                quote_indices = section.get("quote_indices", [])
                
                # Get quotes for this section
                section_quotes = []
                for idx in quote_indices:
                    if 0 <= idx - 1 < len(quotes):  # Convert to 0-based index
                        section_quotes.append(quotes[idx - 1])
                
                clustered_quotes[section_name] = {
                    "description": section_description,
                    "quotes": section_quotes,
                    "quote_count": len(section_quotes)
                }
            
            # Ensure Background section exists
            if "Background" not in clustered_quotes:
                clustered_quotes["Background"] = {
                    "description": "Introduction and background information",
                    "quotes": [],
                    "quote_count": 0
                }
            
            logger.info(f"Generated outline with {len(sections)} sections")
            
            # Log processing trace
            trace_info = {
                "step": "outline_generation",
                "query": query,
                "quotes_processed": len(quotes),
                "sections_generated": len(sections),
                "section_names": [s.get("name", "") for s in sections]
            }
            logger.info(f"Outline generation trace: {trace_info}")
            
            return {
                "outline": sections,
                "clustered_quotes": clustered_quotes,
                "processing_trace": trace_info
            }
            
        except Exception as e:
            logger.error(f"Error in outline generation: {str(e)}")
            return {
                "outline": [],
                "clustered_quotes": {"Background": {"description": "", "quotes": [], "quote_count": 0}},
                "processing_trace": {"step": "outline_generation", "error": str(e)}
            }
