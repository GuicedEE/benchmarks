# GuicedEE benchmarks

A standalone benchmark suite for **GuicedEE 2.6.0**, comparing SPI and scanner discovery,
full-JDK and application-jlink execution, and native executables against normal Quarkus
applications. Both frameworks execute the same commercetools/GraphQL/Firestore business
workload, with REST, retries, timeouts, metrics, OpenAPI and Swagger capability checks.

## Performance

<!-- BEGIN GENERATED: headline -->
GuicedEE native completes the first full business request in **657 ms**, versus **684 ms** for Quarkus native (**4.0% less time**). Warm p50 is **5.29 / 5.53 ms** (GuicedEE / Quarkus). Peak charged memory is **79.78 / 55.25 MiB**; executables are **191.83 / 143.31 MiB**. The native sample contains **28 starts and 420 passing capability checks**.
<!-- END GENERATED: headline -->

<!-- BEGIN GENERATED: build-headline -->
**Clean JVM build:** GuicedEE SPI compiles in **3.01 s** versus **3.65 s** for Quarkus (**17.5% less time**). Complete runnable JVM packaging takes **3.69 / 6.17 s** (GuicedEE / Quarkus), **40.2% less time**. Medians of 3 clean, offline builds per task; dependency preparation is excluded.
<!-- END GENERATED: build-headline -->

**Median launch to completed business response, seconds.** JVM/default and C1 columns use
matched seven-mode Docker batches at **250m CPU / 500 MiB**. The native column uses a larger
counterbalanced native-only sample. Links open the full timing and memory grids.

<!-- BEGIN GENERATED: overview -->
| Application | Full JDK default (s) | Full JDK C1 (s) | Application jlink default (s) | Application jlink C1 (s) | Native (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI | [27.917](RESULTS.md#jvm-default) | [17.191](RESULTS.md#jvm-c1) | [13.401](RESULTS.md#jvm-default) | [7.637](RESULTS.md#jvm-c1) | [0.657](RESULTS.md#native-standard) |
| GuicedEE scanner | [29.629](RESULTS.md#jvm-default) | [17.641](RESULTS.md#jvm-c1) | [13.704](RESULTS.md#jvm-default) | [7.817](RESULTS.md#jvm-c1) | SPI only |
| Quarkus / upstream SDKs | [23.879](RESULTS.md#jvm-default) | [14.015](RESULTS.md#jvm-c1) | Not implemented | Not implemented | [0.684](RESULTS.md#native-standard) |
<!-- END GENERATED: overview -->

![Startup by execution mode](docs/startup.svg)

[The full results](RESULTS.md) include readiness, first-request and full-business startup,
warm p50/p95/p99, memory, executable/image sizes, **percentage differences for every
GuicedEE mode**, and scanning/Guice/commercetools/Firestore phase analysis. Actual image IDs,
artifact hashes, flags and sample counts accompany the measurements. C1 applies equally to
all JVMs; native executables have no JIT tiering.

## Compile and package time

<!-- BEGIN GENERATED: build-grid -->
| Artifact | Clean compile (s) | Compile min–max (s) | Complete package (s) | Package min–max (s) | Package difference vs Quarkus |
| --- | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3.01 | 2.93–3.05 | 3.69 | 3.65–3.74 | -40.2% |
| GuicedEE scanner / full JDK | 3.05 | 3.02–3.10 | 3.64 | 3.57–3.68 | -41.1% |
| Quarkus upstream SDKs / fast-JAR | 3.65 | 3.57–4.17 | 6.17 | 6.16–6.55 | Baseline |
| GuicedEE SPI / application jlink | — | — | 17.82 | 17.46–17.91 | +188.7% |
| GuicedEE scanner / application jlink | — | — | 17.70 | 17.45–17.71 | +186.7% |
| GuicedEE SPI / native | — | — | 82.36 | 80.96–85.08 | +24.0% |
| Quarkus upstream SDKs / native | — | — | 66.44 | 66.34–69.67 | Baseline |
<!-- END GENERATED: build-grid -->

![Clean compilation and complete packaging](docs/builds.svg)

Complete packaging includes runtime dependencies for JVM artifacts, runtime creation for
jlink, and native compilation for native executables. Native rows compare with Quarkus
native; other rows compare with Quarkus fast-JAR. A dash means that compilation is covered
by the underlying application, rather than timed again as a separate packaging project.
The build machine has its full CPU/memory allocation; runtime tests use the stated 250m/500 MiB
limits. [Build protocol, ranges and runtime tradeoffs](RESULTS.md#build-performance) and
[build CSV](docs/build-performance.csv) make those costs explicit.

## First-use SDK cost

<!-- BEGIN GENERATED: sdk-headline -->
**Commercetools first-use initialization:** GuicedEE SPI jlink records **1.287 s** versus **16.611 s** for standard Quarkus JVM: **15.325 s less** (**92.3% less time**). These are instrumented phase diagnostics (3 GuicedEE starts, 1 Quarkus start), separate from build time and the uninstrumented runtime rankings. The samples identify a first-use cost; they do not establish its cause or a general SDK performance ratio.
<!-- END GENERATED: sdk-headline -->

The [phase grid](RESULTS.md#first-use-business-phases) also includes scanner, wrapped-SDK
control and native diagnostics, plus REST/OAuth, GraphQL and Firestore completion.

## Run it

Install JDK 25, Maven 4, Python 3.11+, Node.js 22+ and Docker with Linux containers, then:

```shell
git -c core.longpaths=true clone --depth 1 https://github.com/GuicedEE/benchmarks.git
cd benchmarks
python tools/build.py --docker --runtime both --native
python tools/compare.py --docker --firebase --runtime both --native --runs 5 --requests 100 --warmup 20
# Repeat the same matrix with equal C1 tuning:
python tools/compare.py --docker --firebase --runtime both --native --tiered --runs 5 --requests 100 --warmup 20
# Measure clean compilation and packaging of all seven artifacts:
python tools/compare_builds.py --docker --runs 3
```

GuicedEE dependencies resolve through Maven. No DevSuite checkout, private framework path,
vendor account or production credentials are required. The build sets up the local Firestore
emulator; the runner starts the deterministic vendor fixture and enforces container limits.
See [RUNNING.md](RUNNING.md) for individual modes, configuration, explicit artifact repositories,
native metadata and diagnostics.

## Repository layout

| Path | Purpose |
|---|---|
| `guicedee`, `guicedee-scan` | Separate modular SPI and scanner applications |
| `guicedee-jlink`, `guicedee-scan-jlink`, `guicedee-native` | Linked-runtime and native packaging |
| `quarkus-standard` | Default Quarkus JVM/native comparison with upstream SDK dependencies |
| `common`, `quarkus`, `quarkus-native` | Shared workload, Quarkus adapter and optional wrapped-SDK control/build support |
| `fixtures`, `docker`, `tools` | Local services, image recipes, build/measurement/report tools |
| `results/latest` | Only the current published raw measurements and their manifest |
| `target/runs` | Ignored output of new executions |

[CSV](docs/current-performance.csv) and [JSON](docs/current-performance.json) expose the full
numeric grids. [Publishing results](results/README.md) replaces current measurements without
accumulating reports, source snapshots or experiment archives in the repository.

```shell
python -m unittest discover -s tools -p test_harness.py
python tools/verify_latest.py
python tools/render_performance.py --check
```

Measurements cover this local reference workload and its completed reactive flow. They are
sequential latency tests, not sustained-load throughput or production WAN measurements.
