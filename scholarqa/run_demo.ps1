<#
Simple helper to run ScholarQA locally on Windows (PowerShell).

Usage:
  .\run_demo.ps1 [-Install] [-SetApiKey "sk-..."] [-Port 8000]

Options:
  -Install: create venv and install requirements
  -SetApiKey: set OPENAI_API_KEY for this session
  -Port: port to run uvicorn on (default 8000)
#>

param(
    [switch]$Install,
    [string]$SetApiKey = $null,
    [int]$Port = 8000
)

$venvPath = Join-Path $PSScriptRoot '.venv'

if ($Install) {
    Write-Host "Creating virtual environment at $venvPath"
    python -m venv $venvPath
    Write-Host "Activating virtual environment and installing requirements (this may take a few minutes)"
    & "$venvPath\Scripts\Activate.ps1"
    pip install --upgrade pip
    pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
}

if ($SetApiKey) {
    Write-Host "Setting OPENAI_API_KEY for this session (only in-memory)"
    $env:OPENAI_API_KEY = $SetApiKey
}

Write-Host "Starting uvicorn server on port $Port"
$activate = "$venvPath\Scripts\Activate.ps1"
if (Test-Path $activate) {
    & $activate
}

Start-Process -NoNewWindow -FilePath python -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port $Port"

Write-Host "Server started. Example request (paste into PowerShell after server is ready):"

Write-Host "`$body = @{
    query = 'Example question'
    ranked_passages = @(
        @{ paper_id = 'p1'; title = 'Paper 1'; evidence = 'Result A is ...'; cross_score=0.9; final_score=0.9 }
    )
}
Invoke-RestMethod -Uri http://localhost:$Port/scholarqa-pipeline -Method POST -Body ($body | ConvertTo-Json -Depth 5) -ContentType 'application/json'"
