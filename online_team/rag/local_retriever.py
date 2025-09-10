import os
import psycopg2
from typing import List, Dict, Optional
import re
from config import get_connection 

def highlight_keywords(text: str, keywords: List[str]) -> str:
    """Highlight all keywords in text, case-insensitive"""
    if not text:
        return ""
    for kw in keywords:
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        text = pattern.sub(lambda m: f"<b>{m.group(0)}</b>", text)
    return text
def retrieve_papers(
    query: str,
    filters: Optional[Dict] = None,
    limit: int = 50
) -> List[Dict]:
    """
    Retrieve papers with keyword match score and highlight keywords.
    Each query word contributes to exact_score if it appears in title or abstract.
    """
    filters = filters or {}
    where_clauses = []
    params = []

    # --- Query match using ILIKE for filtering ---
    if query:
        where_clauses.append("(title ILIKE %s OR abstract ILIKE %s)")
        params.extend([f"%{query}%", f"%{query}%"])

    # --- Filters ---
    if "venue" in filters:
        where_clauses.append('("journal-ref" ILIKE %s OR "journal-ref" IS NULL)')
        params.append(f"%{filters['venue']}%")
    if "field_of_study" in filters:
        where_clauses.append('(categories ILIKE %s OR categories IS NULL)')
        params.append(f"%{filters['field_of_study']}%")
    if "update_date" in filters:
        start_date, end_date = filters["update_date"].split(":")
        where_clauses.append("(update_date BETWEEN %s AND %s OR update_date IS NULL)")
        params.extend([start_date, end_date])

    where_sql = " AND ".join(f"({clause})" for clause in where_clauses) if where_clauses else "TRUE"

    sql = f"""
        SELECT id, title, abstract, "journal-ref", categories, update_date
        FROM arxiv_data
        WHERE {where_sql}
        LIMIT {limit}
    """

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # --- Map result with keyword match score ---
    papers = []
    keywords = [w.lower() for w in query.split()]
    for r in rows:
        title_lower = r[1].lower() if r[1] else ""
        abstract_lower = r[2].lower() if r[2] else ""
        match_count = sum(1 for kw in keywords if kw in title_lower or kw in abstract_lower)
        exact_score = match_count / len(keywords)  # 0~1
        papers.append({
            "corpus_id": r[0],
            "title": highlight_keywords(r[1], keywords),
            "abstract": highlight_keywords(r[2], keywords),
            "journal-ref": r[3],
            "categories": r[4],
            "update_date": str(r[5]),
            "exact_score": exact_score
        })

    # --- Sort by exact_score DESC, then update_date DESC ---
    papers = sorted(papers, key=lambda x: (x["exact_score"], x["update_date"]), reverse=True)

    return papers


# --- Hàm test ---
'''
def main():
    test_query = "transformers"
    filters = {"update_date": "2020-01-01:2023-12-31"}

    matched = retrieve_papers(
        query=test_query,
        exact_title=False,
        exact_abstract=False,
        filters=filters,
        limit=10
    )

    print(f"Found {len(matched)} papers:")
    for paper in matched:
        print(f"- {paper['title']} ({paper['update_date']}")


if __name__ == "__main__":
    main()
'''