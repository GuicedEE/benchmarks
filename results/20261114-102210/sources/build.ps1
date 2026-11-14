param([switch]$InstallGuicedEE)
$ErrorActionPreference = 'Stop'
$workspace = Split-Path $PSScriptRoot -Parent
if ($InstallGuicedEE) {
    # Optional explicit preparation; keeps framework builds outside the measurement window.
    foreach ($module in @('client','inject','web','rest','fault-tolerance','metrics','openapi','swagger-ui')) {
        & mvn -B -f "$workspace/GuicedEE/$module/pom.xml" install '-DskipTests' '-Dmaven.javadoc.skip=true'
        if ($LASTEXITCODE) { throw "Framework build failed: $module" }
    }
}
& mvn -B -f "$PSScriptRoot/pom.xml" install
if ($LASTEXITCODE) { throw 'Benchmark build failed' }
& mvn -B -f "$PSScriptRoot/guicedee/pom.xml" dependency:build-classpath '-Dmdep.outputFile=target/classpath.txt' '-Dmdep.regenerateFile=true'
if ($LASTEXITCODE) { throw 'Classpath resolution failed' }
& npm ci --prefix "$PSScriptRoot/fixtures/firebase" --ignore-scripts --no-audit
if ($LASTEXITCODE) { throw 'Emulator tooling installation failed' }
& node "$PSScriptRoot/fixtures/firebase/node_modules/firebase-tools/lib/bin/firebase.js" setup:emulators:firestore
if ($LASTEXITCODE) { throw 'Emulator download failed' }
