# GuicedEE native comparison

This Maven project depends on the existing SPI application JAR. Its main class, service, resource,
business workload and `module-info.class` are used unchanged. The additional module contributes
build-time metadata, using the optional `com.guicedee:native-image` integration. Config-core and
GraalVM remain absent from GuicedEE core's dependencies.

The Guice integration generates interception classes at build time and creates injectors, services,
scopes and interceptor instances at runtime. It keeps reactive retries, timeouts and metrics enabled.
Metadata providers must not instantiate services or capture `.env`, credentials or network clients.
An unknown interceptor selection fails explicitly. This first native variant uses SPI discovery;
it does not claim runtime ClassGraph scanning support.

From the DevSuite root:

```powershell
./benchmarks/docker/build-guicedee-native.ps1
python benchmarks/tools/compare.py --docker --firebase --runtime native --runs 5 --requests 30 --warmup 10
```

Build Quarkus native first with `./benchmarks/docker/build.ps1 -Native` when it is not already present.
Both native Docker stages pin the same Mandrel 25.0.5 image digest. GuicedEE uses `-O2`, x86-64-v3,
Serial GC and no PGO, matching the existing Quarkus native build. The optional Maven `native` profile
also supports direct Linux builds: `mvn -f benchmarks/pom.xml -pl guicedee-native -am package -Pnative`.
Maven 4 and Java 25 are required; the workspace wrapper supplies the Maven version.

The Docker build compiles from source against the staged Maven repository and preserves the verified
Firebase/commercetools SDK JARs. `prepare_guicedee_native.py` rejects mismatched SDK hashes. It reuses
the same SDK substitutions and relocated SDK metadata as Quarkus native. `NativeModuleAccess.java`
opens dependency-owned native substitution packages specifically to the image builder and maps
traced resources to their JPMS modules. No application descriptors are removed.
The native module path enumerates each JAR so its embedded metadata is discovered. Netty initializes
at runtime to preserve runtime logging and configuration.

SDK metadata generation reads the shade recipe embedded in the exact SDK JAR, so later workspace
POM changes cannot silently produce metadata for a different binary. Generated protobuf reflection
entries are conditional on their message type being reachable; Firestore keeps its metadata, while
unused Monitoring and Storage models can be eliminated. Both native projects share this change.

The server benchmark defaults to a headless build and excludes only Java Sound's audio/MIDI service
providers. Automatic service loading remains enabled for application and library SPIs. Use
`-IncludeDesktop` (Docker `--build-arg NATIVE_DESKTOP=true`, or `NATIVE_DESKTOP=true` for direct builds)
to retain those providers. This is a benchmark packaging choice, not a GuicedEE core default.

`-AuditNative` enables GraalVM call-tree and used-class reports in the builder's
`/src/guicedee-native/target/reports`. Every build retains `/app/native-build-statistics.json`.
`--diagnostics` also works with native variants and enables Guice stage timing, SDK phases and
the injector inventory; these instrumented runs are always excluded from performance rankings.

To compare saved images with candidates in the same rotating batch:

```powershell
python benchmarks/tools/compare.py --docker --firebase --runtime native --baseline-image-tag native-before --runs 7 --requests 30 --warmup 10
python benchmarks/tools/summarize_native.py benchmarks/results/<batch>
```

The native metadata SPI pre-inspects the framework-owned `JsonMapper`, `VertxImpl` and `MetricRegistry`
classes for member injection. Only proven empty results are reused. Runtime construction, type
listeners, constructor injection and classes with injectable members retain normal Guice behavior.

The existing GuicedEE `.env` is copied into the runtime image; environment variables and `.env.local`
retain runtime precedence. The final image launches `/app/application` directly and includes native
sidecar libraries emitted by the compiler. It contains no JVM. Build tools and compiler memory are
outside the measured 250m CPU / 500 MiB runtime limit.

To refresh reachability metadata after changing the workload, collect a fresh full-capability JVM
trace with `tools/trace_native.py --framework guicedee`, then pass that directory to
`docker/build-guicedee-native.ps1 -TraceDirectory <path>`. A trace is diagnostic, not a timed result.
The committed metadata covers the reference workload, including Firestore; it is not a claim that
all Firebase products or all GuicedEE integrations support native compilation.
