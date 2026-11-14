# GuicedEE native

The latest [startup and footprint audit](NATIVE_OPTIMIZATION.md) closes the measured startup gap to
**659 ms versus 655 ms** for Quarkus native, reduces GuicedEE's executable to **191.83 MiB** and
median peak container memory to **79.98 MiB**. All 420 capability checks pass in the final paired
batch. The first complete native comparison below is retained as historical evidence.

## First working native images

GuicedEE now builds and runs the full SPI reference service as a native executable. In the final
five-start comparison, median launch-to-first-business completion is **735 ms**, versus **669 ms**
for Quarkus native: a **66 ms / 9.9%** gap. This measures completion of the real commercetools
OAuth/REST/GraphQL and Firestore work, not merely an available HTTP port.

All **150/150 capability checks** passed across ten starts. All **300 measured warm requests**
succeeded. The Swagger check now also fetches and validates its JavaScript bundle and stylesheet.

## Measurements

Final batch: [20261114-212840](results/20261114-212840/summary.json).
[Calculated statistics and SDK hash verification](results/20261114-212840/native-summary.json).
[Environment, image identities and source snapshots](results/20261114-212840/environment.json).
[Application JAR identity, SDK hashes and preserved module descriptors](results/20261114-212840/native-module-verification.txt).

| Measurement | GuicedEE native | Quarkus native | GuicedEE relative to Quarkus |
|---|---:|---:|---:|
| Median launch → ready | 629 ms | 578 ms | 8.8% longer |
| Median launch → first completed business request | **735 ms** | **669 ms** | **9.9% longer** |
| Median first business request duration, after ready | 104 ms | 87 ms | 20.6% longer |
| Median of per-run warm p50 | 5.57 ms | 6.26 ms | 10.9% shorter |
| Median of per-run warm p95 | 26.50 ms | 26.87 ms | 1.4% shorter |
| Median peak container memory | 81.7 MiB | 63.2 MiB | 29.2% larger |
| Native executable | 223.7 MiB | 174.8 MiB | 28.0% larger |
| Uncompressed Docker image | 462.6 MiB | 395.2 MiB | 17.0% larger |

GuicedEE readiness ranged from 582–633 ms; Quarkus from 564–588 ms. First-business completion
ranged from 670–1,200 ms and 630–693 ms respectively. The single slowest GuicedEE first request
is retained in the data. Five starts and 30 measured warm requests per start are a small sample;
the warm results do not establish a general throughput advantage. Readiness polling uses 50 ms
intervals. Container memory is the cgroup peak, not Java heap size or process RSS.

An earlier eligible batch, [20261114-212404](results/20261114-212404/summary.json), measured
849 ms versus 682 ms for median first-business completion. The final source cleanup avoids
allocating an AOT-only cache in ordinary Guice builders, followed by a fresh build and repeat.
The difference between batches is not evidence that this allocation alone saved 114 ms.
Both batches put Quarkus ahead on startup; the warm ordering varies.

The [earlier failed batch](results/20261114-211508/summary.json) is excluded: GuicedEE returned
404 for Swagger's JavaScript and CSS. The initial single-variant probe used the older HTML-only
Swagger check and is not a ranked comparison.

## Comparable conditions

Both images use **Mandrel 25.0.5**, the same pinned Linux compiler image, `-O2`, x86-64-v3,
Serial GC and no PGO. Runtime limits are **0.25 CPU / 500 MiB**, with no extra swap;
`-Xms128m -Xmx384m -XX:ActiveProcessorCount=2` applies to both. Neither native image receives
JIT tiering flags. The harness verifies their ELF entry points and absence of a JVM.

The Firebase and commercetools compiler-input hashes match between the two native builds.
The adapters share the business workload and local vendor fixture; Firestore uses the official
emulator. Fixtures run outside the service container limits. Processes are fresh and order rotates
and reverses; filesystem caches are not flushed. Build time, image pulls and Kubernetes scheduling
are excluded. The original Q_v_H application remains unavailable and is not reproduced here.

Image IDs:

- GuicedEE: `sha256:3dd1fe1458f2236804fd28b2ab08ee60f60531d7846b9f25a05ec232c18b27d3`
- Quarkus: `sha256:c3928e04b0e4d53f84c4755a10cb71b837806387db509cac6ef99ca2711c109d`

## Implementation and validation

- [Optional native support](docs/FRAMEWORK_SOURCES.md#native-support) prepares Guice interception classes
  at build time. Injector creation, scopes, interceptor state, services, `.env` and SDK clients remain
  runtime concerns. Guice retains its normal JVM path and has no GraalVM dependency.
- The separate [Maven project](guicedee-native/pom.xml) depends on the existing SPI application JAR.
  It preserves its main class, business code and module descriptor. Metadata is contributed by SPI;
  unregistered interception selections fail explicitly. Interception is not disabled.
  The SPI application's built JAR and the native compiler's copy have identical SHA-256 hashes.
- SDK substitutions and relocated metadata are shared with Quarkus native. The native module path
  enumerates JARs explicitly: a directory module path loads Java modules but omitted their embedded
  native-image configuration in this toolchain. Traced resources are mapped to their owning modules.
- OpenAPI owns native reflection metadata for its model types. Swagger UI owns metadata for all its
  bundled assets. Netty initializes at runtime so its package-wide build-time defaults cannot capture
  the build machine's logging state. The final image includes emitted native sidecar libraries.
- JVM checks passed: **9 Guice**, **2 optional-native compatibility**, **14 OpenAPI**, **1 Swagger UI**
  and **14 harness tests**. Native checks additionally exercise reactive retry/exhaustion, bounded
  asynchronous timeout, counters, JSON/error handling, generated OpenAPI, full Swagger assets,
  actual SDK requests and Firestore writes/reads.

This is an initial native integration for the reference service. Runtime ClassGraph scanning,
arbitrary new interceptor selections, all Firebase products, production TLS/authentication,
long-running load and Kubernetes scale-out are not validated by this fixture. Native size and
metadata scope remain worth optimizing; Quarkus still uses less memory and a smaller executable.

## Reproduce

```powershell
./benchmarks/docker/build-guicedee-native.ps1
python benchmarks/tools/compare.py --docker --firebase --runtime native --runs 5 --requests 30 --warmup 10
```

See the [native project instructions](guicedee-native/README.md) for fresh SDK traces and building
Quarkus native when it is not already present. The supporting library is also available through the
opt-in root Maven profile `guicedee-native`.
