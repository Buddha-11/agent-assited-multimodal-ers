param([switch]$CoreOnly)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
        py -3.10 -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.10 first.' }
    }
    $requirementsFile = if ($CoreOnly) { 'backend/requirements.txt' } else { 'backend/requirements-ml.txt' }
    & '.venv/Scripts/python.exe' -m pip install -r $requirementsFile
    if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
    if (-not (Test-Path -LiteralPath 'backend/.env')) { Copy-Item -LiteralPath 'backend/.env.example' -Destination 'backend/.env' }
    Push-Location 'frontend'
    try {
        npm ci
        if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
    } finally { Pop-Location }
    Write-Host 'Setup complete. Configure backend/.env, then follow README startup commands.'
} finally { Pop-Location }
