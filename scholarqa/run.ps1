param(
  [int]$Port = 8000
)

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

if (-not $env:OPENAI_API_KEY) {
  Write-Host "WARNING: OPENAI_API_KEY is not set. /generate-themes and /final-report will fail." -ForegroundColor Yellow
}

uvicorn app.main:app --host 0.0.0.0 --port $Port --reload


