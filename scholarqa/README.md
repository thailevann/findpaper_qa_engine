## ScholarQA Microservice (Standalone)

This is a production-ready FastAPI microservice that powers quote filtering, theme generation, and final report synthesis for a QA workflow.

### Quickstart (Windows)

1) Create venv and install deps
```
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

2) Set your OpenAI API key (PowerShell)
```
$env:OPENAI_API_KEY="sk-..."
```

3) Run the API
```
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open http://localhost:8000/docs

### Docker

```
docker build -t scholarqa:latest .
docker run -e OPENAI_API_KEY=%OPENAI_API_KEY% -p 8000:8000 scholarqa:latest
```

### Integration into findpaper_qa_engine

- Copy the `service/scholarqa` directory into your repo, e.g., `services/scholarqa`.
- Option A: Run as a separate container/service and call its HTTP endpoints from your orchestrator.
- Option B: Mount `app.main.app` into your existing FastAPI application using `Mount` or include_router.

Key endpoints:
- POST `/embed`
- POST `/filter-quotes`
- POST `/generate-themes`
- POST `/final-report`


