param([switch]$Native)
$ErrorActionPreference = 'Stop'
$benchmarkRoot = Split-Path $PSScriptRoot -Parent
foreach ($application in @('guicedee','guicedee-scan')) {
$libraryDir = Join-Path $benchmarkRoot "$application/target/lib"
if (Test-Path -LiteralPath $libraryDir) {
    $resolvedLibraryDir = (Resolve-Path -LiteralPath $libraryDir).Path
    $expectedLibraryDir = [IO.Path]::GetFullPath($libraryDir)
    if ($resolvedLibraryDir -ne $expectedLibraryDir -or !$resolvedLibraryDir.StartsWith($benchmarkRoot + [IO.Path]::DirectorySeparatorChar)) {
        throw 'Dependency output is outside the benchmark workspace'
    }
    Remove-Item -LiteralPath $resolvedLibraryDir -Recurse -Force
}
& mvn -B -f "$benchmarkRoot/$application/pom.xml" dependency:copy-dependencies '-DincludeScope=runtime' "-DoutputDirectory=$libraryDir"
if ($LASTEXITCODE) { throw 'Runtime dependency packaging failed' }
}
& python "$benchmarkRoot/tools/prepare_jlink.py"
if ($LASTEXITCODE) { throw 'Modular application artifact validation failed' }
if ($Native) {
    & python "$benchmarkRoot/tools/prepare_native_metadata.py"
    if ($LASTEXITCODE) { throw 'SDK native metadata preparation failed' }
    & python "$benchmarkRoot/tools/prepare_native.py"
    if ($LASTEXITCODE) { throw 'Native/JVM adapter parity validation failed' }
}
& python "$benchmarkRoot/tools/stage_link_repository.py"
if ($LASTEXITCODE) { throw "Local Maven repository staging failed" }
& python "$benchmarkRoot/tools/image_provenance.py"
if ($LASTEXITCODE) { throw 'Image input capture failed' }
$variants = @('guicedee','guicedee-scan','quarkus','guicedee-jlink','guicedee-scan-jlink')
if ($Native) { $variants += 'quarkus-native' }
foreach ($framework in $variants) {
    & docker build --target $framework -t "devsuite-bench-${framework}:local" -f "$PSScriptRoot/Dockerfile" $benchmarkRoot
    if ($LASTEXITCODE) { throw "Image build failed: $framework" }
}
if ($Native) {
    & "$PSScriptRoot/build-guicedee-native.ps1"
    if ($LASTEXITCODE) { throw 'GuicedEE native image build failed' }
}
