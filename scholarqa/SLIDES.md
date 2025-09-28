# ScholarQA — Slide Deck (markdown)

---

# Slide 1: Title

ScholarQA — Structured evidence-backed answers from paper passages

Presenter: Team / Your Name

---

# Slide 2: Problem

- Research questions are hard to answer quickly from many papers.
- Need evidence with verbatim quotes, citations, and structured comparisons.

---

# Slide 3: Solution

- ScholarQA pipeline: retrieval → rerank → quote extraction → planning → comparisons → synthesis.
- Returns structured JSON with sections, quotes (metadata), comparison tables, and processing trace.

---

# Slide 4: Architecture

- API: `app/main.py` (FastAPI)
- Pipeline orchestrator: `components/pipeline.py` (ScholarQAPipeline)
- Embeddings: `embedding.py` using `sentence-transformers`
- LLM integrations: legacy helpers in `qa.py` (OpenAI)

---

# Slide 5: Key Components

- PassageRetriever — choose top candidate passages
- PassageReranker — rerank using embeddings
- QuoteExtractor — extract verbatim quotes with metadata
- OutlinePlanner — cluster quotes into sections
- ComparisonGenerator — build tables across papers
- ReportSynthesizer — finalize narrative and metadata

---

# Slide 6: Demo / How to run

1. `python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt`
2. `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
3. POST to `/scholarqa-pipeline` with `query` and `ranked_passages` (see README/PRESENTATION)

---

# Slide 7: Strengths & Next steps

- Strengths: modular, traceable, backward-compatible. Good default embeddings.
- Next: persistent cache, CI tests, robust error handling, rate limits.

---

# Slide 8: Questions

- Thank you — open for questions!
