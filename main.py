import os
from dotenv import load_dotenv

# Load env
load_dotenv()

from online_team.preprocess.query_processeor import decompose_query_with_gemini
from online_team.rag.local_retriever import retrieve_papers

def main():
    # 1. Query ban đầu
    user_query = "Deep learning papers about transformers from 2020 to 2025"

    # 2. Decompose query với Gemini
    processed, raw_content = decompose_query_with_gemini(user_query)
    print("\n--- Gemini decomposed query ---")
    print(f"Rewritten: {processed.rewritten_query}")
    print(f"Keyword: {processed.keyword_query}")
    print(f"Filters: {processed.search_filters}")
    print("\nRaw Gemini output:\n", raw_content)

    # 3. Chuyển filters từ Gemini sang format của local_retriever
    filters = {}
    if "year" in processed.search_filters:
        # ví dụ Gemini trả 2020-2023 -> convert sang update_date format
        start_year, end_year = processed.search_filters["year"].split("-")
        filters["update_date"] = f"{start_year}-01-01:{end_year}-12-31"
    if "venue" in processed.search_filters:
        filters["venue"] = processed.search_filters["venue"]
    '''
    if "fieldsOfStudy" in processed.search_filters:
        filters["field_of_study"] = processed.search_filters["fieldsOfStudy"]
    '''

    matched = retrieve_papers(
    query=processed.keyword_query or processed.rewritten_query,
    filters=filters,
    limit=10
    )


    # 5. In kết quả
    print(f"\nFound {len(matched)} papers:")
    for paper in matched:
        print(f"- {paper['title']} ({paper['update_date']})")
        print(f"- {paper['abstract']}")
        print(f"---------------------")
        #print(f"exact_score:", paper['exact_score'])

if __name__ == "__main__":
    main()
