param([Parameter(ValueFromRemainingArguments=$true)][string[]]$BuildArguments)
$ErrorActionPreference = 'Stop'
& python (Join-Path $PSScriptRoot 'tools/build.py') @BuildArguments
if ($LASTEXITCODE) { throw 'Benchmark build failed' }
