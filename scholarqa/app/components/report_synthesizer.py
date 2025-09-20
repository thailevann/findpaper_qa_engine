"""
Report synthesizer component for generating final structured reports.
"""
from typing import List, Dict, Any
import logging
import os
import json
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

load_dotenv()
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

logger = logging.getLogger(__name__)


class ReportSynthesizer:
    """Component responsible for synthesizing the final structured report."""
    
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
    

    def synthesize_report(self, query: str, clustered_quotes: Dict[str, Any], 
                        comparison_tables: List[Dict[str, Any]], 
                        processing_trace: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Synthesizing final report")

        # Function to process a single section
        def process_section(section_name, section_data):
            quotes = section_data.get("quotes", [])
            narrative = ""
            if quotes:
                narrative = self._generate_section_narrative(query, section_name, quotes)
            return section_name, narrative

        # Process all sections in parallel
        section_narratives = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = executor.map(lambda item: process_section(*item), clustered_quotes.items())
            for section_name, narrative in results:
                section_narratives[section_name] = narrative

        # Generate overall summary (can be heavy too, maybe optimize later)
        overall_summary = self._generate_overall_summary(query, section_narratives, comparison_tables)

        # Build structured report
        structured_report = {
            "query": query,
            "summary": overall_summary,
            "sections": [],
            "comparison_tables": comparison_tables,
            "processing_trace": processing_trace,
            "metadata": {
                "total_sections": len(clustered_quotes),
                "total_quotes": sum(len(section_data.get("quotes", [])) for section_data in clustered_quotes.values()),
                "total_papers": len(set(
                    quote["paper_id"] 
                    for section_data in clustered_quotes.values() 
                    for quote in section_data.get("quotes", [])
                )),
                "comparison_tables_count": len(comparison_tables)
            }
        }

        # Add sections
        for section_name, section_data in clustered_quotes.items():
            quotes = section_data.get("quotes", [])
            narrative = section_narratives.get(section_name, "")
            section_info = {
                "name": section_name,
                "description": section_data.get("description", ""),
                "narrative": narrative,
                "quotes": quotes,
                "quote_count": len(quotes),
                "papers_referenced": list(set(quote["paper_id"] for quote in quotes))
            }
            structured_report["sections"].append(section_info)

        logger.info(f"Synthesized report with {len(structured_report['sections'])} sections")

        # Log processing trace
        trace_info = {
            "step": "report_synthesis",
            "query": query,
            "sections_synthesized": len(section_narratives),
            "comparison_tables_included": len(comparison_tables),
            "total_quotes": structured_report["metadata"]["total_quotes"]
        }
        logger.info(f"Report synthesis trace: {trace_info}")

        return structured_report

    
    def _generate_section_narrative(self, query: str, section_name: str, 
                                   quotes: List[Dict[str, Any]]) -> str:
        """Generate narrative text for a specific section."""
        
        # Prepare quotes with citations
        quotes_with_citations = []
        for i, quote in enumerate(quotes):
            citation = f"[{quote['paper_id'][:8]}...]"  # Short paper ID
            quotes_with_citations.append(f"{citation} {quote['quote_text']}")
        
        system_prompt = (
            "You are an expert technical writer. Given a section name, user query, and relevant quotes, "
            "write a coherent narrative that synthesizes the information. Use quotes where helpful and "
            "provide context to connect the ideas. Cite quotes inline using the provided citation format."
        )
        
        user_prompt = (
            f"Section: {section_name}\n"
            f"User Query: {query}\n\n"
            f"Relevant quotes:\n"
            + "\n\n".join(quotes_with_citations) +
            f"\n\nInstructions:\n"
            f"- Write a coherent narrative for this section\n"
            f"- Synthesize information from the quotes\n"
            f"- Use quotes where they add value\n"
            f"- Maintain the citation format provided"
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            logger.error(f"Error generating narrative for {section_name}: {str(e)}")
            return f"Error generating narrative for {section_name}: {str(e)}"
    
    def _generate_overall_summary(self, query: str, section_narratives: Dict[str, str], 
                                 comparison_tables: List[Dict[str, Any]]) -> str:
        """Generate an overall summary of the report."""
        
        system_prompt = (
            "You are an expert research assistant. Given a user query, section narratives, and comparison tables, "
            "write a comprehensive summary that answers the user's question. Highlight key findings, "
            "methodological approaches, and any comparative insights from the tables."
        )
        
        # Prepare section summaries
        section_summaries = []
        for section_name, narrative in section_narratives.items():
            if narrative.strip():
                section_summaries.append(f"{section_name}: {narrative[:200]}...")
        
        # Prepare table summaries
        table_summaries = []
        for table in comparison_tables:
            table_summaries.append(f"Comparison in {table['section']}: {len(table['rows'])} papers compared on {len(table['headers'])} dimensions")
        
        user_prompt = (
            f"User Query: {query}\n\n"
            f"Section Summaries:\n" + "\n".join(section_summaries) + "\n\n"
            f"Comparison Tables:\n" + "\n".join(table_summaries) + "\n\n"
            f"Instructions:\n"
            f"- Write a comprehensive summary answering the user's question\n"
            f"- Highlight key findings and insights\n"
            f"- Mention any comparative analysis when relevant\n"
            f"- Keep it concise but informative"
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            logger.error(f"Error generating overall summary: {str(e)}")
            return f"Error generating summary: {str(e)}"
