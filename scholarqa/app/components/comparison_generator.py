"""
Comparison generator component for creating tabular comparisons.
"""
from typing import List, Dict, Any, Optional
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


class ComparisonGenerator:
    """Component responsible for generating tabular comparisons when multiple papers discuss the same dimension."""
    
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
    
    def generate_comparison_tables(self, query: str, clustered_quotes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate comparison tables for sections where multiple papers discuss the same dimension.
        
        Args:
            query: User query
            clustered_quotes: Dictionary of clustered quotes by section
            
        Returns:
            List of comparison tables
        """
        logger.info("Generating comparison tables")
        
        comparison_tables = []
        
        for section_name, section_data in clustered_quotes.items():
            quotes = section_data.get("quotes", [])
            
            # Only generate tables for sections with multiple papers
            unique_papers = set(quote["paper_id"] for quote in quotes)
            if len(unique_papers) < 2:
                continue
            
            # Check if this section is suitable for comparison
            if self._is_comparison_suitable(section_name, quotes):
                table = self._create_comparison_table(section_name, quotes, query)
                if table:
                    comparison_tables.append(table)
        
        logger.info(f"Generated {len(comparison_tables)} comparison tables")
        
        # Log processing trace
        trace_info = {
            "step": "comparison_generation",
            "query": query,
            "sections_analyzed": len(clustered_quotes),
            "tables_generated": len(comparison_tables),
            "table_sections": [t["section"] for t in comparison_tables]
        }
        logger.info(f"Comparison generation trace: {trace_info}")
        
        return comparison_tables
    
    def _is_comparison_suitable(self, section_name: str, quotes: List[Dict[str, Any]]) -> bool:
        """Check if a section is suitable for tabular comparison."""
        # Sections that typically benefit from comparison
        comparison_suitable_sections = [
            "Methods", "Results", "Performance", "Evaluation", 
            "Experiments", "Datasets", "Models", "Approaches"
        ]
        
        section_lower = section_name.lower()
        return any(keyword in section_lower for keyword in comparison_suitable_sections)
    
    def _create_comparison_table(self, section_name: str, quotes: List[Dict[str, Any]], 
                               query: str) -> Optional[Dict[str, Any]]:
        """Create a comparison table for a specific section."""
        
        # Group quotes by paper
        papers_data = {}
        for quote in quotes:
            paper_id = quote["paper_id"]
            if paper_id not in papers_data:
                papers_data[paper_id] = {
                    "paper_id": paper_id,
                    "title": quote["title"],
                    "quotes": [],
                    "score": quote["score"]
                }
            papers_data[paper_id]["quotes"].append(quote["quote_text"])
        
        # Prepare data for LLM
        papers_text = []
        for paper_id, data in papers_data.items():
            quotes_text = " | ".join(data["quotes"])
            papers_text.append(f"Paper: {data['title']}\nQuotes: {quotes_text}")
        
        # System prompt for table generation
        system_prompt = (
            "You are an expert research assistant. Given multiple papers discussing the same topic, "
            "create a structured comparison table. Extract key attributes like methods, datasets, results, "
            "or other relevant dimensions for comparison. Return a JSON table structure."
        )
        
        user_prompt = (
            f"Section: {section_name}\n"
            f"Query: {query}\n\n"
            f"Papers and their relevant quotes:\n"
            + "\n\n".join(papers_text) +
            f"\n\nInstructions:\n"
            f"- Create a comparison table with relevant attributes\n"
            f"- Each row should represent a paper\n"
            f"- Columns should represent comparable dimensions\n"
            f"- Return JSON: {{\"table\": {{\"headers\": [str, ...], \"rows\": [{{\"paper_title\": str, \"attributes\": [str, ...]}}]}}}}"
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content or '{"table": {"headers": [], "rows": []}}'
            table_data = json.loads(content)
            
            table = table_data.get("table", {})
            if table.get("headers") and table.get("rows"):
                return {
                    "section": section_name,
                    "headers": table["headers"],
                    "rows": table["rows"],
                    "paper_count": len(papers_data),
                    "metadata": {
                        "papers": list(papers_data.keys()),
                        "generated_at": "comparison_step"
                    }
                }
            
        except Exception as e:
            logger.error(f"Error creating comparison table for {section_name}: {str(e)}")
        
        return None
