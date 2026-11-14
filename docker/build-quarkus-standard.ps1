param([string]$Tag = 'local', [switch]$Native, [switch]$NativeOnly)
$ErrorActionPreference = 'Stop'
$benchmarkRoot = Split-Path $PSScriptRoot -Parent
$buildOptions = @('--docker','--framework','quarkus','--quarkus-dependencies','standard','--tag',$Tag)
if ($NativeOnly) { $buildOptions += @('--runtime','native') } elseif ($Native) { $buildOptions += '--native' }
& python (Join-Path $benchmarkRoot 'tools/build.py') @buildOptions
if ($LASTEXITCODE) { throw 'Quarkus image build failed' }
