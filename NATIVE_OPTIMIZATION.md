# Native startup and footprint audit — 14 November 2026

This report uses GuicedEE's repackaged SDKs on both frameworks. The later
[comparison with normal Quarkus dependencies](STANDARD_QUARKUS_COMPARISON.md) uses an
independent Quarkus project and should be used for the upstream-dependency baseline.

GuicedEE's median launch-to-first-completed-business-request fell **18.5%, from 808 ms to 659 ms**.
Quarkus native measured **655 ms** in the same final batch. The remaining 4 ms difference is within
the observed run-to-run variation; this supports comparable startup for this reference workload,
not a general claim that either framework is faster. GuicedEE's executable fell **14.2%** and its
median peak container memory fell **7.2%**. Quarkus still uses less memory and disk space.

Evidence: [complete batch](results/20261114-222751/summary.json),
[calculated statistics and SDK hashes](results/20261114-222751/native-summary.json),
[compiler reachability audit](results/20261114-222751/native-reachability-audit.json), and
[original application JAR identity and module descriptors](results/20261114-222751/native-module-verification.txt).

| Measurement | GuicedEE before | GuicedEE after | Quarkus before | Quarkus after |
|---|---:|---:|---:|---:|
| Median launch → ready | 703 ms | **576 ms** | 573 ms | 572 ms |
| Median launch → full business completion | 808 ms | **659 ms** | 702 ms | 655 ms |
| Median peak container memory | 86.18 MiB | **79.98 MiB** | 63.19 MiB | 62.75 MiB |
| Median container memory at end | 82.66 MiB | **76.50 MiB** | 59.48 MiB | 59.13 MiB |
| Native executable | 223.69 MiB | **191.83 MiB** | 174.81 MiB | 158.01 MiB |
| Uncompressed Docker image | 462.55 MiB | **421.17 MiB** | 395.23 MiB | 374.96 MiB |
| Median per-run warm p50 | 4.66 ms | 4.31 ms | 4.65 ms | 4.47 ms |
| Median per-run warm p95 | 24.58 ms | 25.23 ms | 22.90 ms | 29.02 ms |
| Median per-run warm p99 | 29.07 ms | 30.71 ms | 25.69 ms | 31.92 ms |

Seven fresh processes per image, rotating/reversing execution order, with **420/420 capability
checks and 840/840 measured requests passing**. Each process has 10 warmups and 30 measured sequential
requests. All use 250m CPU, 500 MiB, no extra swap, and
`-Xms128m -Xmx384m -XX:ActiveProcessorCount=2`. The same pinned Mandrel 25.0.5 compiler, O2,
x86-64-v3 and Serial GC are used, without PGO. Framework-specific native features and initialization
policies remain different and are recorded with the image inputs. Quarkus received the same shared
SDK metadata improvement; its older executable was not used as the only comparison.

The business timer includes actual commercetools SDK OAuth/REST/GraphQL and Firebase Admin SDK
Firestore write/read completion against the deterministic fixture and official emulator. It does
not stop when a port opens. Warm requests include Firestore too. The fixture and emulator remain
outside the application resource limits. This is a fresh-process Docker test with warm host caches,
not Kubernetes scale-out, production-network latency or a rerun of the unavailable Q_v_H service.

GuicedEE's final business-completion range was **635–701 ms**, versus **648–714 ms** for updated
Quarkus. Readiness polling is at 50 ms intervals, so a few milliseconds between readiness medians
has no useful ranking significance. GuicedEE peak memory ranged **79.29–80.66 MiB**, versus
**81.05–108.11 MiB** for its preserved baseline. Memory is cgroup `memory.peak`, not Java heap size
or process RSS; Docker image size and executable size are separate measurements.

## Changes and inclusion evidence

- **Guice member analysis:** the optional native SPI now supports `inspectMemberInjection(...)`.
  It proves that the configured `JsonMapper`, `VertxImpl` and `MetricRegistry` classes have no
  injectable members and retains only their class identities. This avoids repeated runtime member
  analysis. Constructor injection, type listeners, inherited/generic injectable members and normal
  error/partial-result handling remain in Guice. No injector, service, credential or `.env` state
  is created or captured at build time.
- **Native discovery:** the optional native adapter replaces GuicedEE's scanner entry point with
  an explicit SPI-mode check. A native `GUICEDEE_DISCOVERY_MODE=scan` override fails with a clear
  message. JVM scanning is unchanged, and no core dependency on GraalVM, config-core or Jackson
  was introduced.
