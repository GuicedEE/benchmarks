# Current performance state

**Report: 15 November 2026.** All tables are generated from the latest retained samples.
The complete default/C1 matrices were rerun together for this report; diagnostic and local
profiles have their own recorded batch identities.

<!-- BEGIN GENERATED: headline -->
GuicedEE native completes the first full business request in **657 ms**, versus **684 ms** for Quarkus native (**4.0% less time**). Warm p50 is **5.29 / 5.53 ms** (GuicedEE / Quarkus). Peak charged memory is **79.78 / 55.25 MiB**; executables are **191.83 / 143.31 MiB**. The native sample contains **28 starts and 420 passing capability checks**.
<!-- END GENERATED: headline -->

GuicedEE native has the lower median full-business startup and warm p50 in the current
comparison against normal-dependency Quarkus native. Quarkus has the smaller executable,
container image and peak container memory. The JVM matrix shows a different tradeoff:
Quarkus fast-JAR reaches HTTP readiness sooner, while application-linked GuicedEE completes
the cold SDK/Firestore business request sooner than Quarkus JVM.

## Build performance

<!-- BEGIN GENERATED: build-headline -->
**Clean JVM build:** GuicedEE SPI compiles in **3.01 s** versus **3.65 s** for Quarkus (**17.5% less time**). Complete runnable JVM packaging takes **3.69 / 6.17 s** (GuicedEE / Quarkus), **40.2% less time**. Medians of 3 clean, offline builds per task; dependency preparation is excluded.

**jlink versus native build:** GuicedEE SPI/scanner jlink packages in **17.82 / 17.70 s**, versus **66.44 s** for Quarkus native (**73.2% less time / 73.4% less time**).
<!-- END GENERATED: build-headline -->

<!-- BEGIN GENERATED: build-grid -->
| Artifact | Clean compile (s) | Compile min–max (s) | Complete package (s) | Package min–max (s) | Build baseline | Package difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3.01 | 2.93–3.05 | 3.69 | 3.65–3.74 | Quarkus fast-JAR | -40.2% |
| GuicedEE scanner / full JDK | 3.05 | 3.02–3.10 | 3.64 | 3.57–3.68 | Quarkus fast-JAR | -41.1% |
| Quarkus upstream SDKs / fast-JAR | 3.65 | 3.57–4.17 | 6.17 | 6.16–6.55 | Quarkus fast-JAR | Baseline |
| GuicedEE SPI / application jlink | — | — | 17.82 | 17.46–17.91 | Quarkus native | -73.2% |
| GuicedEE scanner / application jlink | — | — | 17.70 | 17.45–17.71 | Quarkus native | -73.4% |
| GuicedEE SPI / native | — | — | 82.36 | 80.96–85.08 | Quarkus native | +24.0% |
| Quarkus upstream SDKs / native | — | — | 66.44 | 66.34–69.67 | Quarkus native | Baseline |
<!-- END GENERATED: build-grid -->

![Clean compilation and complete packaging](docs/builds.svg)

**Timing boundary:** wall time from launching a new Maven process to its successful exit.
`clean compile` measures the complete source-to-classes lifecycle, including Maven setup and
dependency resolution from disk. `clean package` measures a separate complete build from
clean outputs. The columns overlap; do not add them. JVM packaging includes dependency
copying for GuicedEE and fast-JAR augmentation for Quarkus. Linked packaging creates and
archives the application runtime. Native packaging includes Java compilation, framework
preparation and the native compiler. These are build lifecycle timings, not isolated javac
CPU time, hot-reload latency or an incremental edit benchmark.

**Controlled inputs:** three repetitions per task, sequential rotated order, one untimed
successful package build per artifact to prepare dependencies. Every measured Maven
invocation is offline and cleans outputs; tests are skipped equally. All seven artifacts
use Maven 4.0.0-rc-7 and Mandrel JDK 25.0.5 in the same Linux container, with 32 logical CPUs
and approximately 31 GiB exposed by Docker, without the runtime benchmark's CPU/memory
limits. Both native compilers use an 8 GiB Java heap. Image construction, artifact downloads,
SDK wrapper builds, metadata tracing and emulator preparation are excluded. The application
build consumes framework/vendor artifacts, as a developer build would.

