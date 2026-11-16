# GuicedEE benchmarks

A standalone benchmark suite for **GuicedEE 2.6.0**, comparing SPI and scanner discovery,
full-JDK and application-jlink execution, and native executables against normal Quarkus
and **Micronaut Platform 5.2.6** applications. All three execute the same commercetools/GraphQL/Firestore business
workload, with REST, retries, timeouts, metrics, OpenAPI and Swagger capability checks.

## Repository layout

| Path | Purpose |
|---|---|
| `guicedee`, `guicedee-scan` | Separate modular SPI and scanner applications |
| `guicedee-jlink`, `guicedee-scan-jlink`, `guicedee-native` | Linked-runtime and native packaging |
| `guicedee-cdi`, `guicedee-cdi-spi`, and their jlink/native projects | Jakarta CDI and MicroProfile Config equivalents |
| `quarkus-standard` | Default Quarkus JVM/native comparison with upstream SDK dependencies |
| `micronaut` | Independent Micronaut JVM/native application using the upstream platform and SDKs |
| `common`, `quarkus`, `quarkus-native` | Shared workload, Quarkus adapter and optional wrapped-SDK control/build support |
| `persistence/model`, `persistence/guicedee`, `persistence/quarkus`, `persistence/micronaut` | Shared 15-entity PostgreSQL workload, reactive stateless GuicedEE, Narayana Quarkus and Micronaut Hibernate adapters |
| `fixtures`, `docker`, `tools` | Local services, image recipes, build/measurement/report tools |
| `results/latest` | Only the current published raw measurements and their manifest |
| `target/runs` | Ignored output of new executions |

## Performance

