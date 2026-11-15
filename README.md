# GuicedEE benchmarks

A standalone benchmark suite for **GuicedEE 2.6.0**, comparing SPI and scanner discovery,
full-JDK and application-jlink execution, and native executables against normal Quarkus
applications. Both frameworks execute the same commercetools/GraphQL/Firestore business
workload, with REST, retries, timeouts, metrics, OpenAPI and Swagger capability checks.

## Performance

<!-- BEGIN GENERATED: headline -->
GuicedEE native completes the first full business request in **656 ms**, versus **678 ms** for Quarkus native (**3.2% less time**). Warm p50 is **5.21 / 5.11 ms** (GuicedEE / Quarkus). Peak charged memory is **68.47 / 55.30 MiB**; executables are **142.35 / 143.31 MiB**. The native sample contains **28 starts and 420 passing capability checks**.
<!-- END GENERATED: headline -->

<!-- BEGIN GENERATED: build-headline -->
**Clean JVM build:** GuicedEE SPI compiles in **3.14 s** versus **3.66 s** for Quarkus (**14.1% less time**). Complete runnable JVM packaging takes **3.61 / 6.29 s** (GuicedEE / Quarkus), **42.6% less time**. Medians of 3 clean, offline builds per task; dependency preparation is excluded.

**jlink versus native build:** GuicedEE SPI/scanner jlink packages in **17.68 / 17.34 s**, versus **66.36 s** for Quarkus native (**73.4% less time / 73.9% less time**).
<!-- END GENERATED: build-headline -->

**Median launch to completed business response, seconds.** JVM/default and C1 columns use
matched five-mode Docker batches at **250m CPU / 500 MiB**. The native column uses a larger
counterbalanced native-only sample. Links open the full timing and memory grids.

<!-- BEGIN GENERATED: overview -->
| Application | Full JDK default (s) | Full JDK C1 (s) | Application jlink default (s) | Application jlink C1 (s) | Native (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI | [22.928](RESULTS.md#jvm-default) | [13.353](RESULTS.md#jvm-c1) | [12.966](RESULTS.md#jvm-default) | [7.567](RESULTS.md#jvm-c1) | [0.656](RESULTS.md#native-standard) |
| GuicedEE scanner | [23.706](RESULTS.md#jvm-default) | [13.364](RESULTS.md#jvm-c1) | [13.556](RESULTS.md#jvm-default) | [7.874](RESULTS.md#jvm-c1) | SPI only |
| Quarkus / upstream SDKs | [23.387](RESULTS.md#jvm-default) | [14.311](RESULTS.md#jvm-c1) | Not implemented | Not implemented | [0.678](RESULTS.md#native-standard) |
<!-- END GENERATED: overview -->

![Startup by execution mode](docs/startup.svg)

[The full results](RESULTS.md) include readiness, first-request and full-business startup,
warm p50/p95/p99, memory, executable/image sizes, **percentage differences for every
GuicedEE mode**, and scanning/Guice/commercetools/Firestore phase analysis. Actual image IDs,
artifact hashes, flags and sample counts accompany the measurements. C1 applies equally to
all JVMs; native executables have no JIT tiering.

The current JVM wrapper shares the SDK's duplicate Reflections scan during each mapper
construction, then releases it. Full-JDK tests preserve SDK and application mixins/subtypes,
mapper options and an independent-scan override. Native images and the clean-build grid
retain their separately identified earlier artifact cohort; they were not rebuilt for this
JVM change. See the [measurement boundaries](RESULTS.md#jvm-discovery-boundaries).

The [native inclusion profile](RESULTS.md#native-inclusion-and-allocation-profile) records the
current compiler footprint and SDK reflection, provider and buffer-pool policies, including
the available overrides. The separate
[1,000-request cohort](RESULTS.md#extended-native-request-sequence) shows memory after a longer
request sequence; its smaller cold-start sample is reported separately from the headline.

## Compile and package time

<!-- BEGIN GENERATED: build-grid -->
| Artifact | Clean compile (s) | Compile min–max (s) | Complete package (s) | Package min–max (s) | Build baseline | Package difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3.14 | 3.13–3.32 | 3.61 | 3.54–3.79 | Quarkus fast-JAR | -42.6% |
| GuicedEE scanner / full JDK | 3.05 | 3.02–3.26 | 3.68 | 3.63–3.69 | Quarkus fast-JAR | -41.5% |
| Quarkus upstream SDKs / fast-JAR | 3.66 | 3.59–3.81 | 6.29 | 6.19–6.32 | Quarkus fast-JAR | Baseline |
| GuicedEE SPI / application jlink | — | — | 17.68 | 17.42–17.71 | Quarkus native | -73.4% |
| GuicedEE scanner / application jlink | — | — | 17.34 | 17.24–17.35 | Quarkus native | -73.9% |
| GuicedEE SPI / native | — | — | 65.05 | 64.97–80.24 | Quarkus native | -2.0% |
| Quarkus upstream SDKs / native | — | — | 66.36 | 66.07–66.67 | Quarkus native | Baseline |
<!-- END GENERATED: build-grid -->

![Clean compilation and complete packaging](docs/builds.svg)

Complete packaging includes runtime dependencies for JVM artifacts, runtime creation for
jlink, and native compilation for native executables. **jlink and native build times compare
with Quarkus native**; full-JDK JVM builds compare with Quarkus fast-JAR. The chart also places
both jlink modes alongside GuicedEE native. A dash means that compilation is covered
by the underlying application, rather than timed again as a separate packaging project.
The build machine has its full CPU/memory allocation; runtime tests use the stated 250m/500 MiB
limits. [Build protocol, ranges and runtime tradeoffs](RESULTS.md#build-performance) and
[build CSV](docs/build-performance.csv) make those costs explicit.

## First-use SDK cost

<!-- BEGIN GENERATED: sdk-headline -->
**Commercetools first-use initialization:** GuicedEE SPI JVM records **13.995 s** versus **11.503 s** for standard Quarkus JVM: **2.492 s more** (**21.7% more time**). These are instrumented phase diagnostics (GuicedEE n=1, Quarkus n=1), separate from build time and the uninstrumented runtime rankings. The samples identify a first-use cost; they do not establish a general SDK performance ratio. The linked-image SDK scanner reports zero URLs; jlink timings cover the tested workload, not complete SDK mixin/subtype discovery.
<!-- END GENERATED: sdk-headline -->

The [phase grid](RESULTS.md#first-use-business-phases) also includes scanner, jlink and native
diagnostics, plus REST/OAuth, GraphQL and Firestore completion.

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
