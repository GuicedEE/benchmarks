# Quarkus native comparison

This is the preserved comparison with GuicedEE's SDK wrappers. For normal upstream SDK
dependencies and published Quarkus/Quarkiverse integrations, use
[quarkus-standard](../quarkus-standard/README.md) and `--quarkus-dependencies standard`.

This is a separate Maven project for a Linux native executable. It compiles the existing `../quarkus/src/main/java` adapter and uses its `application.properties`, the same Quarkus version and extensions, and `comparison-common` for all SDK/GraphQL/Firestore work. Native-specific metadata belongs under this project's `src/main/resources/META-INF/native-image/`.

Normal reactor builds produce JVM artifacts without requiring GraalVM. The `native` profile enables native compilation. The Docker target uses a digest-pinned Java 25 Mandrel builder and the same Oracle Linux runtime base as the other benchmark images. The final image launches `/app/application` directly and contains no JVM. Native compilation uses an 8 GiB build heap and takes place outside measurement.

From DevSuite:

```powershell
# Build the fixture and package all six images, including native compilation:
./benchmarks/build.ps1
./benchmarks/docker/build.ps1 -Native

# Compare the existing five variants and native:
python benchmarks/tools/compare.py --docker --firebase --runtime both --native --runs 3 --requests 30 --warmup 10
# Apply C1 to the JVM variants only; native keeps its original compiler optimization settings:
python benchmarks/tools/compare.py --docker --firebase --runtime both --native --tiered --runs 3 --requests 30 --warmup 10
# Smaller Quarkus JVM/native comparison:
python benchmarks/tools/compare.py --docker --firebase --framework quarkus --native --runs 3 --requests 30 --warmup 10
```

With Mandrel/GraalVM 25 installed locally, `mvn -f benchmarks/pom.xml -pl quarkus-native -am package -Pnative -DskipTests` builds for the host OS. The benchmark runner currently accepts the Linux Docker executable only. `--runtime native` selects only the native diagnostic; a single variant cannot declare an eligible comparison.

Every runtime must pass the same 15 capability checks. Native startup alone is insufficient. The runner verifies an ELF executable and its direct entrypoint, captures its SHA-256 and native compiler version, and enforces the same 250m CPU / 500 MiB container limits. It passes `-Xms128m -Xmx384m -XX:ActiveProcessorCount=2` to native; `TieredStopAtLevel` is never passed to it. No PGO or UPX profile is configured.

SDK wrappers preserve `org.graalvm` hosted API references and the JDK's `org.ietf` API references. Firebase also preserves `org.conscrypt` names used by its JNI library. Wrapper source snapshots accompany image provenance. Rebuild the wrappers before packaging consumers when those inputs change (`./benchmarks/build.ps1 -InstallGuicedEE`).

`tools/prepare_native_metadata.py` translates the SDKs' embedded JSON/properties metadata using the wrappers' shade rules. It preserves reflection, JNI, resources, features and initialization rules under their actual relocated names. The native build excludes the originals inside the two SDK JARs and includes these translated copies from this project. `native-metadata-inputs.json` records the source JAR and shade-POM hashes. Docker's `-Native` build runs this step automatically; run it manually after SDK updates when using a local native compiler. No module descriptor or SDK class is stripped.

Native compatibility code in `src/main/java/bench/nativecompat` preserves absent optional backend behavior for the SDKs' relocated Netty/Apache clients. It is guarded by dependency presence and retains the JDK TLS/PEM fallbacks. Network transports, platform probes and credential-provider state initialize at runtime. These are compiler compatibility changes, not replacements for the SDK business calls. HTTPS and optional codecs are outside this fixture's capability coverage.

SDK service descriptors and constructors for all providers of exercised SPI interfaces are registered explicitly because Quarkus disables GraalVM's automatic service-loader registration. The additional `sdk-trace/reachability-metadata.json` was collected from the full JVM capability workload; only types/resources owned by the two SDK wrapper JARs are imported. Unexercised SDK products require additional tracing and capability checks before claiming native support. `native-trace-inputs.json` records hashes, and packaging rejects changed SDK JARs until that trace is refreshed.

To refresh the trace after an SDK update, rebuild the benchmark JVM artifacts and the Quarkus JVM image first (`./benchmarks/build.ps1`, then `./benchmarks/docker/build.ps1` without `-Native`). Extract `libnative-image-agent.so` from the same pinned Mandrel builder used in `docker/Dockerfile`, then run with a fresh output directory:

```powershell
python benchmarks/tools/trace_native.py <path-to-libnative-image-agent.so> benchmarks/results/native-agent-refresh
python benchmarks/tools/import_native_trace.py benchmarks/results/native-agent-refresh
./benchmarks/docker/build.ps1 -Native
```

Tracing runs only Quarkus JVM with 2 CPU / 2 GiB for diagnostic headroom. It must pass all 15 capabilities before its metadata can be imported, and the traced image's SDK hashes must match the local SDK artifacts. It cannot produce an eligible performance comparison. Its timings must not enter the results tables. Normal comparison limits remain 250m CPU / 500 MiB.

Follow [RESULTS.md](../RESULTS.md) for measured status and retained failures. Native build/run failures are not valid performance results.

Build guidance: [Quarkus native executables](https://quarkus.io/guides/building-native-image/), [native compatibility tips](https://quarkus.io/guides/writing-native-applications-tips/), [substitutions](https://quarkus.io/guides/native-reference/) and [service-provider registration](https://quarkus.io/version/3.40/guides/writing-extensions/#service-files).
