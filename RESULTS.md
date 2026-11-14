Latest native comparison: [normal Quarkus dependencies](STANDARD_QUARKUS_COMPARISON.md):
**668 ms versus 706 ms** median full-business startup for GuicedEE and Quarkus native, with
**5.18 ms versus 6.02 ms** warm request medians. The two batches reverse initial order and
pass all **420 capability checks / 840 measured requests**. GuicedEE uses **79.58 MiB versus
55.33 MiB** peak container memory and a **191.83 MiB versus 143.31 MiB** executable. This
independent upstream-SDK baseline is separate from the earlier shared-wrapper comparisons.

Earlier controlled native comparison, with GuicedEE SDK wrappers on both frameworks:
[startup and footprint audit](NATIVE_OPTIMIZATION.md): **659 ms versus
655 ms** median first-business completion for GuicedEE and Quarkus native. GuicedEE improves from
808 ms, its executable shrinks **223.69 → 191.83 MiB**, and median peak container memory falls
**86.18 → 79.98 MiB**. All **420 capability checks** and **840 measured requests** pass across seven
starts for each before/after native image. Quarkus receives the shared SDK metadata fix as well.
The six-variant JVM/jlink matrix below was not rerun in this batch.

Earlier validated comparison: [six-variant Linux/native results](#current-linux-native-comparison). Packaging evidence: [Oracle JDK validation](MODULAR-VALIDATION.md).

Later [instrumented phase diagnostics](PHASE_ANALYSIS.md) identify OpenAPI construction and cold SDK initialization costs, and verify that scanning accepts only three application classes. They do not replace the uninstrumented timing tables below.

The subsequent [OpenAPI optimization comparison](OPENAPI_OPTIMIZATION.md) alternates original and updated GuicedEE jlink images: SPI readiness improves **8.062 → 7.661 s (5.0%)**, scanner **8.504 → 8.037 s (5.5%)**, with all 180 capability checks passing. The provider phase itself falls 28–40%. This is a GuicedEE before/after comparison; the six-variant Quarkus/native matrix below was not rerun. The [Quarkus JVM commercetools initialization cost](PHASE_ANALYSIS.md#first-use-sdk-phases), 14.300 s versus SPI jlink's 1.108 s, remains a distinct finding.

> Historical JDK-only jlink results are retained separately below. The current Linux tables use fully linked GuicedEE application images and module-path baselines.

# Reference-service measurements — 14 November 2026

This is a new service built because the original comparison template is unavailable. It does not reproduce the historical Kotlin application in [PERFORMANCE_ANALYSIS.MD](docs/PERFORMANCE_ANALYSIS.MD), and its timings must not be presented as improvements over that application's 34-second readiness or 67-second first success.

The workload executes a real commercetools SDK OAuth/REST/GraphQL sequence and a Firebase Admin SDK Firestore write/read. A deterministic local vendor fixture and the official Firestore emulator replace external services. Both adapters share that business code. REST/DI, retries/timeouts, metrics and OpenAPI/Swagger run through each framework's integrations. The capability ledger and commands are in [README.md](README.md).

## Current Linux native comparison

The separate [quarkus-native Maven project](quarkus-native/README.md) compiles the same Quarkus adapter sources and shared business code into a Linux native executable. Packaging verifies matching Quarkus adapter bytecode and application defaults. The existing five variants and native were rebuilt with the same corrected SDK wrapper artifacts before this comparison. These results supersede the earlier five-variant baseline for current comparisons; older raw results are preserved below.

Both the [default-JVM/native batch](results/20261114-154043/summary.json) and [C1-JVM/native batch](results/20261114-154849/summary.json) have `eligibleComparison: true`: **36 fresh starts passed all 15 capabilities, all first business requests succeeded, and all 1,080 measured warm requests succeeded.** Discovery and both verticle deployments were verified for every GuicedEE run. All resource limits were checked; there were no OOM kills. Both batches use the same six immutable image IDs, recorded in the [verification ledger](results/native-comparison-verification.json).

Each variant has three fresh starts per profile, 10 warmups and 30 measured sequential requests per start. Every application runs at **250m CPU / 500 MiB**, without extra swap. Both timing columns start before `docker run`. First business completion includes readiness, real commercetools SDK OAuth/REST/GraphQL calls and the Firebase Admin SDK Firestore write/read through the official emulator. Warm requests also include Firestore.

### What the startup timers include

`launchToReadyMs` stops after an HTTP `GET /ready` returns status 200 and exactly `{"ready":true}`. Both adapters implement this as a fixed response. It establishes HTTP route availability, not dependency health or completion of a business transaction. It is stronger than an open TCP port, but is not a business-readiness guarantee. The driver probes at 50 ms intervals, so this is not a precise internal server-startup timestamp.

`launchToFirstBusinessMs` stops after the client has read and parsed the complete response to `POST /quote?persist=true`. The request chains commercetools OAuth, REST and GraphQL calls, then awaits Firebase Firestore write and read before creating the HTTP response. Returning or subscribing to a `Uni` does not stop the timer. The runner requires the expected status and body, checks recorded vendor traffic, and rejects runs that subsequently fail capability checks. See [the timer boundaries](tools/compare.py), [the resource composition](guicedee/src/main/java/bench/guicedee/rest/Resource.java), and [the shared SDK workload](common/src/main/java/bench/workload/Workload.java).

The default-profile raw rows also record the first HTTP business request's own duration, independently of process startup:

| Variant | Median launch to HTTP ready | Median first business request alone | Median launch to business completion |
|---|---:|---:|---:|
| GuicedEE SPI, application jlink | 8.960 s | 6.301 s | 15.261 s |
| Quarkus fast-JAR, full JDK | 7.014 s | 23.201 s | 30.026 s |
| Quarkus native executable | 0.586 s | 0.148 s | 0.737 s |

These are independent medians of three runs, so the first two columns need not sum to the third. The complete 15-capability suite, including induced retries/timeouts, metrics and documentation checks, runs after the first business request; 0.737 seconds is not the time to finish that entire suite. Build-time native compilation is outside these runtime timers. The native application's own log reports an internal startup time of 0.035 seconds in its first run; the comparison uses the external launch-to-response timers above instead.

The shared Firestore adapter currently uses `CompletableFuture.supplyAsync` around blocking SDK future `.get()` calls. Both frameworks wait for that future, so the database work is included, but the adapter is not fully nonblocking. A future callback-based adapter should be applied to the shared workload and remeasured for all variants. The local fixtures/emulator are already running outside each application's CPU/memory cap; these numbers do not represent startup of the entire dependency stack or production WAN/TLS latency.

### Default JVMs and native

All variants receive `-Xms128m -Xmx384m -XX:ActiveProcessorCount=2`. JVMs use default JIT tiering; native uses its ahead-of-time compilation.

| Variant | Median ready | Median first business completion | Median warm p50 | Peak charged memory range |
|---|---:|---:|---:|---:|
| GuicedEE SPI, full JDK | 10.438 s | 31.019 s | 95.94 ms | 291.4-301.4 MiB |
| GuicedEE scanner, full JDK | 11.037 s | 32.975 s | 94.26 ms | 295.9-300.3 MiB |
| Quarkus fast-JAR, full JDK | 7.014 s | 30.026 s | 97.07 ms | 297.3-298.9 MiB |
| GuicedEE SPI, application jlink | 8.960 s | 15.261 s | 95.46 ms | 217.6-247.6 MiB |
| GuicedEE scanner, application jlink | 8.910 s | 15.673 s | 95.19 ms | 222.3-228.4 MiB |
| Quarkus native executable | 0.586 s | 0.737 s | 4.97 ms | 58.8-59.1 MiB |

### C1 JVMs and the unchanged native executable

`-XX:TieredStopAtLevel=1` is added to all five JVM variants. Native receives no JIT flag and runs the identical compiled executable; its repeated row is a reference for this batch.

| Variant | Median ready | Median first business completion | Median warm p50 | Peak charged memory range |
|---|---:|---:|---:|---:|
| GuicedEE SPI, full JDK | 5.573 s | 18.546 s | 86.97 ms | 257.5-260.2 MiB |
| GuicedEE scanner, full JDK | 6.011 s | 19.432 s | 79.31 ms | 261.2-264.0 MiB |
| Quarkus fast-JAR, full JDK | 4.162 s | 17.812 s | 66.86 ms | 259.6-260.4 MiB |
| GuicedEE SPI, application jlink | 5.352 s | 8.781 s | 77.54 ms | 188.8-189.2 MiB |
| GuicedEE scanner, application jlink | 5.450 s | 8.854 s | 70.35 ms | 191.8-192.8 MiB |
| Quarkus native executable | 0.580 s | 0.701 s | 4.39 ms | 59.0-60.0 MiB |

### Interpretation and packaging

**Quarkus native is fastest on readiness and first completed business request in this fixture.** Its default-batch first business completions were 0.699-0.755 seconds, with a 0.737-second median. GuicedEE SPI jlink takes 15.261 seconds with default tiering and 8.781 seconds with C1. Linked GuicedEE remains faster than Quarkus JVM on first business completion in both batches; Quarkus JVM reaches readiness sooner.

Native compilation, metadata tracing and image builds occur outside measurement. The native executable uses Mandrel 25.0.5.0-Final (JDK 25.0.5+8-LTS), optimization level 2, x86-64-v3 and Serial GC, without PGO or UPX. The JVM variants use Oracle JDK 25.0.5.0.3+1-LTS-2; all six final images share the Oracle Linux runtime base. Native is therefore a different compilation/runtime strategy, not a GuicedEE core startup optimization. The runner verifies the ELF binary, direct `/app/application` entrypoint, absence of the JVM launcher, binary SHA-256 and compiler version.

| Variant | Docker local image-store disk usage |
|---|---:|
| GuicedEE SPI, full JDK | 1003.7 MiB |
| GuicedEE scanner, full JDK | 1003.7 MiB |
| Quarkus fast-JAR, full JDK | 993.6 MiB |
| GuicedEE SPI, application jlink | 473.2 MiB |
| GuicedEE scanner, application jlink | 473.4 MiB |
| Quarkus native executable | 395.2 MiB |

This daemon uses the containerd image store, which retains compressed content and unpacked snapshots. These figures include both, plus the common OS and build-provenance record; they are not linked runtime sizes or registry transfer sizes. The [jlink size and dependency audit](JLINK_AUDIT.md) measures the SPI linked runtime at **168.8 MiB**, its module image at **135.2 MiB**, and its unpacked Docker layers at **286.2 MiB**. See [Docker's storage explanation](https://docs.docker.com/engine/storage/containerd/#disk-space-usage).

Native's executable is 183,299,176 bytes. Peak memory is **cgroup charged memory**, including its page-cache accounting, not process RSS or Java heap usage. These short, concurrency-one warm samples are not sustained throughput measurements. Three starts per profile are a small sample; host page caches were not flushed, and fixtures/emulator run outside the capped containers. No Kubernetes scale-out or historical Kotlin application claim follows from these results.

Native support required correcting wrapper relocation of platform/hosted/JNI APIs, translating SDK native metadata and registering exercised service-provider interfaces. Dependency-guarded native substitutions preserve absent optional backend behavior; the shared business code is unchanged. The [native project documentation](quarkus-native/README.md) records those boundaries. Other SDK products, HTTPS and optional codecs need separate native validation before claiming support. The initial native failure and instrumented metadata runs remain in the [result index](results/README.md); they are excluded from these tables.

The Maven reactor, eleven harness tests, modular-artifact checks and native/JVM adapter parity checks passed. The [default environment](results/20261114-154043/environment.json) and [C1 environment](results/20261114-154849/environment.json) capture image IDs, SDK/input hashes, wrapper sources, runtime flags and source snapshots. Measured application and comparison-runner sources match their build snapshots. A subsequent diagnostic-tool check rejects stale traced SDK images; its changes and regression test are recorded separately in the verification ledger.

<a id="current-linux-application-jlink-comparison"></a>
## Earlier five-variant Linux application-jlink comparison

These earlier measurements predate the native compatibility fixes to the SDK wrappers. They are a separate artifact baseline and are not pooled with the six-variant results above.

After the Docker reset, all five images were rebuilt and measured at **250m CPU / 500 MiB RAM**, with no swap beyond that limit. GuicedEE SPI and scanner run either on the module path of the full Oracle JDK or from fully linked application images. Quarkus runs its fast-JAR on the same Oracle JDK build. There is no Quarkus application-jlink variant in this fixture; the earlier JDK-only variants are not part of this comparison.

Both the [default-JVM matrix](results/20261114-134115/summary.json) and the [equally tuned C1 matrix](results/20261114-134836/summary.json) have `eligibleComparison: true`. **All 30 fresh starts passed all 15 capabilities, all 30 first business requests succeeded, and all 900 measured warm requests succeeded.** Every GuicedEE run verified its requested discovery mode and both verticle deployments. No container was OOM-killed. These two profiles use the same immutable image IDs and build provenance.

Each profile has three fresh starts per variant, 10 warmups and 30 measured sequential business requests per start. Both timing columns start before `docker run`. First business completion includes readiness followed by the first successful commercetools OAuth/REST/GraphQL and Firebase Firestore write/read request. It is not merely a socket-open or health-check measurement.

### Default JVM settings

Every variant uses `-Xms128m -Xmx384m -XX:ActiveProcessorCount=2`, with default JIT tiering.

| Variant | Median ready | Median first business completion | Median warm p50 | Peak charged memory range |
|---|---:|---:|---:|---:|
| GuicedEE SPI, full JDK | 9.143 s | 29.517 s | 91.11 ms | 293.6-303.6 MiB |
| GuicedEE scanner, full JDK | 9.086 s | 28.382 s | 94.12 ms | 293.5-299.8 MiB |
| Quarkus fast-JAR, full JDK | 6.511 s | 27.092 s | 91.34 ms | 293.0-304.1 MiB |
| GuicedEE SPI, application jlink | 8.208 s | 14.018 s | 92.17 ms | 233.3-239.1 MiB |
| GuicedEE scanner, application jlink | 8.505 s | 14.106 s | 89.61 ms | 221.1-228.3 MiB |

### Equal C1 startup tuning

The only JVM flag change is `-XX:TieredStopAtLevel=1`, applied to all five variants. The workload and capability gates are unchanged.

| Variant | Median ready | Median first business completion | Median warm p50 | Peak charged memory range |
|---|---:|---:|---:|---:|
| GuicedEE SPI, full JDK | 5.341 s | 17.346 s | 29.76 ms | 257.9-261.2 MiB |
| GuicedEE scanner, full JDK | 5.517 s | 17.905 s | 21.40 ms | 262.6-262.7 MiB |
| Quarkus fast-JAR, full JDK | 4.127 s | 16.518 s | 23.89 ms | 258.8-260.4 MiB |
| GuicedEE SPI, application jlink | 4.869 s | 8.265 s | 21.50 ms | 187.4-189.4 MiB |
| GuicedEE scanner, application jlink | 5.203 s | 8.594 s | 35.13 ms | 190.7-192.7 MiB |

### What the measurements establish

Application-linked GuicedEE wins on **first completed business request in this workload**: SPI is 48.3% faster than Quarkus with default tiering and 50.0% faster with equal C1 tuning. Linked scanning is approximately 48% faster in both profiles. Full-JDK GuicedEE remains behind Quarkus on this metric. Quarkus still reaches HTTP readiness sooner than either linked GuicedEE variant.

The largest difference occurs after readiness: under default tiering, the median first business request itself takes about 5.4-5.8 seconds in the linked images versus about 19-20 seconds in the full-JDK variants. These timings locate the difference in the first-use business path; they do not isolate a particular SDK or class-loading mechanism as its cause.

Three starts are a small sample. SPI/scanner differences and warm-latency differences are not reliable causal estimates. Warm p50 is the median of the three per-JVM p50 values at concurrency one; this is not a throughput, overload, scale-out or sustained-load result. Host page caches are not flushed. Local vendor fixtures and the official Firestore emulator are outside the capped containers. This does not reproduce the unavailable historical Kotlin application or compare Quarkus native.

### Packaging and reproducibility

Both linked images contain **107 modules: 18 JDK modules plus the application and its dependencies**. They run the generated `bin/benchmark` launcher with the application embedded in `lib/modules`, without loose application JARs or a classpath fallback. The standalone scanner Maven project retains `module-info.class` and contains no benchmark discovery provider. The full-JDK baselines retain the JDK's stock CDS archive; no application-trained cache was used.

| Variant | Docker-reported image size |
|---|---:|
| GuicedEE SPI, full JDK | 1002.3 MiB |
| GuicedEE scanner, full JDK | 1002.3 MiB |
| Quarkus fast-JAR, full JDK | 992.2 MiB |
| GuicedEE SPI, application jlink | 471.8 MiB |
| GuicedEE scanner, application jlink | 471.9 MiB |

Application linking reduces each GuicedEE image by approximately **53%**. These are Docker-reported sizes, not registry transfer sizes or unique host disk usage. Peak memory above is cgroup charged memory, not Java heap or process RSS.

All five images use Oracle JDK `25.0.5.0.3+1-LTS-2` on Oracle Linux. The builder fixes make Maven's extracted launcher executable and install `binutils` in the build stage for debug stripping. Seven harness tests and both modular-artifact checks passed before measurement. The [default environment](results/20261114-134115/environment.json), [C1 environment](results/20261114-134836/environment.json) and [verification ledger](results/application-link-verification.json) record image IDs, flags, runtime hashes, generated launchers, source provenance and resource-limit checks. The Oracle download URL is mutable; the captured archive hash identifies the measured JDK. Those source snapshots matched the workspace when the earlier report was generated; subsequent SDK wrapper changes are captured in the six-variant records above.

The earlier Windows and classpath/JDK-only measurements remain separate evidence below. They must not be used to calculate a speedup for this new module graph or JVM build.

## Earlier classpath matrix and framework contract fixes

The scanner is now its own Maven project, [guicedee-scan](guicedee-scan/pom.xml), with the retained named-module descriptor `bench.guicedee.scan`. The SPI application retains `bench.guicedee`. Both applications use Guice's `Inject` and `Singleton` annotations. There is no scanner classifier, descriptor exclusion, or descriptor-stripping preparation step. Packaging verifies matching business bytecode while requiring both descriptors and the absence of `BenchmarkDiscovery` from the scanner artifact.

The three failures were fixed in the framework:

- REST's `ParameterExtractor` applies annotation defaults before Java primitive defaults; missing boxed values remain null and malformed supplied values still fail conversion.
- REST's `OperationRegistry` enforces the compiled class/method `@Consumes` contract after authentication/authorization and before parameter extraction or resource invocation. Unsupported entities return 415.
- Fault tolerance's `TimeoutInterceptor` now times reactive completion for Uni, CompletionStage, CompletableFuture and Vert.x Future. It uses a nonblocking deadline, preserves Vert.x context, propagates cancellation where supported and reports MicroProfile TimeoutException.

The focused REST run passed 31 tests, the full fault-tolerance suite passed 26, and the benchmark harness passed seven. Both updated framework artifacts were installed locally before the five-project fixture reactor and six Docker images were rebuilt. The benchmark's capability assertions and business workload were not weakened. The current shared workload also includes the Firebase module/build updates made during this work; compare its recorded artifact hashes rather than treating it as identical packaging to older batches.

The [intermediate failed smoke run](results/20261114-121520/summary.json) is retained: the fixture had switched to Jakarta injection annotations without opting into the CDI bridge, leaving its service field null. The final fixture uses Guice annotations as requested; no CDI dependency was added to the applications or framework modules. That failed smoke run is not a timing baseline.

The [corrected six-variant matrix](results/20261114-122316/summary.json), with [image and runtime provenance](results/20261114-122316/environment.json), now has **`eligibleComparison: true`**. Every variant passed all 15 capability checks on all three fresh starts. All 18 first business requests and 540 measured warm requests succeeded; there were no OOM kills. The three corrected cases returned 200, 415 and 504 respectively. Every GuicedEE run verified the requested discovery mode and both application verticle deployments.

This run used the classpath/fast-JAR launch paths and the shared jlink JDK runtime. Concurrent edits subsequently introduced a commercetools module wrapper and full application JPMS/jlink launch configuration. [Source changes after packaging](results/20261114-122316/source-changes-after-run.json) records that boundary. Those subsequent launch/packaging changes are not validated by this matrix, and its figures must not be relabeled as full JPMS/application-jlink measurements.

| Variant | Median launch to ready | Median launch to first business completion | Median warm p50 |
|---|---:|---:|---:|
| GuicedEE SPI, standard JRE | 5.406 s | 15.747 s | 49.13 ms |
| GuicedEE scanner, standard JRE | 5.356 s | 15.259 s | 33.97 ms |
| Quarkus, standard JRE | 3.939 s | 14.384 s | 30.49 ms |
| GuicedEE SPI, jlink | 5.167 s | 15.182 s | 68.84 ms |
| GuicedEE scanner, jlink | 5.907 s | 15.618 s | 49.95 ms |
| Quarkus, jlink | 4.003 s | 14.530 s | 12.36 ms |

All rows use `-Xms128m -Xmx384m -XX:ActiveProcessorCount=2 -XX:TieredStopAtLevel=1`, 250m CPU and 500 MiB RAM. Each JVM receives 10 warm-ups and 30 measured sequential requests. Warm p50 is the median of the three per-JVM p50 values. This is the current C1 profile; a new three-run default-JVM matrix was not collected after these fixes. Small differences, including scanner versus SPI, are not reliable causal estimates with three starts. Correctness now passes the implemented workload contract; these figures still do not show GuicedEE ahead of Quarkus on launch-to-first-business completion.

The [verification ledger](results/framework-contract-verification.json) records the focused tests, module descriptor validation and packaged framework hashes. Earlier failed measurements below remain unchanged and are not substituted for this passing matrix.

## Earlier scanner classifier and jlink runtimes

This earlier matrix kept `.env` configuration and deployed Resource and Service from separate packages. Its scanner classifier omitted `BenchmarkDiscovery`, its service registration and the module descriptor. **That packaging has been superseded:** the current scanner is a separate Maven project with its own retained `module-info.class` and no discovery provider. The older measurements and image snapshots below remain historical evidence for the classifier implementation. Their packaging checks established matching business bytecode, and runtime logs verified scanning and both verticle deployments.

The [six-image smoke check](results/20261114-112645/summary.json) completed the business path on all images. The [default-JVM matrix](results/20261114-112932/summary.json), with [image/runtime provenance](results/20261114-112932/environment.json), then measured three fresh starts per variant at 250m CPU / 500 MiB, with 10 warm-ups and 30 measured requests per start. All 18 first business requests and all 540 measured warm requests succeeded; no container was OOM-killed. Every GuicedEE run passed 12/15 capabilities and every Quarkus run passed 15/15. The omitted boolean, unsupported media and reactive timeout failures below remain unchanged, so these are **diagnostic timings, not a parity-qualified winner**.

| Variant | Median ready | Median first business completion from launch | Median warm p50 | Peak charged memory range |
|---|---:|---:|---:|---:|
| GuicedEE SPI, standard JRE | 9.018 s | 24.165 s | 93.92 ms | 278.7–285.0 MiB |
| GuicedEE scanner, standard JRE | 9.869 s | 24.708 s | 91.21 ms | 283.9–285.5 MiB |
| Quarkus, standard JRE | 6.613 s | 23.414 s | 88.47 ms | 276.8–282.2 MiB |
| GuicedEE SPI, jlink | 9.270 s | 24.111 s | 90.52 ms | 276.7–282.8 MiB |
| GuicedEE scanner, jlink | 9.727 s | 25.023 s | 92.05 ms | 279.2–285.8 MiB |
| Quarkus, jlink | 6.693 s | 23.598 s | 81.98 ms | 277.6–282.9 MiB |

Warm p50 is the median of each JVM's p50, at concurrency one. Default JVM flags are `-Xms128m -Xmx384m -XX:ActiveProcessorCount=2`. Order rotates/reverses between rounds. Three starts are a small sample: the standard-JRE scanner's first-business results range from 23.605 to 25.274 seconds. Do not interpret small differences as established speedups.

The scanner's measured ClassGraph work is 497–596 ms in this batch. The standard-JRE scanner adds 0.851 seconds to median readiness and 0.544 seconds to median first-business completion relative to SPI. The business request still takes approximately 15–17 seconds after readiness under the CPU cap. Logs show additional `org.reflections` scanning during commercetools SDK mapper initialization in the shared business path; this is separate from GuicedEE's ClassGraph scan.

Jlink did not show a consistent startup improvement. Its clear measured benefit is disk/image footprint:

| Packaged variant | Standard image | jlink image | Reduction |
|---|---:|---:|---:|
| GuicedEE SPI | 652.4 MiB | 588.2 MiB | 64.2 MiB |
| GuicedEE scanner | 652.4 MiB | 588.2 MiB | 64.2 MiB |
| Quarkus | 658.3 MiB | 594.0 MiB | 64.2 MiB |

Image values use Docker's reported image size, not registry transfer size. The JDK directory's apparent size drops from 190.8 to 117.8 MiB. All three linked variants use the same 31-module runtime and module-image hash; all standard variants use the same stock runtime hash. Both runtimes report Temurin 25.0.5+8. Jlink builds a custom JDK runtime around the unchanged classpath/fast-JAR applications, not a linked application module or native executable. The runtime includes a generic JDK CDS archive, with no application training. See [runtime construction](README.md#jlink-runtime-comparison).

### Same matrix with C1 applied equally

The [C1 matrix](results/20261114-113839/summary.json), with [runtime/image provenance](results/20261114-113839/environment.json), repeats three starts per variant using the **same immutable images and source hashes**. The only JVM flag change is `-XX:TieredStopAtLevel=1` for every variant. All 18 first business requests and all 540 measured warm requests succeeded, with no OOM kills. Discovery mode and both GuicedEE verticle deployments were verified in every run. Capability results are still 12/15 for GuicedEE and 15/15 for Quarkus.

| Variant | Median ready | Median first business completion from launch | Median warm p50 | Peak charged memory range |
|---|---:|---:|---:|---:|
| GuicedEE SPI, standard JRE + C1 | 5.915 s | 16.701 s | 84.09 ms | 240.0–241.2 MiB |
| GuicedEE scanner, standard JRE + C1 | 6.149 s | 16.862 s | 79.08 ms | 243.0–243.6 MiB |
| Quarkus, standard JRE + C1 | 4.273 s | 15.097 s | 67.08 ms | 245.2–245.5 MiB |
| GuicedEE SPI, jlink + C1 | 5.847 s | 16.253 s | 73.01 ms | 238.1–240.2 MiB |
| GuicedEE scanner, jlink + C1 | 5.989 s | 16.418 s | 75.25 ms | 240.8–243.1 MiB |
| Quarkus, jlink + C1 | 4.381 s | 15.598 s | 48.87 ms | 243.1–245.6 MiB |

The scanner adds 0.234 seconds to median readiness and 0.161 seconds to first-business completion on the standard JRE in this C1 batch. ClassGraph logs show 305–396 ms in five samples and a 1,001 ms outlier. Jlink's first-business median moves down about 0.45 seconds for both GuicedEE modes and up about 0.50 seconds for Quarkus; these three-run samples do not establish a general jlink startup benefit.

C1 reduces standard-JRE median first-business completion by 30.9% for GuicedEE SPI and 35.5% for Quarkus relative to the matched default-JVM matrix. It remains an optional startup-oriented setting; the sequential warm samples do not establish its sustained-throughput tradeoff. Do not compare these current figures with earlier images as a controlled verticle-only experiment: the earlier batches have different configuration/packaging snapshots.

The fixture reactor and seven harness tests passed. [Scanner/jlink verification](results/scanner-jlink-verification.json) records the completed matrices, source/JAR consistency checks and the separate capability failures. The current measurements support smaller runtime images and a modest scanning cost; they **do not demonstrate GuicedEE beating Quarkus**. Cold SDK initialization remains a substantial part of the first-business delay.

## Configuration checks: `.env`

The current GuicedEE fixture keeps [guicedee/.env](guicedee/.env), with no configuration annotations on Main or package-info. The temporary Main-annotation change was reverted. Resource and Service now occupy separate packages with their own `@Verticle` declarations. The earlier configuration checks below are preserved for their exact source/image snapshots.

A [local smoke check with annotated Main](results/20261114-111122/summary.json) verified successful startup, the first business response, Prometheus and the `.env` telemetry override. The same three known REST/timeout checks fail; this single-framework run makes no comparative timing claim.

The [Docker configuration smoke run](results/20261114-110626/summary.json) and [local working-directory check](results/20261114-110753/summary.json) start with no discovery CLI override, so SPI selection, Prometheus and disabled telemetry come from the file. Both first business responses succeed, and there are no measured warm-request errors. Capability counts remain GuicedEE 12/15 and Quarkus 15/15, with the same three known failures. The [configuration verification ledger](results/env-verification.json) records eight targeted Java checks and four harness checks, all passing; the new regression tests exercise real `.env` and `.env.local` files with no options annotations.

The timing tables below remain historical results for their exact recorded images. These configuration smoke runs are not new three-run startup estimates. The environment-only fixture uses native Vert.x defaults for unspecified options.

## Initial capped baseline

[Raw three-run baseline](results/20261114-102210/summary.json), with [environment and input hashes](results/20261114-102210/environment.json). Each framework started three fresh JVMs, in alternating order, with 10 warm-up requests followed by 30 measured requests per JVM. All first business responses succeeded, all 90 measured warm requests per framework succeeded, and none of the six containers reported an OOM kill.

| Metric | GuicedEE, initial scan profile | Quarkus |
|---|---:|---:|
| Median launch to ready | 8.854 s | 6.143 s |
| Median first business request duration | 14.698 s | 15.607 s |
| Median launch to first business completion | 23.853 s | 21.751 s |
| Median of per-run warm p50 | 88.82 ms | 83.26 ms |
| Whole-container peak charged memory, observed range | 281.3–290.4 MiB | 274.6–281.8 MiB |

These are diagnostic timings. The initial contract failed for GuicedEE, so `eligibleComparison` is false. The memory figure is cgroup `memory.peak`, not heap or process RSS. Three startup samples and 90 sequential warm requests are too few for a robust production latency or throughput claim.

## Earlier capability failures (fixed in the current matrix)

The [refined contract run](results/20261114-102719/summary.json) used the same initial images and separated an omitted primitive query parameter from validation/media tests. GuicedEE passed 12 of 15 checks; Quarkus passed 15 of 15.

| Check | GuicedEE observation | Required result |
|---|---|---|
| Omitted `boolean persist` query parameter | HTTP 400 with an unboxing `NullPointerException` | HTTP 200, `persist=false` |
| Unsupported `text/plain` body on JSON-only endpoint | HTTP 400 application validation envelope | HTTP 415 before invocation |
| `@Timeout(50)` around asynchronous completion | HTTP 200 `{"result":"late"}` after about 314 ms | HTTP 504 timeout envelope |

Valid business responses, actual vendor OAuth/REST/GraphQL calls, application validation, malformed-JSON status, three-attempt retry, retry exhaustion, a changing application metric, generated OpenAPI, Swagger UI and Firestore write/read passed. Framework-generated error-envelope consistency is not fully tested. Neither authentication nor Secret Manager, inbound GraphQL, tracing, cancellation, shutdown under traffic or Kubernetes scale-out is covered.

The earlier timeout interceptor waited for the Java method to return its reactive object and did not enforce a deadline on that object's eventual completion. Its then-existing suite passed; the service-level asynchronous check exposed the missing behavior. The current implementation and regression coverage are described above.

## Integrated SPI-only profile

The [three-run SPI batch](results/20261114-104245/summary.json), with [image/source provenance](results/20261114-104245/environment.json), uses the integrated package options, explicit discovery provider and updated adapters. GuicedEE starts without a ClassGraph scan. All six first business requests and all 90 measured warm requests per framework succeeded; there were no OOM kills. GuicedEE still passes 12/15 capability checks in every run; Quarkus passes 15/15. `eligibleComparison` remains false.

| Metric | GuicedEE SPI | Quarkus |
|---|---:|---:|
| Median launch to ready | 8.663 s | 6.204 s |
| Median first business request duration | 14.995 s | 15.598 s |
| Median launch to first business completion | 23.758 s | 21.801 s |
| Median of per-run warm p50 | 90.06 ms | 84.51 ms |
| Median of per-run warm p95 | 105.82 ms | 95.33 ms |
| Whole-container peak charged memory, observed range | 275.4–286.0 MiB | 273.1–279.9 MiB |

Removing scanning did **not** produce a material first-business improvement in these samples: 23.853 s initially versus 23.758 s with SPI. Do not attribute the small difference to SPI alone: the batches use different packaged configuration/adapters and only three starts each. Most of the observed first-business interval remains after readiness, while the SDKs initialize and execute their first calls.

The ten resolved GuicedEE application dependencies were checked against their current workspace target JARs; every SHA-256 matched. The runtime image IDs and packaged JAR hashes are recorded in the linked environment file.

## Equal startup-oriented JIT profile

The [three-run C1 batch](results/20261114-104548/summary.json), with [environment and immutable image provenance](results/20261114-104548/environment.json), adds `-XX:TieredStopAtLevel=1` to **both** applications. Everything else in the SPI profile is unchanged. All first business requests and all 90 measured warm requests per framework succeeded, with no OOM kills. Capability counts remain 12/15 versus 15/15; these timings therefore remain diagnostic.

| Metric | GuicedEE SPI + C1 | Quarkus + C1 |
|---|---:|---:|
| Median launch to ready | 5.422 s | 3.885 s |
| Median first business request duration | 9.499 s | 9.991 s |
| Median launch to first business completion | 14.835 s | 13.891 s |
| Median of per-run warm p50 | 34.95 ms | 35.49 ms |
| Median of per-run warm p95 | 89.40 ms | 88.13 ms |
| Whole-container peak charged memory, observed range | 239.5–241.5 MiB | 245.7–245.9 MiB |

Compared with the untuned SPI batch, median launch-to-first-business decreased by **37.6% for GuicedEE** and **36.3% for Quarkus**. This is a JVM tuning result for the capped fixture, not evidence of a framework-wide speedup. C1 disables higher-tier optimization; sustained concurrent load is required to assess its steady-state tradeoff. It remains opt-in in the runner and is not imposed on applications or framework defaults.

After these timed batches, the shared workload received its explicit `comparison.common` descriptor and the GuicedEE descriptor was updated to read it. The final reactor and both images were rebuilt. A [final capped C1 smoke run](results/20261114-105153/summary.json) repeated the successful first-business path and the same 12/15 versus 15/15 capability results. The tables above retain their original three-run image sets; this one-run smoke check does not replace those medians. All launches in this report use the classpath/fast-JAR paths, not a JPMS runtime launch.

## Changes driven by integration

- Added the root benchmark reactor, shared workload, two framework adapters, deterministic vendor fixture, official Firestore emulator setup, capability checks and Docker runner.
- Completed the GuicedEE JPMS descriptor and dual SPI registration. `@Counted` is the supported MicroProfile annotation; `MPCounter` is an implementation class. The timed SPI batches used package options; the current fixture uses `.env` as described above.
- Updated metrics and fault-tolerance option discovery to use `Discovery.annotations`, telemetry to prefer registered class/package options, and Vert.x to honor the package's `@VertX` configuration. Existing environment overrides remain in the option wrappers.
- Updated OpenAPI to consume registered resources in SPI mode while retaining the scanning fallback and its package/class filters. Jakarta REST remains optional in the OpenAPI module.
- Added immutable image input hashes and fixture-source snapshots. The runner pins image IDs before starting applications, so later rebuilds cannot change a sample midway through a batch.

The initial benchmark integration did not change retry or timeout implementation. The later framework fixes described above resolve the three REST/fault-tolerance gaps. No JSON/config dependency was added to core.

## Conditions and validation

Both containers use Temurin 25.0.5+8, `-Xms128m -Xmx384m -XX:ActiveProcessorCount=2`, 0.25 CPU, 500 MiB memory and no additional swap. The driver verifies effective cgroup limits. The vendor fixture and Firestore emulator run outside these limits. Container creation/start overhead is included; image building/pulling is excluded. No native image, trained JVM cache, unpacked-JAR optimization or page-cache flush was used.

The initial images predate the integrated package/SPI changes. Their IDs and binary hashes remain authoritative for that baseline; [source changes after the initial run](results/20261114-102210/source-changes-after-run.json) records the files that no longer matched its working-tree hashes. Later images include their own fixture-source snapshots. Do not substitute current sources for an older measured image.

Validation completed during integration: the benchmark Maven reactor packaged both applications and compiled the shared-workload and GuicedEE JPMS descriptors; three harness tests passed; the OpenAPI suite passed 7 tests, fault tolerance 16 tests, and focused metrics/telemetry/Vert.x checks 1, 3 and 1 tests respectively. The [verification ledger](results/verification.json) records these 31 checks. These are local checks, not a full DevSuite reactor or hosted CI result. The HTTP capability gate is reported separately from those passing tests.

The failed package-option setup also exposed an OpenTelemetry `RetryPolicy.getRetryExceptionPredicate` linkage error when tracing was accidentally enabled. Tracing is deliberately disabled in both measured profiles; dependency compatibility for a tracing-enabled variant remains unresolved and must be checked before adding that capability.

The next performance investigation should time and profile cold vendor/Firebase SDK initialization, alongside the remaining GuicedEE bootstrap cost. Under the CPU cap, the logs show vendor SDK initialization occupying an event-loop thread. That identifies work to investigate; it does not establish that scanning accounts for all startup latency.
