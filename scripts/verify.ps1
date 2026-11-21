param(
    [string]$PythonPath = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($PythonPath)) {
    $PythonPath = Join-Path $repoRoot ".venv\Scripts\python.exe"
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [Parameter(Mandatory = $true)]
        [string]$FailureMessage
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw $FailureMessage
    }
}

if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Missing .venv. Run .\scripts\bootstrap.ps1 first."
}

$pythonTargets = @(
    Get-ChildItem -LiteralPath $repoRoot -Filter "*.py" -File |
        ForEach-Object { $_.FullName }
) + @(Join-Path $repoRoot "tests")

Push-Location $repoRoot
try {
    Invoke-Checked $PythonPath @("-m", "pip", "check") "Python dependency verification failed."
    Invoke-Checked $PythonPath (@("-m", "compileall", "-q") + $pythonTargets) "Python compilation failed."

    $pytestCommand = "import sys, pytest; sys.path.insert(0, r'$repoRoot'); raise SystemExit(pytest.main(['-q']))"
    Invoke-Checked $PythonPath @("-c", $pytestCommand) "Python tests failed."

    Invoke-Checked "npm" @("--prefix", "web", "audit", "--audit-level=high") "npm audit failed."
    Invoke-Checked "npm" @("--prefix", "web", "run", "lint") "Frontend lint failed."
    Invoke-Checked "npm" @("--prefix", "web", "run", "typecheck") "TypeScript validation failed."
    Invoke-Checked "npm" @("--prefix", "web", "run", "build") "Frontend production build failed."

    Write-Host "All repository verification checks passed."
}
finally {
    Pop-Location
}
