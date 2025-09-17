"""
Quote extraction component for selecting relevant quotes from passages.
"""
from typing import List, Dict, Any, Tuple
import logging
import os
from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

load_dotenv()
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

logger = logging.getLogger(__name__)


class QuoteExtractor:
    """Component responsible for extracting relevant quotes from passages."""
    
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
    
    def extract_quotes(self, query: str, passages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract relevant quotes from passages with metadata.
        
        Args:
            query: User query
            passages: List of passages with metadata
            
        Returns:
            List of extracted quotes with metadata
        """
        logger.info(f"Extracting quotes from {len(passages)} passages")
        
        if not passages:
            return []
        
        # Prepare passages for LLM
        passage_texts = []
        for i, passage in enumerate(passages):
            passage_texts.append(f"[{i+1}] {passage['evidence']}")
        
        # System prompt for quote selection
        system_prompt = (
            "You are an expert research assistant. Given a user question and a set of passages from research papers, "
            "select only verbatim quotes that directly contribute to answering the question. "
            "Relevant quotes should contain specific information that helps answer the query. "
            "Irrelevant quotes should be discarded. Return only the selected quotes, one per line, "
            "with their passage numbers in brackets (e.g., '[1] quote text')."
        )
        
        user_prompt = (
            f"User question: {query}\n\n"
            f"Passages from research papers:\n"
            + "\n\n".join(passage_texts) +
            f"\n\nInstructions:\n"
            f"- Select only verbatim quotes that directly contribute to answering the question.\n"
            f"- Relevant -> keep\n"
            f"- Irrelevant -> discard\n"
            f"- Return only the selected quotes with passage numbers, one per line."
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            
            selected_quotes_text = response.choices[0].message.content or ""
            
            # Parse selected quotes and match with original passages
            extracted_quotes = []
            quote_lines = [line.strip() for line in selected_quotes_text.split('\n') if line.strip()]
            
            for quote_line in quote_lines:
                # Extract passage number and quote text
                if quote_line.startswith('[') and ']' in quote_line:
                    try:
                        end_bracket = quote_line.index(']')
                        passage_num = int(quote_line[1:end_bracket]) - 1  # Convert to 0-based index
                        quote_text = quote_line[end_bracket + 1:].strip()
                        
                        if 0 <= passage_num < len(passages):
                            passage = passages[passage_num]
                            extracted_quotes.append({
                                "quote_text": quote_text,
                                "paper_id": passage.get("paper_id", ""),
                                "title": passage.get("title", ""),
                                "score": passage.get("final_score", 0.0),
                                "similarity_score": passage.get("similarity_score", 0.0),
                                "passage_index": passage_num,
                                "metadata": {
                                    "cross_score": passage.get("cross_score", 0.0),
                                    "final_score": passage.get("final_score", 0.0)
                                }
                            })
                    except (ValueError, IndexError):
                        # Skip malformed lines
                        continue
            
            logger.info(f"Extracted {len(extracted_quotes)} quotes")
            
            # Log processing trace
            trace_info = {
                "step": "quote_extraction",
                "query": query,
                "input_passages": len(passages),
                "extracted_quotes": len(extracted_quotes),
                "papers_referenced": len(set(q["paper_id"] for q in extracted_quotes))
            }
            logger.info(f"Quote extraction trace: {trace_info}")
            
            return extracted_quotes
            
        except Exception as e:
            logger.error(f"Error in quote extraction: {str(e)}")
            return []
