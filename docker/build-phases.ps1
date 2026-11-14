param([string]$Tag = 'phases', [switch]$UpdateOpenApi, [switch]$GuicedeeOnly)
$ErrorActionPreference = 'Stop'
$benchmarkRoot = Split-Path $PSScriptRoot -Parent
$workspace = Split-Path $benchmarkRoot -Parent

# Keep the existing staged SDK snapshot; never consume a half-written host SDK JAR.
& mvn -B -ntp -f "$workspace/GuicedEE/inject/pom.xml" package '-DskipTests' '-Dmaven.javadoc.skip=true'
if ($LASTEXITCODE) { throw 'Diagnostic inject packaging failed' }
$prepareArguments = @()
if ($UpdateOpenApi) {
    & mvn -B -ntp -f "$workspace/GuicedEE/openapi/pom.xml" package '-DskipTests' '-Dmaven.javadoc.skip=true'
    if ($LASTEXITCODE) { throw 'OpenAPI packaging failed' }
    $prepareArguments += '--update-openapi'
}
& python "$benchmarkRoot/tools/prepare_phase_build.py" @prepareArguments
if ($LASTEXITCODE) { throw 'Phase input preparation failed' }
foreach ($entry in @(
    @{ Target = 'guicedee-jlink'; Image = 'guicedee-jlink' },
    @{ Target = 'guicedee-scan-jlink'; Image = 'guicedee-scan-jlink' },
    @{ Target = 'phase-quarkus'; Image = 'quarkus' }
)) {
    if ($GuicedeeOnly -and $entry.Image -eq 'quarkus') { continue }
    & docker build --target $entry.Target -t "devsuite-bench-$($entry.Image):$Tag" -f "$PSScriptRoot/Dockerfile" $benchmarkRoot
    if ($LASTEXITCODE) { throw "Phase image build failed: $($entry.Image)" }
}
