import os
import json
import logging
from typing import Tuple, List, Union
from collections import namedtuple
from pydantic import BaseModel, Field
from google import genai 

from online_team.llms.prompts import QUERY_DECOMPOSER_PROMPT
from config import get_gemini_client

# --- Config logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Định nghĩa output ---
LLMProcessedQuery = namedtuple("LLMProcessedQuery",
                               ["rewritten_query", "keyword_query", "search_filters"])


class DecomposedQuery(BaseModel):
    earliest_search_year: str = Field(description="The earliest year to search for papers", default="")
    latest_search_year: str = Field(description="The latest year to search for papers", default="")
    venues: str = Field(description="Comma separated list of venues to search for papers", default="")
    authors: Union[List[str], str] = Field(description="List of authors to search for papers", default=[])
    field_of_study: str = Field(description="Comma separated list of field of study to search for papers", default="")
    rewritten_query: str = Field(description="The rewritten simplified query", default="")
    rewritten_query_for_keyword_search: str = Field(description="The rewritten query for keyword search", default="")


# --- Khởi tạo Gemini client ---
client = get_gemini_client()

def decompose_query_with_gemini(query: str) -> Tuple[LLMProcessedQuery, str]:
    """
    Gửi query tới Gemini, ép trả về JSON, parse thành DecomposedQuery
    """
    search_filters = dict()

    prompt = QUERY_DECOMPOSER_PROMPT + query

    try:
        # Gọi Gemini 2.0
        resp = client.models.generate_content(
            model="gemini-1.5-flash",  # model mới của Gemini 2.0
            contents=prompt
        )

        # Gemini trả về text
        content = resp.text.strip()
        logger.info(f"Raw Gemini output:\n{content}")

        # Tìm JSON trong text (Gemini đôi khi thêm ```json)
        start = content.find("{")
        end = content.rfind("}") + 1
        json_str = content[start:end]

        data = json.loads(json_str)
        decomposed_query = {k: str(v) if isinstance(v, int) else v for k, v in data.items()}
        dq = DecomposedQuery(**decomposed_query)

        rewritten_query = dq.rewritten_query
        keyword_query = dq.rewritten_query_for_keyword_search

        if dq.earliest_search_year or dq.latest_search_year:
            search_filters["year"] = f"{dq.earliest_search_year}-{dq.latest_search_year}"
        if dq.venues:
            search_filters["venue"] = dq.venues
        if dq.field_of_study:
            search_filters["fieldsOfStudy"] = dq.field_of_study

    except Exception as e:
        logger.error(f"Error while decomposing query with Gemini: {e}")
        rewritten_query = query
        keyword_query = ""
        content = ""

    return LLMProcessedQuery(rewritten_query=rewritten_query,
                             keyword_query=keyword_query,
                             search_filters=search_filters), content

# --- Hàm main test ---
'''
def main():
    test_query = "Deep learning papers about transformers from 2020 to 2023 in NeurIPS"
    processed, raw_content = decompose_query_with_gemini(test_query)

    print("\n--- Gemini decomposed query ---")
    print(f"Rewritten: {processed.rewritten_query}")
    print(f"Keyword: {processed.keyword_query}")
    print(f"Filters: {processed.search_filters}")
    print("\nRaw Gemini output:\n", raw_content)

if __name__ == "__main__":
    main()
'''