Quarkus uses its normal upstream dependencies and extensions. GuicedEE uses the prepared
framework artifacts with the hashes and artifact version recorded in
[build evidence](results/latest/builds.json). Source hashes, exact commands, Maven/JDK
versions, every elapsed sample and compiler completion evidence are retained there. The
dependency-cache inventory includes plugins and cached JARs; it is not a runtime module graph.
Build measurements form a separate cohort from the immutable images in the runtime grids.
The report verifies that the shared workload source hashes in those Docker images match
the build cohort before it renders the combined comparison.

**Package differences:** negative means less time for GuicedEE. **jlink and native rows use
Quarkus native as the build-time baseline**; full-JDK JVM rows use Quarkus fast-JAR. The chart
compares both jlink modes with both native builds. These are deployment build alternatives:
jlink includes a JVM runtime, while native compilation produces an ahead-of-time executable.
The runtime percentage grids retain their separately labelled JVM and native baselines.
Compilation for packaging-only projects is included in their total package time; a dash
indicates there is no separate compile-only measurement for that project.

### Build cost and resulting execution mode

<!-- BEGIN GENERATED: build-runtime -->
| Artifact | Complete package (s) | Full-business startup (s) | Warm p50 (ms) |
| --- | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3.69 | 27.917 | 90.38 |
| GuicedEE scanner / full JDK | 3.64 | 29.629 | 91.80 |
| Quarkus upstream SDKs / fast-JAR | 6.17 | 23.879 | 87.05 |
| GuicedEE SPI / application jlink | 17.82 | 13.401 | 91.77 |
| GuicedEE scanner / application jlink | 17.70 | 13.704 | 90.26 |
| GuicedEE SPI / native | 82.36 | 0.657 | 5.29 |
| Quarkus upstream SDKs / native | 66.44 | 0.684 | 5.53 |
<!-- END GENERATED: build-runtime -->

<!-- BEGIN GENERATED: build-findings -->
GuicedEE's JVM package requires **40.2% less time** than Quarkus fast-JAR.

**jlink versus native:** SPI/scanner jlink take **17.82 / 17.70 s**. Against Quarkus native's **66.44 s**, that is **73.2% less time / 73.4% less time**; against GuicedEE native's **82.36 s**, it is **78.4% less time / 78.5% less time**.

The complete GuicedEE native build takes **82.36 s** versus **66.44 s**, or **24.0% more time**. jlink produces a bundled JVM runtime; native builds produce ahead-of-time executables. The runtime grid shows the startup and request-latency tradeoffs for each artifact.
<!-- END GENERATED: build-findings -->

