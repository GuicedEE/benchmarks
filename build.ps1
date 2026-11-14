param([switch]$InstallGuicedEE)
$ErrorActionPreference = 'Stop'
$workspace = Split-Path $PSScriptRoot -Parent
if ($InstallGuicedEE) {
    # Optional explicit preparation; keeps framework builds outside the measurement window.
    foreach ($module in @('bom/Versioner','bom/StandaloneBOM','bom','services/Libraries/firebase-admin','services/Libraries/okio','services/Libraries/zstd-jni','services/Libraries/commercetools','client','vertx','inject','telemetry','web','rest','fault-tolerance','metrics','openapi','swagger-ui')) {
        & mvn -B -f "$workspace/GuicedEE/$module/pom.xml" install '-DskipTests' '-Dmaven.javadoc.skip=true'
        if ($LASTEXITCODE) { throw "Framework build failed: $module" }
    }
}
& mvn -B -f "$PSScriptRoot/pom.xml" clean install
if ($LASTEXITCODE) { throw 'Benchmark build failed' }
foreach ($application in @('guicedee','guicedee-scan')) {
    & mvn -B -f "$PSScriptRoot/$application/pom.xml" dependency:build-classpath '-Dmdep.outputFile=target/classpath.txt' '-Dmdep.regenerateFile=true'
    if ($LASTEXITCODE) { throw "Classpath resolution failed: $application" }
}
& npm ci --prefix "$PSScriptRoot/fixtures/firebase" --ignore-scripts --no-audit
if ($LASTEXITCODE) { throw 'Emulator tooling installation failed' }
& node "$PSScriptRoot/fixtures/firebase/node_modules/firebase-tools/lib/bin/firebase.js" setup:emulators:firestore
if ($LASTEXITCODE) { throw 'Emulator download failed' }