The SDK workload is reported below. The separate [PostgreSQL persistence comparison](persistence/README.md)
measures transactions over 15 related entities; its [results](RESULTS.md#postgresql-persistence)
include committed writes, joined reads, updates and rollbacks.
The [current persistence profile](docs/PERSISTENCE_PROFILE.md) separates Hibernate startup,
reactive allocations and PostgreSQL work from the benchmark timings.

<!-- BEGIN GENERATED: headline -->
GuicedEE native completes the first full business request in **655 ms**, versus **681 ms** for Quarkus native (**3.9% less time**). Warm p50 is **4.93 / 5.19 ms** (GuicedEE / Quarkus). Peak charged memory is **68.57 / 55.30 MiB**; executables are **142.35 / 143.31 MiB**. Micronaut native completes the same first business response in **627 ms**, with warm p50 **5.25 ms**, peak charged memory **85.26 MiB** and a **205.94 MiB** executable. The native sample contains **18 starts and 270 passing capability checks**.
<!-- END GENERATED: headline -->

<!-- BEGIN GENERATED: build-headline -->
**Clean JVM build:** GuicedEE SPI compiles in **3.52 s** versus **4.01 s** for Quarkus (**12.4% less time**). Complete runnable JVM packaging takes **4.10 / 6.80 s** (GuicedEE / Quarkus), **39.7% less time**. Medians of 3 clean, offline builds per task; dependency preparation is excluded.

**jlink versus native build:** GuicedEE SPI/scanner jlink packages in **18.25 / 17.88 s**, versus **70.91 s** for Quarkus native (**74.3% less time / 74.8% less time**).

**Micronaut:** compile **5.68 s**, JVM package **5.85 s**, native package **92.24 s**. GuicedEE SPI JVM packaging uses **30.0% less time**; SPI jlink uses **80.2% less time** than Micronaut native packaging.
<!-- END GENERATED: build-headline -->

**Median launch to completed business response, seconds.** JVM/default and C1 columns use
matched ten-mode Docker batches at **250m CPU / 500 MiB**. The native column uses a separate
four-mode sample, including CDI/config. Links open the full timing and memory grids.

<!-- BEGIN GENERATED: overview -->
| Application | Full JDK default (s) | Full JDK C1 (s) | Application jlink default (s) | Application jlink C1 (s) | Native (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI | [22.367](RESULTS.md#jvm-default) | [13.290](RESULTS.md#jvm-c1) | [13.005](RESULTS.md#jvm-default) | [8.300](RESULTS.md#jvm-c1) | [0.655](RESULTS.md#native-standard) |
| GuicedEE scanner | [23.862](RESULTS.md#jvm-default) | [13.480](RESULTS.md#jvm-c1) | [13.195](RESULTS.md#jvm-default) | [7.777](RESULTS.md#jvm-c1) | SPI only |
| GuicedEE CDI SPI | Not measured | Not measured | Not measured | Not measured | Not measured |
| GuicedEE CDI scanner | Not measured | Not measured | Not measured | Not measured | SPI only |
| Quarkus / upstream SDKs | [23.320](RESULTS.md#jvm-default) | [14.177](RESULTS.md#jvm-c1) | Not implemented | Not implemented | [0.681](RESULTS.md#native-standard) |
| Micronaut / upstream SDKs | [26.573](RESULTS.md#jvm-default) | [15.658](RESULTS.md#jvm-c1) | Not implemented | Not implemented | [0.627](RESULTS.md#native-standard) |
<!-- END GENERATED: overview -->

![Startup by execution mode](docs/startup.svg)

[The full results](RESULTS.md) include readiness, first-request and full-business startup,
warm p50/p95/p99, memory, executable/image sizes, **percentage differences for every
GuicedEE and Micronaut mode**, and scanning/Guice/commercetools/Firestore phase analysis. Actual image IDs,
artifact hashes, flags and sample counts accompany the measurements. C1 applies equally to
all JVMs; native executables have no JIT tiering.

The current JVM wrapper shares the SDK's duplicate Reflections scan during each mapper
construction, then releases it. Full-JDK tests preserve SDK and application mixins/subtypes,
mapper options and an independent-scan override. The GuicedEE JVM and native artifacts retain
their separately identified dependency hashes. The clean-build grid is a fresh independent
cohort; its artifact inputs are recorded alongside the timings. See the
[measurement boundaries](RESULTS.md#jvm-discovery-boundaries).

The [native inclusion profile](RESULTS.md#native-inclusion-and-allocation-profile) records the
current compiler footprint and SDK reflection, provider and buffer-pool policies, including
the available overrides. The separate
[1,000-request cohort](RESULTS.md#extended-native-request-sequence) shows memory after a longer
request sequence; its smaller cold-start sample is reported separately from the headline.

## Compile and package time

<!-- BEGIN GENERATED: build-grid -->
| Artifact | Clean compile (s) | Compile min–max (s) | Complete package (s) | Package min–max (s) | Build baseline | Package difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3.52 | 3.47–3.91 | 4.10 | 3.92–4.19 | Quarkus fast-JAR | -39.7% |
| GuicedEE scanner / full JDK | 3.72 | 3.33–3.81 | 3.88 | 3.76–4.47 | Quarkus fast-JAR | -42.8% |
| Quarkus upstream SDKs / fast-JAR | 4.01 | 3.87–4.47 | 6.80 | 6.66–6.89 | Quarkus fast-JAR | Baseline |
| GuicedEE SPI / application jlink | — | — | 18.25 | 18.14–19.46 | Quarkus native | -74.3% |
| GuicedEE scanner / application jlink | — | — | 17.88 | 17.41–18.44 | Quarkus native | -74.8% |
| GuicedEE SPI / native | — | — | 67.86 | 66.25–86.94 | Quarkus native | -4.3% |
| Quarkus upstream SDKs / native | — | — | 70.91 | 68.84–85.88 | Quarkus native | Baseline |
| Micronaut upstream SDKs / JVM | 5.68 | 5.12–5.82 | 5.85 | 5.59–6.48 | Quarkus fast-JAR | -13.9% |
| Micronaut upstream SDKs / native | — | — | 92.24 | 84.91–95.63 | Quarkus native | +30.1% |
<!-- END GENERATED: build-grid -->

![Clean compilation and complete packaging](docs/builds.svg)

Complete packaging includes runtime dependencies for JVM artifacts, runtime creation for
jlink, and native compilation for native executables. **jlink and native build times compare
with Quarkus native**; full-JDK JVM builds compare with Quarkus fast-JAR. The chart also places
both jlink modes alongside all three native applications. A dash means that compilation is covered
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
# Measure clean compilation and packaging of all nine artifacts:
python tools/compare_builds.py --docker --runs 3
```

GuicedEE dependencies resolve through Maven. No DevSuite checkout, private framework path,
vendor account or production credentials are required. The build sets up the local Firestore
emulator; the runner starts the deterministic vendor fixture and enforces container limits.
See [RUNNING.md](RUNNING.md) for individual modes, configuration, explicit artifact repositories,
native metadata and diagnostics.

[CSV](docs/current-performance.csv) and [JSON](docs/current-performance.json) expose the full
numeric grids. [Publishing results](results/README.md) replaces current measurements without
accumulating reports, source snapshots or experiment archives in the repository.

```shell
python -m unittest discover -s tools -p "test_*.py"
python tools/verify_latest.py
python tools/render_performance.py --check
python tools/render_persistence.py --check
```

Measurements cover this local reference workload and its completed reactive flow. They are
sequential latency tests, not sustained-load throughput or production WAN measurements.

The optional [Jakarta CDI/config comparison](RUNNING.md#jakarta-cdi-and-applicationproperties-comparison)
adds Jakarta scopes/injection and MicroProfile Config backed by `application.properties`
across scanner/SPI JVM and application-jlink variants, plus SPI native. Select it with
`--cdi-config` on both build and measurement commands. Native runtime scanning is unsupported.