- **SDK metadata:** generated protobuf reflection entries are conditional on the corresponding
  message type being reachable. Monitoring and Storage generated methods disappear from this
  workload; Firestore's 9,974 reachable methods remain. The change is shared by both native
  projects. No SDK JAR or module descriptor was removed or changed. Conditional metadata follows
  the [GraalVM metadata model](https://www.graalvm.org/jdk25/reference-manual/native-image/metadata/).
- **Metadata provenance:** generation now reads the shade recipe embedded in each exact SDK JAR.
  A failed exploratory Quarkus rebuild exposed the old tool's use of newer workspace POM rules
  against the preserved SDK binaries. Both final builds use the corrected generator and matching
  verified SDK hashes. The failed build and earlier exploratory runs are retained.
- **Reflection and services:** framework metadata keeps traced member accesses plus constructor
  support instead of making every framework method and field reflectively invocable. The server
  benchmark uses headless compilation and excludes only audio/MIDI SPI providers; application
  service loading remains enabled. `-IncludeDesktop` / `NATIVE_DESKTOP=true` restores those providers.
- **Swagger assets:** library-owned native metadata includes the default UI's runtime files,
  including OAuth redirect scripts and favicons. Source maps and unused alternate bundles are
  omitted from the native image; all files remain in the JAR. Custom native metadata can include
  `{"module":"com.guicedee.swaggerui","glob":"swagger/**"}` to restore the full distribution.
  The HTTP handler streams bounded chunks with worker reads and asynchronous writes instead of
  copying an entire bundle into response buffers. The JVM test checks complete byte-for-byte JS,
  CSS and favicon responses and missing-resource handling; native checks validate the UI assets.

| Compiler audit | Baseline rebuild | Final build |
|---|---:|---:|
| Reachable methods | 273,042 | 232,581 |
| Methods registered for reflection | 142,290 | 108,899 |
| Reachable Monitoring methods | 16,350 | 0 |
| Reachable Storage methods | 10,012 | 0 |
| Reachable Firestore methods | 9,974 | 9,974 |
| Sound implementation methods | 1,029 | 14 |
| Methods on `ClassGraph` itself | 31 | 2 |

These are compiler reachability counts, not execution counts or per-package memory attribution.
ClassGraph compatibility/data types and some desktop metadata remain reachable; the entire modules
were not removed. Firebase remains the largest code origin at about **32.24 MB**, followed by
`java.base` (17.00 MB) and commercetools (6.52 MB). Other retained code includes XML, Jackson,
Log4j, Swagger and Vert.x. Their presence is not by itself proof that their code is unnecessary.
Generated native sidecar libraries are retained. Further memory work needs allocation/residency
evidence rather than deleting dependencies by name.

## Diagnostics and validation

The [separate native diagnostic](results/20261114-221910/summary.json), after member-analysis
preparation and before the later static-asset change, measured Guice injector creation at
**16.99 and 17.12 ms**. Its module-execution stage was 4 ms and member validation 3 ms in the first
run. These instrumented results are excluded from performance rankings. Guice's opt-in
`-Dguice_startup_diagnostics=true` exposes its internal stages on JVM and native runtimes.

The earlier [paired native batch](results/20261114-221748/native-summary.json) already showed
the startup improvement, but GuicedEE peak memory remained near 82 MiB. A separate
[`-Xms32m` experiment](results/20261114-222037/native-summary.json) did not materially reduce memory,
so the final comparison retains the original 128 MiB initial heap. Warm percentile ordering varies
between batches; these sequential samples do not establish throughput superiority.

Validation also passed 16 harness tests, 9 Guice tests, 2 optional native-support JVM tests,
and the expanded Swagger HTTP test. The final executable preserves the original SPI application
JAR and JPMS descriptors. The existing JVM/scanner/jlink matrix was not rerun in this native-focused
iteration; the Swagger HTTP test does exercise the changed serving path on the JVM.

## Reproduce

Preserve both original images under `native-before` before replacing `local`, then build the shared
metadata and both native candidates from the isolated repository. The GuicedEE build helper runs
its owning-module tests before staging artifacts:

```powershell
python benchmarks/tools/prepare_native_metadata.py --repository benchmarks/docker/repository
./benchmarks/docker/build-guicedee-native.ps1 -AuditNative
docker build --target quarkus-native -t devsuite-bench-quarkus-native:local -f benchmarks/docker/Dockerfile benchmarks
python benchmarks/tools/compare.py --docker --firebase --runtime native --baseline-image-tag native-before --runs 7 --requests 30 --warmup 10
python benchmarks/tools/summarize_native.py benchmarks/results/<batch>
```

Wait for all builds to finish before measuring. Immutable image IDs, runtime flags, source snapshots,
SDK hashes, capability responses and every latency sample are retained in each result directory.
`-AuditNative` retains call-tree/used-class reports in the builder; every runtime image includes
`/app/native-build-statistics.json`. Diagnostics can be repeated with `--diagnostics --framework
guicedee --runtime native --docker --firebase --runs 2 --requests 3 --warmup 1`.
