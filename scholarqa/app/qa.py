from __future__ import annotations

from json import load
import os
from typing import List, Tuple

import numpy as np
from numpy.linalg import norm

from .embedding import embed_texts
from dotenv import load_dotenv
try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore

load_dotenv()
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _cosine_similarity_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    if a.size == 0 or b.size == 0:
        return np.empty((a.shape[0], b.shape[0]))
    a_norm = a / np.clip(norm(a, axis=1, keepdims=True), 1e-12, None)
    b_norm = b / np.clip(norm(b, axis=1, keepdims=True), 1e-12, None)
    return a_norm @ b_norm.T


def filter_passages(query: str, passages: List[str], top_k: int = 10) -> Tuple[List[str], List[int], List[float]]:
    if not passages:
        return [], [], []
    embeddings = embed_texts([query] + passages)
    query_vec = embeddings[0:1]
    passage_vecs = embeddings[1:]
    sims = _cosine_similarity_matrix(passage_vecs, query_vec).reshape(-1)
    order = np.argsort(-sims)[: min(top_k, len(passages))]
    filtered = [passages[i] for i in order]
    scores = [float(sims[i]) for i in order]
    indices = [int(i) for i in order]
    return filtered, indices, scores


SYSTEM_THEMES = (
    "You are an expert research assistant. Given a user question and a set of passages, "
    "extract only verbatim quotes that directly support answering the question. Group the quotes into clear, non-overlapping themes. "
    "Always include a first theme named 'Introduction/Background' that briefly frames the topic; this theme may be empty if needed. "
    "Return only JSON strictly matching the provided schema. Do not add commentary."
)


def _get_openai_client() -> "OpenAI":
    if OpenAI is None:
        raise RuntimeError("openai package is not installed. Add 'openai' to requirements and set OPENAI_API_KEY.")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in environment.")
    return OpenAI(api_key=api_key)


def generate_themes(query: str, passages: List[str], model: str | None = None, max_themes: int = 5) -> List[dict]:
    client = _get_openai_client()
    model_name = model or DEFAULT_OPENAI_MODEL
    prompt = (
        "User question:\n" + query + "\n\n" +
        "Passages (use only verbatim quotes that directly contribute to the answer):\n" +
        "\n\n".join(f"[{i}] {p}" for i, p in enumerate(passages)) +
        "\n\nInstructions:\n- Extract only necessary verbatim quotes.\n"
        "- Group quotes into at most " + str(max_themes) + " themes.\n"
        "- Always include first theme named 'Introduction/Background'.\n"
        "- Respond with strict JSON: {\"themes\": [{\"name\": str, \"quotes\": [str, ...]}]}\n"
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_THEMES},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or '{"themes": []}'
    import json

    data = json.loads(content)
    themes = data.get("themes", [])
    intro_idx = next((i for i, t in enumerate(themes) if t.get("name", "").strip().lower() == "introduction/background"), None)
    if intro_idx is None:
        themes = [{"name": "Introduction/Background", "quotes": []}] + themes
    elif intro_idx != 0:
        intro = themes.pop(intro_idx)
        themes = [intro] + themes
    for t in themes:
        t["quotes"] = [str(q) for q in t.get("quotes", [])]
    return themes


SYSTEM_REPORT = (
    "You are an expert technical writer. Using the provided themes with verbatim quotes and the user query, "
    "draft a comprehensive, well-structured answer. Use quotes where helpful, synthesize missing pieces succinctly, and avoid hallucinations. "
    "Cite quotes inline minimally (e.g., [T1-Q3]) if helpful, but do not fabricate sources."
)


def generate_final_report(query: str, themes: List[dict], model: str | None = None) -> str:
    client = _get_openai_client()
    model_name = model or DEFAULT_OPENAI_MODEL
    import json

    outline = json.dumps({"themes": themes}, ensure_ascii=False)
    user_prompt = (
        "User question:\n" + query + "\n\n" +
        "Themes with quotes (JSON):\n" + outline + "\n\n" +
        "Write a long-form answer with: Background, Thematic sections with bullets where appropriate, and concise Summary/Recommendations."
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_REPORT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    return (response.choices[0].message.content or "").strip()


def process_qa_pipeline(query: str, ranked_passages: List[dict], model: str | None = None, max_themes: int = 5) -> dict:
    """
    Complete QA pipeline following the flow diagram:
    1. User query + Top 50-ranked passages
    2. LLM: Select only verbatim quotes that directly contribute to answering the query
    3. Concatenate with paper's abstract
    4. LLM generates themes + constructs answer outline
    5. Assign filtered quotes to themes
    6. LLM synthesizes content for each section
    7. Final report/answer
    """
    client = _get_openai_client()
    model_name = model or DEFAULT_OPENAI_MODEL
    
    # Step 1: Extract passages and abstracts
    passages = [p["evidence"] for p in ranked_passages]
    abstracts = []
    paper_info = []
    
    for p in ranked_passages:
        abstracts.append(f"Title: {p['title']}\nAbstract: {p['evidence']}")
        paper_info.append({
            "paper_id": p["paper_id"],
            "title": p["title"],
            "score": p["final_score"]
        })
    
    # Step 2: LLM selects verbatim quotes that directly contribute to answering the query
    SYSTEM_QUOTE_SELECTION = (
        "You are an expert research assistant. Given a user question and a set of passages from research papers, "
        "select only verbatim quotes that directly contribute to answering the question. "
        "Relevant quotes should contain specific information that helps answer the query. "
        "Irrelevant quotes should be discarded. Return only the selected quotes, one per line."
    )
    
    quote_selection_prompt = (
        f"User question: {query}\n\n"
        f"Passages from research papers:\n"
        + "\n\n".join(f"[{i+1}] {passage}" for i, passage in enumerate(passages)) +
        f"\n\nInstructions:\n"
        f"- Select only verbatim quotes that directly contribute to answering the question.\n"
        f"- Relevant -> keep\n"
        f"- Irrelevant -> discard\n"
        f"- Return only the selected quotes, one per line."
    )
    
    quote_response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_QUOTE_SELECTION},
            {"role": "user", "content": quote_selection_prompt},
        ],
        temperature=0.2,
    )
    
    selected_quotes = [line.strip() for line in quote_response.choices[0].message.content.split('\n') if line.strip()]
    
    # Step 3: Concatenate selected quotes with abstracts
    combined_content = selected_quotes + abstracts
    
    # Step 4: LLM generates themes and constructs answer outline
    themes = generate_themes(query, combined_content, model_name, max_themes)
    
    # Step 5: Assign filtered quotes to themes (this is handled in generate_themes)
    # Step 6: LLM synthesizes content for each section
    # Step 7: Generate final report
    final_report = generate_final_report(query, themes, model_name)
    
    return {
        "query": query,
        "filtered_passages": selected_quotes,
        "themes": themes,
        "final_report": final_report,
        "processing_info": {
            "total_passages": len(passages),
            "selected_quotes": len(selected_quotes),
            "themes_generated": len(themes),
            "papers_used": len(paper_info)
        }
    }


