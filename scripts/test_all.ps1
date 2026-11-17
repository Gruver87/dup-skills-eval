#Requires -Version 5.1
<#
.SYNOPSIS
  Unit + ruff gate for dup-skills-eval (no network).
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Assert-NativeExit {
  param([Parameter(Mandatory)][string]$Label)
  if ($null -eq $LASTEXITCODE) { return }
  if ($LASTEXITCODE -ne 0) {
    throw "$Label failed with exit $LASTEXITCODE"
  }
}

Write-Host "== pip install -e .[dev] =="
python -m pip install -e ".[dev]" -q
Assert-NativeExit "pip"

Write-Host "== ruff =="
python -m ruff check src tests scripts
Assert-NativeExit "ruff"

Write-Host "== pytest =="
python -m pytest -q
Assert-NativeExit "pytest"

Write-Host "== self-eval fixtures/good_pack =="
python -m skills_eval (Join-Path $Root "tests\fixtures\good_pack") `
  --report-dir (Join-Path $Root "reports\fixture-good") `
  --no-report
Assert-NativeExit "fixture-good"

Write-Host "test_all PASS"
exit 0
