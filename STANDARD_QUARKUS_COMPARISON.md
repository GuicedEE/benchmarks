# Native comparison with normal Quarkus dependencies

GuicedEE completes this reference workload sooner at the median: **668 ms versus 706 ms
from launch to the first completed business request (5.4% less time)**. Its median warm
request is **5.18 ms versus 6.02 ms (14.0% less time)**. Quarkus retains a substantial
footprint advantage: GuicedEE needs **24.25 MiB more peak container memory**, a
**48.52 MiB larger executable**, and a **68.13 MiB larger container image**.

These results support accepting some footprint cost for the measured latency benefit.
They do not establish that GuicedEE is faster for every workload or percentile. The size
cost here is **33.9% for the executable / 19.3% for the complete image**, rather than a
negligible difference.

## Results

Two independently started batches reverse which framework runs first, then alternate/rotate
their order within each batch. There are **14 fresh starts per framework**, **420 passing
capability checks**, and **840 successful measured requests**. Each start also has 10 warmups.
All starts, including first-use outliers, remain in the statistics.

| Measurement | GuicedEE native, SPI | Quarkus native, upstream SDKs | GuicedEE relative to Quarkus |
|---|---:|---:|---:|
| Median launch → HTTP ready | 582 ms | 577 ms | Within the 50 ms polling granularity |
| Median launch → full business completion | **668 ms** | 706 ms | **5.4% less time** |
| Median first business request alone | **86.4 ms** | 129.0 ms | **33.0% less time** |
| Median of per-start warm p50 | **5.18 ms** | 6.02 ms | **14.0% less time** |
| Median of per-start warm p95 | 27.20 ms | 26.86 ms | 1.3% more time |
| Median of per-start warm p99 | 29.53 ms | 31.55 ms | 6.4% less time |
| Median peak container memory | 79.58 MiB | **55.33 MiB** | +24.25 MiB / +43.8% |
| Median end-of-run container memory | 76.33 MiB | **51.78 MiB** | +24.55 MiB / +47.4% |
| Native executable | 191.83 MiB | **143.31 MiB** | +48.52 MiB / +33.9% |
| Complete container image | 421.17 MiB | **353.04 MiB** | +68.13 MiB / +19.3% |

The startup median lead repeats in both batches:

| Batch | Initial order | GuicedEE business completion | Quarkus business completion |
|---|---|---:|---:|
| [231729](results/20261114-231729/summary.json) | GuicedEE, Quarkus | 667 ms | 705 ms |
| [231959](results/20261114-231959/summary.json) | Quarkus, GuicedEE | 679 ms | 707 ms |

Full-business startup ranges are **585–1,025 ms** for GuicedEE and **671–1,024 ms** for
Quarkus. The first process in each batch took approximately 1.025 seconds, whichever
framework ran first. This is consistent with shared fixture first-use cost, but these
measurements do not isolate its cause. The outliers were not removed. The result is a
repeatable median advantage in this fixture, not a guarantee for every fresh start.

Evidence: [combined statistics](results/standard-quarkus-native-comparison.json),
[first batch environment and immutable inputs](results/20261114-231729/environment.json),
[reverse-order environment](results/20261114-231959/environment.json), and
[source/resource-limit validation](results/standard-quarkus-validation.json).

## What is being compared

The new [quarkus-standard Maven project](quarkus-standard/pom.xml) imports the Quarkus BOM
directly and compiles the exact shared business sources plus the existing Quarkus adapter.
It uses upstream commercetools 20.4.0 and Firebase Admin 9.12.0, Quarkus 3.40.1 extensions,
and published Quarkiverse Firebase/Firestore extensions 2.25.1. It has no GuicedEE parent,
BOM, SDK wrappers, relocated metadata or custom substitution classes. Its resolved Maven
graph contains no `com.guicedee` artifacts. No module descriptor is removed or excluded.

Working integration required Jackson annotations alignment, the legacy Activation API used
by AsyncHttpClient, runtime initialization of that client, and targeted native reflection/
resource/SPI metadata. The metadata comes from a passing trace of the upstream-dependency
JVM and the upstream JARs' service declarations. Every requirement and its observed failure
is documented in [the project README](quarkus-standard/README.md). These are application
compatibility settings; Quarkus framework sources are not patched. Vert.x pool sizing and
Quarkus native service-loader defaults remain at their normal values.

The native build checks the traced SDK dependency hashes before accepting the image.
Image provenance includes source contents/hashes and resolved Maven dependencies. Both
images have identical shared business source hashes; their SDK JAR hashes deliberately
differ. The summary identifies this as `independent-upstream-vs-wrapped` rather than an
identical-dependency experiment. Differences therefore include packaging, transitive
dependency resolution and integration choices, as expected when comparing the applications
as they run.

The earlier [native optimization report](NATIVE_OPTIMIZATION.md) remains a separate,
controlled comparison where **both frameworks used GuicedEE's repackaged SDKs**. Its
659 ms / 655 ms result must not be relabeled as normal upstream-dependency Quarkus.

## Measurement and validation

Both executables use Mandrel 25.0.5, the same Oracle Linux base, default O2 / Serial GC /
x86-64-v3 native compilation, and **250m CPU / 500 MiB** runtime limits without additional
swap. Both receive `-Xms128m -Xmx384m -XX:ActiveProcessorCount=2`. Build work and diagnostic
instrumentation are outside the measured batches. Memory is cgroup container usage,
including its accounted cache; it is not Java heap usage or process RSS. Container sizes
are Docker's local image sizes, not compressed registry transfer sizes.

The first business timer waits for the complete HTTP response after commercetools SDK
OAuth, REST and GraphQL, followed by Firebase Admin SDK Firestore write/read. It does not
stop at port availability or reactive subscription. The gate also checks validation/error
responses, asynchronous retry/timeout behavior, metric increments, OpenAPI, and Swagger's
JavaScript/CSS assets. Warm requests include Firestore and are sequential; these numbers
are not a concurrency or maximum-throughput test.

The final JVM package also passed all 15 capabilities in a separate
[instrumented validation](results/20261114-231541/summary.json). The harness has **17 passing
tests**. Failed integration attempts and diagnostic runs are retained under `results/`
and excluded from rankings. The original production-service template remains unavailable;
this fixture uses a local vendor endpoint and the official Firestore emulator, so it does
not establish production WAN/TLS performance or coverage of every SDK operation.

The measured images are:

- GuicedEE: `sha256:79b8987c62a9eee01a6592332310c714031d75c986a98319a5f77ae9dcdb0868`
- Quarkus standard: `sha256:32153f649fea73fc6143645f48a1c3969851a318903d308a32a7b3876869ec69`

## Reproduce

```powershell
./benchmarks/docker/build-quarkus-standard.ps1 -Native
python benchmarks/tools/compare.py --docker --firebase --runtime native --discovery spi --quarkus-dependencies standard --runs 7 --requests 30 --warmup 10
python benchmarks/tools/compare.py --docker --firebase --runtime native --discovery spi --quarkus-dependencies standard --reverse-initial-order --runs 7 --requests 30 --warmup 10
python benchmarks/tools/summarize_native.py benchmarks/results/<first-batch> benchmarks/results/<second-batch> --output benchmarks/results/standard-quarkus-native-comparison.json
```

Use the recorded GuicedEE image for this exact comparison. Rebuilding GuicedEE from later
workspace artifacts creates a new baseline and requires remeasuring both applications.
