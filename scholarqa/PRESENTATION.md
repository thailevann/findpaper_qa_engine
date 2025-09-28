# ScholarQA — Project Presentation

## Quick elevator pitch

ScholarQA is a modular backend service that converts ranked passages from scientific papers into a structured, evidence-backed answer. It follows AllenAI-style ScholarQA best practices: retrieval → reranking → quote extraction → outline/planning → comparisons → final synthesis. The service exposes REST endpoints for embedding, filtering, theme generation, and two pipeline entrypoints (legacy `qa-pipeline` and new `scholarqa-pipeline`).

## Key goals

- Produce structured, traceable answers with verbatim quotes and metadata.
- Cluster quotes into clear sections/outlines and optionally produce comparison tables.
- Maintain backward compatibility with a legacy QA endpoint while providing an extensible ScholarQA pipeline.

## High-level architecture

1. Ingest: client provides a `query` and `ranked_passages` (each with `paper_id`, `title`, `evidence`, and scores).
2. Pipeline orchestrator `ScholarQAPipeline` coordinates components:
   - `PassageRetriever` — select top passages to consider
   - `PassageReranker` — rerank using embeddings + similarity
   - `QuoteExtractor` — extract verbatim quotes and attach metadata
   - `OutlinePlanner` — cluster quotes into sections and produce an outline
   - `ComparisonGenerator` — produce tabular comparisons for dimensions addressed by multiple papers
   - `ReportSynthesizer` — synthesize final narrative, summary, and metadata
3. Output: structured JSON report with `sections`, `comparison_tables`, `processing_trace`, and `metadata`.

ASCII flow (simplified):

Client -> /scholarqa-pipeline -> ScholarQAPipeline
Retrieval -> Embeddings -> Rerank -> Quote Extraction -> Planning/Clustering -> Comparisons -> Synthesis -> Response

## Important files and responsibilities

- `app/main.py` — FastAPI app; public endpoints: `/health`, `/embed`, `/filter-quotes`, `/generate-themes`, `/final-report`, `/qa-pipeline` (legacy), `/scholarqa-pipeline` (new). Handles logging and basic error wrapping.
- `app/embedding.py` — Embeddings using `sentence-transformers/all-MiniLM-L6-v2`. Thread-safe lazy loading and a simple in-memory cache for repeated texts.
- `app/qa.py` — High-level functions that provide legacy helpers (`filter_passages`, `generate_themes`, `generate_final_report`) and bridge functions that call the `ScholarQAPipeline` (`process_qa_pipeline`, `process_scholarqa_pipeline`). Also contains OpenAI client wrapper and prompt templates for legacy flows.
- `app/components/pipeline.py` — Orchestrator `ScholarQAPipeline` which invokes the pipeline components in sequence and constructs `processing_trace` and `metadata` in the final report.
- `app/schemas.py` — Pydantic models (request/response) for all endpoints, including rich types for `StructuredReport`, `SectionInfo`, `QuoteWithMetadata`, and `ProcessingTrace`.
- `requirements.txt` — pinned dependencies used by the service (FastAPI, uvicorn, pydantic, sentence-transformers, openai, etc.).

## How to run locally (developer / demo)

Prereqs:

- Python 3.10+ recommended
- GPU not required — model `all-MiniLM-L6-v2` runs on CPU but will be faster with GPU
- `OPENAI_API_KEY` environment variable if you plan to call OpenAI endpoints (legacy theme/reporting functions)

Recommended quick steps (PowerShell):

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Export API key (PowerShell):

   ```powershell
   $env:OPENAI_API_KEY = 'sk-REPLACE_WITH_YOUR_KEY'
   ```

3. Start the API server:

   ```powershell
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

4. Test health endpoint (PowerShell):

   ```powershell
   Invoke-RestMethod -Uri http://localhost:8000/health -Method GET
   ```

5. Example ScholarQA pipeline POST (PowerShell):

   ```powershell
   $body = @{
       query = "What are the main trade-offs of method X compared to method Y?"
       ranked_passages = @(
           @{ paper_id = "paper1"; title = "Paper 1"; evidence = "Paper1: result A..."; cross_score = 0.9; final_score = 0.9 },
           @{ paper_id = "paper2"; title = "Paper 2"; evidence = "Paper2: result B..."; cross_score = 0.85; final_score = 0.85 }
       )
       retrieval_top_k = 50
       rerank_top_k = 20
   }

   Invoke-RestMethod -Uri http://localhost:8000/scholarqa-pipeline -Method POST -Body ($body | ConvertTo-Json -Depth 5) -ContentType 'application/json'
   ```

## Edge cases and considerations

- Empty input: endpoints gracefully return empty lists or error messages; `filter_passages` returns empty arrays when no passages provided.
- Large inputs: embedding is batched; `embed_texts` supports `batch_size` param — monitor memory for very large `ranked_passages` sets.
- Missing OpenAI API key: `generate_themes`/`generate_final_report` will raise explicit errors; pipeline components that call OpenAI need env var present.
- Determinism / reproducibility: LLM calls use low temperature (0.2–0.3) in legacy functions, but outputs can still vary.
- Caching: embeddings are cached in-memory by string key — not persistent across process restarts and may be memory-heavy for large corpora.

## Minimal tests & validation

- Unit tests present in repository root (e.g., `test_api_requests.py`, `test_scholarqa_pipeline.py`) — run the test suite to validate changes.

## Next steps and suggestions

- Add persistent embedding cache (Redis, SQLite) to avoid re-encoding large corpora each restart.
- Add rate limits and request size checks to `app/main.py` to protect resource usage.
- Add CI job that runs the unit tests and a lightweight smoke test of the API endpoints.
- Add more robust input validation and clearer error codes for pipeline failures.

---

If you want, I can now:

- Generate a slide-style markdown (`SLIDES.md`) for quick copy-paste into a presentation (todo 2),
- Add a PowerShell helper `run_demo.ps1` that automates venv creation and starts the server (todo 3), or
- Run the local tests and report results (todo 4).
