param([string]$Tag = 'local', [switch]$Native, [switch]$NativeOnly)
$ErrorActionPreference = 'Stop'
$benchmarkRoot = Split-Path $PSScriptRoot -Parent
# The shared OS stage expects this generated file even though standard images replace
# it with their own build inventory. A fresh standalone clone has no staged GuicedEE inputs.
if (-not (Test-Path -LiteralPath "$PSScriptRoot/build-provenance.json")) {
    & python "$benchmarkRoot/tools/image_provenance.py"
    if ($LASTEXITCODE) { throw 'Build context provenance initialization failed' }
}
$targets = @()
if (-not $NativeOnly) { $targets += 'quarkus-standard' }
if ($Native -or $NativeOnly) { $targets += 'quarkus-standard-native' }
foreach ($target in $targets) {
    & docker build --target $target -t "devsuite-bench-${target}:$Tag" -f "$PSScriptRoot/Dockerfile" $benchmarkRoot
    if ($LASTEXITCODE) { throw "Independent Quarkus image build failed: $target" }
}
