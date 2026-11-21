$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $repoRoot ".venv"
$pythonPath = Join-Path $venvPath "Scripts\python.exe"
$requiredPython = "3.11"

Push-Location $repoRoot
try {
    if (Test-Path -LiteralPath $pythonPath) {
        $venvVersion = & $pythonPath -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        if ($LASTEXITCODE -ne 0 -or $venvVersion.Trim() -ne $requiredPython) {
            throw "Existing .venv uses Python $($venvVersion.Trim()); Python $requiredPython is required. Move or remove .venv, then rerun bootstrap."
        }
    }
    else {
        py -3.11 -m venv $venvPath
        if ($LASTEXITCODE -ne 0) {
            throw "Could not create the Python 3.11 virtual environment."
        }
    }

    & $pythonPath -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }

    & $pythonPath -m pip install -r requirements-dev.txt
    if ($LASTEXITCODE -ne 0) { throw "Python dependency installation failed." }

    npm --prefix web ci
    if ($LASTEXITCODE -ne 0) { throw "Frontend dependency installation failed." }

    if (-not (Test-Path -LiteralPath ".env")) {
        Copy-Item -LiteralPath ".env.example" -Destination ".env"
        Write-Host "Created .env from .env.example"
    }

    if (-not (Test-Path -LiteralPath "web\.env.local")) {
        Copy-Item -LiteralPath "web\.env.example" -Destination "web\.env.local"
        Write-Host "Created web/.env.local from web/.env.example"
    }

    git config core.hooksPath .githooks
    if ($LASTEXITCODE -ne 0) { throw "Git hook configuration failed." }

    Write-Host "Bootstrap complete. Run .\scripts\verify.ps1 next."
}
finally {
    Pop-Location
}