Runtime columns use the default-JVM cohort and the larger native-only cohort, each under
250m CPU / 500 MiB. This table connects artifact choices to the measured runtime behavior;
builds and runtime samples are not paired observations. C1 changes launch flags, not the
artifact build, so its startup improvements do not incur a separate compilation cost.
The [C1 grid](#jvm-c1) retains its own runtime results.

## All execution modes

Values are median launch to completed business response in seconds. The default and C1
matrices measure the same seven immutable images. The primary native-only comparison has
a larger counterbalanced sample. Full grids retain every start and measured request.

<!-- BEGIN GENERATED: overview -->
| Application | Full JDK default (s) | Full JDK C1 (s) | Application jlink default (s) | Application jlink C1 (s) | Native (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI | [27.917](RESULTS.md#jvm-default) | [17.191](RESULTS.md#jvm-c1) | [13.401](RESULTS.md#jvm-default) | [7.637](RESULTS.md#jvm-c1) | [0.657](RESULTS.md#native-standard) |
| GuicedEE scanner | [29.629](RESULTS.md#jvm-default) | [17.641](RESULTS.md#jvm-c1) | [13.704](RESULTS.md#jvm-default) | [7.817](RESULTS.md#jvm-c1) | SPI only |
| Quarkus / upstream SDKs | [23.879](RESULTS.md#jvm-default) | [14.015](RESULTS.md#jvm-c1) | Not implemented | Not implemented | [0.684](RESULTS.md#native-standard) |
<!-- END GENERATED: overview -->

![Startup by execution mode](docs/startup.svg)

Read the [native comparison](#native-standard), [default JVM matrix](#jvm-default),
[C1 matrix](#jvm-c1), [percentage differences](#relative-differences),
[local profile](#local-windows), [packaging](#packaging), and [phase diagnostics](#phase-diagnostics).

## Measurement contract

| Measurement | Boundary and interpretation |
|---|---|
| HTTP ready | External launch through an HTTP 200 with exactly `{"ready":true}` from `/ready`; fixed response, not dependency health. Polled every 50 ms. |
| First request | Client elapsed time for the first complete `POST /quote?persist=true` response, including JSON parsing. |
| Full business | External launch through that complete, validated business response. Includes commercetools OAuth/REST/GraphQL and Firestore write/read completion. |
| First OpenAPI | First documentation fetch after business and earlier capability checks; not a documentation-first startup test. |
| Warm p50/p95/p99 | Median of each start's recorded percentile after explicit warmup; one outstanding request. Not pooled percentiles, concurrency or throughput. |
| Peak/end memory | Cgroup `memory.peak` / `memory.current` at the end of the run; whole-container charged memory including cache, not RSS or heap. |
| Docker image size | Recorded daemon-local image-store accounting; includes shared layers and, on this containerd store, compressed content and unpacked snapshots. Not registry transfer size. |

Docker groups use **0.25 CPU, 500 MiB memory and no additional swap**. Every process receives
`-Xms128m -Xmx384m -XX:ActiveProcessorCount=2`. C1 adds `-XX:TieredStopAtLevel=1` to every JVM
in that group; native executables receive no JIT flag. JVM images use Oracle JDK 25;
native uses Mandrel 25.0.5, O2, Serial GC and x86-64-v3, without PGO or UPX.

Timing begins before `docker run`, so local container creation is included. Building and
pulling images is excluded. Fixtures and the Firestore emulator are already running outside
the application quota. Host page caches are not flushed. All starts and outliers are kept;
launch order rotates/reverses. Independently calculated medians need not add up.

Only complete eligible, uninstrumented batches enter performance tables. Full-body business
validation, all 15 capability checks and all measured requests must pass. Failed executions remain in local run output and cannot enter the published comparison. All image identities appear in the [identity grid](#image-identities).

<a id="native-standard"></a>
## Native: normal Quarkus dependencies

This is the primary application comparison: GuicedEE SPI native versus Quarkus with upstream
commercetools 20.4.0, Firebase Admin 9.12.0, Quarkus 3.40.1 and Quarkiverse Firebase/Firestore
2.25.1. Quarkus has no GuicedEE SDK wrappers or framework patches. Native compatibility
metadata and application configuration are described in [the project](quarkus-standard/README.md).
Business sources match; dependency packaging and transitive graphs deliberately differ.

The two batches reverse their initial framework order and use identical image IDs and flags.

<!-- BEGIN GENERATED: native-standard -->
Displayed rows: **28 starts / 420 passing checks / 840 successful measured requests**. Each start: 10 warmups, 30 measured requests. Batch IDs in [latest measurements](results/latest/measurements.json): `20261115-005208`, `20261115-005244`.

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | 14 | 0.575 | 82.52 | 0.657 | 0.615–1.053 | 3.48 |
| Quarkus upstream SDKs / native | 14 | 0.577 | 99.45 | 0.684 | 0.644–0.976 | 2.25 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | 5.29 | 21.96 | 27.52 | 79.78 | 79.17–80.46 | 76.35 |
| Quarkus upstream SDKs / native | 5.53 | 24.57 | 28.50 | 55.25 | 54.21–56.20 | 51.87 |
<!-- END GENERATED: native-standard -->

<!-- BEGIN GENERATED: native-deltas -->
| Metric | GuicedEE native | Quarkus upstream native | GuicedEE difference |
| --- | ---: | ---: | ---: |
| Full-business startup | 656.93 ms | 684.24 ms | -4.0% |
| First business request | 82.52 ms | 99.45 ms | -17.0% |
| Warm p50 | 5.29 ms | 5.53 ms | -4.3% |
| Warm p95 | 21.96 ms | 24.57 ms | -10.6% |
| Warm p99 | 27.52 ms | 28.50 ms | -3.4% |
| Peak container memory | 79.78 MiB | 55.25 MiB | +44.4% |
| Executable size | 191.83 MiB | 143.31 MiB | +33.9% |
| Docker local image size | 421.17 MiB | 353.04 MiB | +19.3% |
<!-- END GENERATED: native-deltas -->

Negative differences mean GuicedEE uses less time or space. Readiness polling is 50 ms,
so small readiness differences are not precise internal startup measurements. Warm p95/p99
are medians of per-start percentiles; these sequential samples do not establish sustained
throughput. First-use outliers remain included. The [native grid](#native-standard) makes
the startup/latency and memory/size tradeoff explicit.

<a id="jvm-default"></a>
<a id="current-linux-native-comparison"></a>
## Full matched matrix: default JVMs

The full-JDK, application-jlink and native modes use **normal-dependency Quarkus** as the
baseline. Every image passes the same business and capability checks. The native rows
show the alternative compilation strategy within this matched batch.

<!-- BEGIN GENERATED: jvm-default -->
Displayed rows: **21 starts / 315 passing checks / 630 successful measured requests**. Each start: 10 warmups, 30 measured requests. Batch IDs in [latest measurements](results/latest/measurements.json): `20261115-013229`.

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3 | 8.813 | 19,888.51 | 27.917 | 27.635–29.691 | 103.25 |
| GuicedEE scanner / full JDK | 3 | 9.433 | 19,998.81 | 29.629 | 27.529–29.693 | 192.07 |
| Quarkus upstream SDKs / fast-JAR | 3 | 6.976 | 17,399.01 | 23.879 | 23.291–29.578 | 402.47 |
| GuicedEE SPI / application jlink | 3 | 7.522 | 5,895.65 | 13.401 | 13.265–13.418 | 201.03 |
| GuicedEE scanner / application jlink | 3 | 8.421 | 5,905.60 | 13.704 | 13.619–14.884 | 188.24 |
| GuicedEE SPI / native | 3 | 0.569 | 77.18 | 0.646 | 0.640–0.676 | 3.77 |
| Quarkus upstream SDKs / native | 3 | 0.573 | 111.58 | 0.684 | 0.652–0.692 | 2.24 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 90.38 | 99.78 | 99.81 | 299.19 | 297.66–375.25 | 295.54 |
| GuicedEE scanner / full JDK | 91.80 | 98.99 | 101.63 | 301.50 | 295.85–378.55 | 297.91 |
| Quarkus upstream SDKs / fast-JAR | 87.05 | 95.07 | 95.81 | 278.15 | 271.43–343.71 | 275.08 |
| GuicedEE SPI / application jlink | 91.77 | 100.55 | 105.26 | 238.98 | 236.05–251.63 | 235.26 |
| GuicedEE scanner / application jlink | 90.26 | 100.94 | 105.18 | 243.87 | 226.45–244.71 | 240.23 |
| GuicedEE SPI / native | 5.16 | 30.79 | 33.25 | 80.02 | 79.60–80.29 | 76.48 |
| Quarkus upstream SDKs / native | 4.99 | 21.69 | 28.38 | 54.84 | 54.68–55.00 | 51.66 |
<!-- END GENERATED: jvm-default -->

<a id="jvm-c1"></a>
## Full matched matrix: equal C1 JVM tuning

These are the **same immutable images** as the default matrix, with C1 applied equally to
all JVMs. Quarkus native is repeated as a batch reference using the same binary and no JIT flag.

<!-- BEGIN GENERATED: jvm-c1 -->
Displayed rows: **21 starts / 315 passing checks / 630 successful measured requests**. Each start: 10 warmups, 30 measured requests. Batch IDs in [latest measurements](results/latest/measurements.json): `20261115-013945`.

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3 | 5.188 | 11,999.36 | 17.191 | 16.877–17.247 | 93.17 |
| GuicedEE scanner / full JDK | 3 | 5.182 | 12,469.69 | 17.641 | 17.170–17.652 | 24.24 |
| Quarkus upstream SDKs / fast-JAR | 3 | 3.911 | 10,104.45 | 14.015 | 13.998–14.107 | 296.29 |
| GuicedEE SPI / application jlink | 3 | 4.615 | 3,012.92 | 7.637 | 7.619–7.785 | 12.14 |
| GuicedEE scanner / application jlink | 3 | 4.816 | 3,010.97 | 7.817 | 7.773–8.133 | 12.49 |
| GuicedEE SPI / native | 3 | 0.578 | 76.05 | 0.654 | 0.650–0.667 | 3.58 |
| Quarkus upstream SDKs / native | 3 | 0.574 | 106.35 | 0.680 | 0.677–0.680 | 2.11 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 27.99 | 92.01 | 92.86 | 262.93 | 261.50–263.19 | 259.43 |
| GuicedEE scanner / full JDK | 49.37 | 89.57 | 90.25 | 264.04 | 263.40–265.50 | 260.32 |
| Quarkus upstream SDKs / fast-JAR | 21.03 | 88.86 | 92.33 | 241.41 | 240.93–241.52 | 237.46 |
| GuicedEE SPI / application jlink | 20.34 | 89.93 | 91.59 | 189.09 | 188.84–189.77 | 185.98 |
| GuicedEE scanner / application jlink | 30.96 | 90.15 | 90.61 | 191.24 | 190.65–191.29 | 187.38 |
| GuicedEE SPI / native | 4.87 | 24.90 | 29.46 | 79.43 | 79.31–79.48 | 76.01 |
| Quarkus upstream SDKs / native | 5.44 | 28.62 | 31.69 | 54.89 | 54.89–55.40 | 51.77 |
<!-- END GENERATED: jvm-c1 -->

<a id="relative-differences"></a>
## Percentage differences against Quarkus

Each row compares GuicedEE with Quarkus in the **same batch and tuning profile**. JVM and
jlink rows use Quarkus fast-JAR as their JVM baseline; native uses Quarkus native. Negative
values mean less time or memory, positive values mean more. No cross-profile ranking is
implied. The byte sizes are compared separately below.

<!-- BEGIN GENERATED: relative -->
| Profile | GuicedEE mode | Quarkus baseline | Ready | Full business | Warm p50 | Warm p95 | Peak memory |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| jvm-default | GuicedEE SPI / full JDK | JVM | +26.3% | +16.9% | +3.8% | +4.9% | +7.6% |
| jvm-default | GuicedEE scanner / full JDK | JVM | +35.2% | +24.1% | +5.5% | +4.1% | +8.4% |
| jvm-default | GuicedEE SPI / application jlink | JVM | +7.8% | -43.9% | +5.4% | +5.8% | -14.1% |
| jvm-default | GuicedEE scanner / application jlink | JVM | +20.7% | -42.6% | +3.7% | +6.2% | -12.3% |
| jvm-default | GuicedEE SPI / native | Native | -0.7% | -5.6% | +3.6% | +41.9% | +45.9% |
| jvm-c1 | GuicedEE SPI / full JDK | JVM | +32.7% | +22.7% | +33.1% | +3.5% | +8.9% |
| jvm-c1 | GuicedEE scanner / full JDK | JVM | +32.5% | +25.9% | +134.7% | +0.8% | +9.4% |
| jvm-c1 | GuicedEE SPI / application jlink | JVM | +18.0% | -45.5% | -3.3% | +1.2% | -21.7% |
| jvm-c1 | GuicedEE scanner / application jlink | JVM | +23.2% | -44.2% | +47.2% | +1.5% | -20.8% |
| jvm-c1 | GuicedEE SPI / native | Native | +0.7% | -3.9% | -10.4% | -13.0% | +44.7% |
<!-- END GENERATED: relative -->

<!-- BEGIN GENERATED: findings -->
**Default JVM:** linked SPI/scanner complete the first business response in **13.401/13.704 s**, versus **23.879 s** for Quarkus JVM. SPI jlink uses **43.9% less time**. The separate readiness and first-request columns show where that difference occurs.

**C1 JVM:** linked SPI/scanner complete the first business response in **7.637/7.817 s**, versus **14.015 s** for Quarkus JVM. SPI jlink uses **45.5% less time**. The separate readiness and first-request columns show where that difference occurs.
<!-- END GENERATED: findings -->

<a id="local-windows"></a>
## Local Windows profile

These are unrestricted-host, default-tiered JVM runs of the four GuicedEE modes. There is
**no 250m CPU quota, no 500 MiB container limit and no Quarkus row**. They establish the
local mode timings and functional coverage only; they cannot rank against Docker results.
Container memory, image size and OpenAPI request timing were not recorded in this batch.

<!-- BEGIN GENERATED: local-windows -->
Displayed rows: **12 starts / 180 passing checks / 1200 successful measured requests**. Each start: 20 warmups, 100 measured requests. Batch IDs in [latest measurements](results/latest/measurements.json): `20261114-124721`.

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3 | 1.241 | 2,797.84 | 4.038 | 3.902–4.145 | — |
| GuicedEE scanner / full JDK | 3 | 1.257 | 2,621.88 | 3.879 | 3.789–3.901 | — |
| GuicedEE SPI / application jlink | 3 | 1.244 | 645.18 | 1.919 | 1.887–2.042 | — |
| GuicedEE scanner / application jlink | 3 | 1.260 | 606.93 | 1.871 | 1.847–1.892 | — |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 7.13 | 31.54 | 32.39 | — | — | — |
| GuicedEE scanner / full JDK | 11.57 | 31.62 | 34.01 | — | — | — |
| GuicedEE SPI / application jlink | 7.18 | 31.34 | 32.86 | — | — | — |
| GuicedEE scanner / application jlink | 7.43 | 31.48 | 32.39 | — | — | — |
<!-- END GENERATED: local-windows -->

<a id="packaging"></a>
## Packaging and module footprint

Image sizes below cover each measured binary once. Runtime memory is in the performance
grids above; it is not the same quantity as disk size.

<!-- BEGIN GENERATED: packaging -->
| Variant | Evidence group | Docker local image (MiB) | Executable (MiB) | Image ID prefix |
| --- | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | native-standard | 421.17 | 191.83 | `79b8987c62a9` |
| Quarkus upstream SDKs / native | native-standard | 353.04 | 143.31 | `32153f649fea` |
| GuicedEE SPI / full JDK | jvm-default | 1,005.17 | — | `fad5ba9c3150` |
| GuicedEE scanner / full JDK | jvm-default | 1,005.17 | — | `a9817e6465b0` |
| Quarkus upstream SDKs / fast-JAR | jvm-default | 976.77 | — | `ff1c796950c8` |
| GuicedEE SPI / application jlink | jvm-default | 473.29 | — | `867a886a5d8c` |
| GuicedEE scanner / application jlink | jvm-default | 473.43 | — | `b8ea0ab4aef0` |
<!-- END GENERATED: packaging -->

The linked-runtime audit applies specifically to the images in the full JVM matrix:

<!-- BEGIN GENERATED: jlink-size -->
| Measured jlink payload | SPI | Scanner |
| --- | ---: | ---: |
| Runtime including application (MiB) | 168.85 | 168.91 |
| Module image (MiB) | 135.18 | 135.25 |
| Unpacked Docker layers (MiB) | 286.21 | 286.29 |
| Installed modules | 107 | 107 |
| Mandatory module closure | 96 | 96 |
| Closure including installed service providers | 101 | 101 |
<!-- END GENERATED: jlink-size -->

The roughly 473 MiB Docker-store value contains a **169 MiB linked application runtime**.
The graph is valid but not minimal: 107 installed modules versus 96 in the mandatory closure
and 101 when resolving providers already present. The current dataset retains the application roots, installed module names and both closure
sets. Linking includes whole modules and their resources; successful linking does not prove
that every class is exercised by the workload. Closure differences are investigation targets,
not demonstrated savings from deleting those modules.

<a id="phase-diagnostics"></a>
## Startup and reactive-flow phase diagnostics

These instrumented runs explain where time is spent. **They are excluded from the ranked
performance grids.** The columns below come from separate image revisions/batches; the
normal-dependency Quarkus columns each have only one diagnostic start. They provide coverage
and hypotheses, not a matched phase-level framework ranking. Missing phases mean unmeasured,
not zero cost.

<!-- BEGIN GENERATED: phase-sources -->
| Diagnostic variant | Starts | Evidence | Image ID prefix |
| --- | ---: | ---: | ---: |
| SPI jlink | 3 | `20261114-200341` | `867a886a5d8c` |
| Scanner jlink | 3 | `20261114-200341` | `b8ea0ab4aef0` |
| Quarkus wrapped JVM | 3 | `20261114-192928` | `8bb83742f618` |
| Quarkus upstream JVM | 1 | `20261114-231541` | `ff1c796950c8` |
| GuicedEE native | 2 | `20261114-221910` | `1fa99f53daf7` |
| Quarkus upstream native | 1 | `20261114-231325` | `a7c4d1a26a04` |
<!-- END GENERATED: phase-sources -->

### Framework startup phases

<!-- BEGIN GENERATED: phase-startup -->
| Inclusive phase (ms) | SPI jlink | Scanner jlink | GuicedEE native |
| --- | ---: | ---: | ---: |
| Context discovery | 496.72 | 411.25 | 4.97 |
| Discovery | 0.26 | 502.53 | 0.00 |
| ClassGraph scan | — | 401.43 | — |
| Pre-startup hooks | 997.53 | 903.05 | 7.59 |
| Guice module discovery | 404.72 | 407.62 | 0.94 |
| Guice injector creation | 1,700.55 | 1,689.56 | 17.06 |
| OpenAPI provider (within injector) | 1,000.15 | 902.24 | 5.22 |
| Post-startup hooks | 898.54 | 1,004.52 | 90.52 |
<!-- END GENERATED: phase-startup -->

Phases are inclusive wall time, with nested work, class loading, CPU throttling and scheduling.
Do not add columns or subtract internal timings from external startup timers. Quarkus internal
framework startup has no equivalent capture in this harness.

In the linked captures, SPI performs no ClassGraph scan. Scanner mode accepts **three classes
and seven resources**, all in `bench.guicedee.scan`. Both report **35 startup Guice bindings**,
19 explicit and 16 created on demand. SDK internals and lazy bindings are not represented by
that startup snapshot. The native startup capture predates the final static-asset serving
revision and is an injector diagnostic, not the exact headline native image.

### First-use business phases

<!-- BEGIN GENERATED: sdk-headline -->
**Commercetools first-use initialization:** GuicedEE SPI jlink records **1.287 s** versus **16.611 s** for standard Quarkus JVM: **15.325 s less** (**92.3% less time**). These are instrumented phase diagnostics (3 GuicedEE starts, 1 Quarkus start), separate from build time and the uninstrumented runtime rankings. The samples identify a first-use cost; they do not establish its cause or a general SDK performance ratio.
<!-- END GENERATED: sdk-headline -->

<!-- BEGIN GENERATED: phase-workload -->
| Inclusive phase (ms) | SPI jlink | Scanner jlink | Quarkus wrapped JVM | Quarkus upstream JVM | GuicedEE native | Quarkus upstream native |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| JDK HTTP client construction | 703.42 | 598.29 | 698.32 | 1,198.45 | 0.38 | 0.63 |
| Commercetools client initialization | 1,286.55 | 910.69 | 14,299.59 | 16,611.47 | 37.94 | 43.50 |
| Commercetools REST + first OAuth | 1,405.65 | 1,391.94 | 1,595.76 | 2,794.86 | 9.93 | 10.81 |
| GraphQL completion | 197.45 | 206.46 | 209.48 | 505.95 | 1.85 | 2.08 |
| Firestore client initialization | 1,788.71 | 1,599.24 | 1,501.74 | 1,485.40 | 5.24 | 26.11 |
| Firestore write completion | 1,196.63 | 1,292.22 | 1,406.62 | 1,215.70 | 192.51 | 310.84 |
| Firestore read completion | 7.58 | 7.23 | 8.41 | 13.73 | 6.08 | 7.46 |
<!-- END GENERATED: phase-workload -->

The commercetools initialization phase is distinct from the first REST/OAuth request. The
wrapped-Quarkus JVM diagnostic records **14.300 seconds** in that initialization step.
The single upstream-dependency JVM capture records **16.611 seconds**, while its native
capture records **43.50 ms**. These point to cold SDK initialization as a useful JVM profiling
target, but one instrumented start cannot establish a comparative median. The data locates
cost but does not isolate class loading, JIT compilation or another initializer as its cause.

SDK spans wait for completion of the asynchronous operations. The shared Firestore adapter
currently waits on SDK futures inside `CompletableFuture.supplyAsync`; both applications
wait for it, so the work is timed, although that adapter is not fully nonblocking. The HTTP
client construction phase sums repeated constructions within each start before taking its
median. Quarkus CDI proxy/subclass construction can initialize the workload twice; a second
construction is retained in the capture rather than counted as a second business operation.

## Capability and evidence coverage

| Capability | Validated behavior in every eligible performance row |
|---|---|
| REST/JSON | Exact successful quote body, optional primitive query handling, validation response, malformed JSON and unsupported-media status |
| commercetools | Real SDK client credentials, project REST fetch and GraphQL inventory used by the quote; local deterministic server |
| Firestore | Real Firebase Admin SDK write/read through the official emulator, awaited by the first and warm business requests |
| Reactive resilience | Exactly three retry attempts, exhaustion envelope, asynchronous timeout envelope and concurrent readiness observation |
| Metrics | Application quote counter exists and increments after another request |
| OpenAPI/Swagger | Generated `/quote` path and working UI, JavaScript bundle and stylesheet |
| GuicedEE discovery | Requested SPI/scanner mode and both application verticle deployments verified |

The gate has 15 checks per start. Error-envelope parity is explicit for application errors;
framework-generated malformed/media errors are checked for status, not identical bodies.
GraphQL here is an outbound SDK call, not an inbound GraphQL server. Firebase here is
Firestore, not every Firebase product.

The harness provides seven Docker variants. GuicedEE scanner native and Quarkus application
jlink are not implemented. Core JMH, sustained throughput, production WAN/TLS, authentication,
telemetry, Secret Manager and additional SDK products are outside this service workload.

## Reproduce and verify the report

[RUNNING.md](RUNNING.md) documents the applications, flags, build commands, fixtures and
configuration. Rebuilds with different framework/SDK inputs require new measurements; the
Maven caches and executable images are generated build outputs.

From the benchmark repository root:

```powershell
python tools/render_performance.py --check
python tools/verify_latest.py
python -m unittest discover -s tools -p test_harness.py
```

The renderer validates complete variant/start matrices, capability/sample success, container
quotas and image identities before calculating tables. It reads every start of each selected
variant from [the latest measurement set](results/latest/measurements.json). Publish new batches
with `tools/publish_results.py`, then refresh the report and review its analysis. Raw new-run
output remains under ignored `target/runs`; only the current public dataset is committed.

[JSON statistics and input hashes](docs/current-performance.json) and [CSV](docs/current-performance.csv)
provide unrounded values. The dataset preserves original batch IDs, actual image/artifact
identities and diagnostic scope without duplicating source files or earlier reports.

<a id="image-identities"></a>
## Immutable image identities

The latest dataset records image IDs, input hashes and runtime flags for every group.
The same image can legitimately appear in more than one profile or dependency experiment.

<!-- BEGIN GENERATED: image-identities -->
| Group | Variant | Immutable Docker image ID |
| --- | ---: | ---: |
| native-standard | GuicedEE SPI / native | `sha256:79b8987c62a9eee01a6592332310c714031d75c986a98319a5f77ae9dcdb0868` |
| native-standard | Quarkus upstream SDKs / native | `sha256:32153f649fea73fc6143645f48a1c3969851a318903d308a32a7b3876869ec69` |
| jvm-default | GuicedEE SPI / full JDK | `sha256:fad5ba9c31502a0d22bc8a2ddb31c8de9d7d49b05e773eb40de43a5ff9ee4cfb` |
| jvm-default | GuicedEE scanner / full JDK | `sha256:a9817e6465b054e8d2419cc03883ce6b81f4ec1bbaeedaa3631a0a5ec6a4ec8f` |
| jvm-default | Quarkus upstream SDKs / fast-JAR | `sha256:ff1c796950c84a86c8bc4f833fb17794bf4d4343ab52b98b51ffc0df436d45a8` |
| jvm-default | GuicedEE SPI / application jlink | `sha256:867a886a5d8cf020d5d9320b93d521acf995535480c7f18d259620f031d7f86a` |
| jvm-default | GuicedEE scanner / application jlink | `sha256:b8ea0ab4aef0522b489a9ab6e42a4944a996758f813c5395c4c66af4703df2ac` |
| jvm-default | GuicedEE SPI / native | `sha256:79b8987c62a9eee01a6592332310c714031d75c986a98319a5f77ae9dcdb0868` |
| jvm-default | Quarkus upstream SDKs / native | `sha256:32153f649fea73fc6143645f48a1c3969851a318903d308a32a7b3876869ec69` |
| jvm-c1 | GuicedEE SPI / full JDK | `sha256:fad5ba9c31502a0d22bc8a2ddb31c8de9d7d49b05e773eb40de43a5ff9ee4cfb` |
| jvm-c1 | GuicedEE scanner / full JDK | `sha256:a9817e6465b054e8d2419cc03883ce6b81f4ec1bbaeedaa3631a0a5ec6a4ec8f` |
| jvm-c1 | Quarkus upstream SDKs / fast-JAR | `sha256:ff1c796950c84a86c8bc4f833fb17794bf4d4343ab52b98b51ffc0df436d45a8` |
| jvm-c1 | GuicedEE SPI / application jlink | `sha256:867a886a5d8cf020d5d9320b93d521acf995535480c7f18d259620f031d7f86a` |
| jvm-c1 | GuicedEE scanner / application jlink | `sha256:b8ea0ab4aef0522b489a9ab6e42a4944a996758f813c5395c4c66af4703df2ac` |
| jvm-c1 | GuicedEE SPI / native | `sha256:79b8987c62a9eee01a6592332310c714031d75c986a98319a5f77ae9dcdb0868` |
| jvm-c1 | Quarkus upstream SDKs / native | `sha256:32153f649fea73fc6143645f48a1c3969851a318903d308a32a7b3876869ec69` |
<!-- END GENERATED: image-identities -->
