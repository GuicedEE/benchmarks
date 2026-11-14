param([string]$Tag = 'local', [string]$TraceDirectory, [switch]$AuditNative, [switch]$IncludeDesktop)
$ErrorActionPreference = 'Stop'
$benchmarkRoot = Split-Path $PSScriptRoot -Parent
$suiteRoot = Split-Path $benchmarkRoot -Parent
foreach ($module in @('GuicedEE/services/Google/guice-core', 'GuicedEE/native-image', 'GuicedEE/openapi', 'GuicedEE/swagger-ui')) {
    & mvn -B -ntp -f (Join-Path $suiteRoot "$module/pom.xml") install '-Dmaven.javadoc.skip=true'
    if ($LASTEXITCODE) { throw "Native support build failed: $module" }
}
$prepare = Join-Path $benchmarkRoot 'tools/prepare_guicedee_native.py'
if ($TraceDirectory) { & python $prepare $TraceDirectory } else { & python $prepare }
if ($LASTEXITCODE) { throw 'Native metadata/staged SDK validation failed' }
$nativeArguments = @()
if ($AuditNative) { $nativeArguments += @('--build-arg', 'NATIVE_AUDIT=true') }
if ($IncludeDesktop) { $nativeArguments += @('--build-arg', 'NATIVE_DESKTOP=true') }
& docker build @nativeArguments --target guicedee-native -t "devsuite-bench-guicedee-native:$Tag" -f "$PSScriptRoot/Dockerfile" $benchmarkRoot
if ($LASTEXITCODE) { throw 'GuicedEE native image build failed' }
