#Requires -Version 5.1
<#
.SYNOPSIS
  Run industrial eval against sibling Desktop/dup-agent-skills pack.
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Pack = Join-Path (Split-Path -Parent $Root) "dup-agent-skills"
$ReportDir = Join-Path $Root "reports\dup-agent-skills"

if (-not (Test-Path (Join-Path $Pack "skills"))) {
  Write-Error "dup-agent-skills not found at $Pack"
  exit 2
}

Set-Location $Root
python -m pip install -e . -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m skills_eval $Pack --report-dir $ReportDir
exit $LASTEXITCODE
