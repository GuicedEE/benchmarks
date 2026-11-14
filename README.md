# GuicedEE benchmarks

A standalone benchmark suite for **GuicedEE 2.6.0**, comparing SPI and scanner discovery,
full-JDK and application-jlink execution, and native executables against normal Quarkus
applications. Both frameworks execute the same commercetools/GraphQL/Firestore business
workload, with REST, retries, timeouts, metrics, OpenAPI and Swagger capability checks.

## Performance

<!-- BEGIN GENERATED: headline -->
GuicedEE native completes the first full business request in **657 ms**, versus **684 ms** for Quarkus native (**4.0% less time**). Warm p50 is **5.29 / 5.53 ms** (GuicedEE / Quarkus). Peak charged memory is **79.78 / 55.25 MiB**; executables are **191.83 / 143.31 MiB**. The native sample contains **28 starts and 420 passing capability checks**.
<!-- END GENERATED: headline -->

**Median launch to completed business response, seconds.** JVM/default and C1 columns use
matched seven-mode Docker batches at **250m CPU / 500 MiB**. The native column uses a larger
counterbalanced native-only sample. Links open the full timing and memory grids.

<!-- BEGIN GENERATED: overview -->
| Application | Full JDK default (s) | Full JDK C1 (s) | Application jlink default (s) | Application jlink C1 (s) | Native (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI | [28.177](RESULTS.md#jvm-default) | [16.746](RESULTS.md#jvm-c1) | [15.138](RESULTS.md#jvm-default) | [7.938](RESULTS.md#jvm-c1) | [0.657](RESULTS.md#native-standard) |
| GuicedEE scanner | [27.831](RESULTS.md#jvm-default) | [17.431](RESULTS.md#jvm-c1) | [14.155](RESULTS.md#jvm-default) | [8.387](RESULTS.md#jvm-c1) | SPI only |
| Quarkus / upstream SDKs | [24.074](RESULTS.md#jvm-default) | [14.168](RESULTS.md#jvm-c1) | Not implemented | Not implemented | [0.684](RESULTS.md#native-standard) |
<!-- END GENERATED: overview -->

![Startup by execution mode](docs/startup.svg)

[The full results](RESULTS.md) include readiness, first-request and full-business startup,
warm p50/p95/p99, memory, executable/image sizes, **percentage differences for every
GuicedEE mode**, and scanning/Guice/commercetools/Firestore phase analysis. Actual image IDs,
artifact hashes, flags and sample counts accompany the measurements. C1 applies equally to
all JVMs; native executables have no JIT tiering.

## Run it

Install JDK 25, Maven 4, Python 3.11+, Node.js 22+ and Docker with Linux containers, then:

```shell
git -c core.longpaths=true clone --depth 1 https://github.com/GuicedEE/benchmarks.git
cd benchmarks
python tools/build.py --docker --runtime both --native
python tools/compare.py --docker --firebase --runtime both --native --runs 5 --requests 100 --warmup 20
# Repeat the same matrix with equal C1 tuning:
python tools/compare.py --docker --firebase --runtime both --native --tiered --runs 5 --requests 100 --warmup 20
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
