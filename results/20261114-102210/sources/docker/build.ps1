$ErrorActionPreference = 'Stop'
$benchmarkRoot = Split-Path $PSScriptRoot -Parent
$libraryDir = Join-Path $benchmarkRoot 'guicedee/target/lib'
if (Test-Path -LiteralPath $libraryDir) {
    $resolvedLibraryDir = (Resolve-Path -LiteralPath $libraryDir).Path
    $expectedLibraryDir = [IO.Path]::GetFullPath($libraryDir)
    if ($resolvedLibraryDir -ne $expectedLibraryDir -or !$resolvedLibraryDir.StartsWith($benchmarkRoot + [IO.Path]::DirectorySeparatorChar)) {
        throw 'Dependency output is outside the benchmark workspace'
    }
    Remove-Item -LiteralPath $resolvedLibraryDir -Recurse -Force
}
& mvn -B -f "$benchmarkRoot/guicedee/pom.xml" dependency:copy-dependencies '-DincludeScope=runtime' "-DoutputDirectory=$libraryDir"
if ($LASTEXITCODE) { throw 'Runtime dependency packaging failed' }
foreach ($framework in @('guicedee','quarkus')) {
    & docker build --target $framework -t "devsuite-bench-${framework}:local" -f "$PSScriptRoot/Dockerfile" $benchmarkRoot
    if ($LASTEXITCODE) { throw "Image build failed: $framework" }
}
