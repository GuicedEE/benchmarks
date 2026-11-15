# Current performance state

**Report: 15 November 2026.** All tables are generated from the latest retained samples.
The complete default/C1 matrices were rerun together for this report; diagnostic and local
profiles have their own recorded batch identities.

<!-- BEGIN GENERATED: host-condition -->
All timing profiles were rerun after the host boot at **2026-11-15T00:45:50.5000000Z**. Across 6 retained one-second preflight/local-start samples, host CPU utilization ranged **2.5–6.9%**, available physical memory **31.5–36.3 GiB**. The recovered build-stage CPU snapshots were **48.9–61.9%** before untimed dependency preparation; the default-runtime stage began at **4.3–6.2%**. Build, runtime and diagnostic stages ran sequentially. Host observations have partial coverage and are boundary snapshots, not continuous measurements of background load during each run. Available observations and their coverage are included in the latest measurement dataset.
<!-- END GENERATED: host-condition -->

<!-- BEGIN GENERATED: headline -->
GuicedEE native completes the first full business request in **655 ms**, versus **695 ms** for Quarkus native (**5.9% less time**). Warm p50 is **5.22 / 5.38 ms** (GuicedEE / Quarkus). Peak charged memory is **80.07 / 55.28 MiB**; executables are **191.83 / 143.31 MiB**. The native sample contains **28 starts and 420 passing capability checks**.
<!-- END GENERATED: headline -->

<!-- BEGIN GENERATED: runtime-findings -->
GuicedEE native records the lower median full-business startup; GuicedEE native records the lower warm p50. Quarkus native has the lower peak container memory. The JVM grids separately report HTTP readiness and completion of the cold SDK/Firestore business request, so both startup costs remain visible.
<!-- END GENERATED: runtime-findings -->

## Build performance

<!-- BEGIN GENERATED: build-headline -->
**Clean JVM build:** GuicedEE SPI compiles in **3.11 s** versus **3.61 s** for Quarkus (**13.8% less time**). Complete runnable JVM packaging takes **3.67 / 6.10 s** (GuicedEE / Quarkus), **39.9% less time**. Medians of 3 clean, offline builds per task; dependency preparation is excluded.

**jlink versus native build:** GuicedEE SPI/scanner jlink packages in **17.35 / 17.28 s**, versus **64.55 s** for Quarkus native (**73.1% less time / 73.2% less time**).
<!-- END GENERATED: build-headline -->

<!-- BEGIN GENERATED: build-grid -->
| Artifact | Clean compile (s) | Compile min–max (s) | Complete package (s) | Package min–max (s) | Build baseline | Package difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3.11 | 3.10–3.23 | 3.67 | 3.64–3.85 | Quarkus fast-JAR | -39.9% |
| GuicedEE scanner / full JDK | 3.06 | 2.99–3.19 | 3.57 | 3.51–3.59 | Quarkus fast-JAR | -41.6% |
| Quarkus upstream SDKs / fast-JAR | 3.61 | 3.52–3.62 | 6.10 | 6.10–6.41 | Quarkus fast-JAR | Baseline |
| GuicedEE SPI / application jlink | — | — | 17.35 | 17.26–17.53 | Quarkus native | -73.1% |
| GuicedEE scanner / application jlink | — | — | 17.28 | 17.10–17.31 | Quarkus native | -73.2% |
| GuicedEE SPI / native | — | — | 75.08 | 74.91–77.17 | Quarkus native | +16.3% |
| Quarkus upstream SDKs / native | — | — | 64.55 | 64.01–65.18 | Quarkus native | Baseline |
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
| GuicedEE SPI / full JDK | 3.67 | 29.351 | 90.66 |
| GuicedEE scanner / full JDK | 3.57 | 28.792 | 93.83 |
| Quarkus upstream SDKs / fast-JAR | 6.10 | 23.553 | 83.33 |
| GuicedEE SPI / application jlink | 17.35 | 12.608 | 87.64 |
| GuicedEE scanner / application jlink | 17.28 | 13.387 | 89.20 |
| GuicedEE SPI / native | 75.08 | 0.655 | 5.22 |
| Quarkus upstream SDKs / native | 64.55 | 0.695 | 5.38 |
<!-- END GENERATED: build-runtime -->

<!-- BEGIN GENERATED: build-findings -->
GuicedEE's JVM package requires **39.9% less time** than Quarkus fast-JAR.

**jlink versus native:** SPI/scanner jlink take **17.35 / 17.28 s**. Against Quarkus native's **64.55 s**, that is **73.1% less time / 73.2% less time**; against GuicedEE native's **75.08 s**, it is **76.9% less time / 77.0% less time**.

The complete GuicedEE native build takes **75.08 s** versus **64.55 s**, or **16.3% more time**. jlink produces a bundled JVM runtime; native builds produce ahead-of-time executables. The runtime grid shows the startup and request-latency tradeoffs for each artifact.
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
| GuicedEE SPI | [29.351](RESULTS.md#jvm-default) | [16.311](RESULTS.md#jvm-c1) | [12.608](RESULTS.md#jvm-default) | [7.519](RESULTS.md#jvm-c1) | [0.655](RESULTS.md#native-standard) |
| GuicedEE scanner | [28.792](RESULTS.md#jvm-default) | [16.789](RESULTS.md#jvm-c1) | [13.387](RESULTS.md#jvm-default) | [8.201](RESULTS.md#jvm-c1) | SPI only |
| Quarkus / upstream SDKs | [23.553](RESULTS.md#jvm-default) | [13.782](RESULTS.md#jvm-c1) | Not implemented | Not implemented | [0.695](RESULTS.md#native-standard) |
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
Displayed rows: **28 starts / 420 passing checks / 840 successful measured requests**. Each start: 10 warmups, 30 measured requests. Batch IDs in [latest measurements](results/latest/measurements.json): `20261115-033613`, `20261115-033655`.

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | 14 | 0.576 | 84.54 | 0.655 | 0.637–0.976 | 3.56 |
| Quarkus upstream SDKs / native | 14 | 0.574 | 119.69 | 0.695 | 0.665–0.992 | 2.13 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | 5.22 | 18.98 | 26.39 | 80.07 | 79.38–80.50 | 76.49 |
| Quarkus upstream SDKs / native | 5.38 | 25.92 | 29.50 | 55.28 | 54.29–56.32 | 51.74 |
<!-- END GENERATED: native-standard -->

<!-- BEGIN GENERATED: native-deltas -->
| Metric | GuicedEE native | Quarkus upstream native | GuicedEE difference |
| --- | ---: | ---: | ---: |
| Full-business startup | 654.54 ms | 695.26 ms | -5.9% |
| First business request | 84.54 ms | 119.69 ms | -29.4% |
| Warm p50 | 5.22 ms | 5.38 ms | -2.9% |
| Warm p95 | 18.98 ms | 25.92 ms | -26.8% |
| Warm p99 | 26.39 ms | 29.50 ms | -10.5% |
| Peak container memory | 80.07 MiB | 55.28 MiB | +44.9% |
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
Displayed rows: **21 starts / 315 passing checks / 630 successful measured requests**. Each start: 10 warmups, 30 measured requests. Batch IDs in [latest measurements](results/latest/measurements.json): `20261115-032428`.

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3 | 9.059 | 19,390.69 | 29.351 | 24.953–32.009 | 193.30 |
| GuicedEE scanner / full JDK | 3 | 9.398 | 19,394.17 | 28.792 | 28.576–29.519 | 190.09 |
| Quarkus upstream SDKs / fast-JAR | 3 | 6.942 | 16,610.62 | 23.553 | 21.374–23.971 | 496.13 |
| GuicedEE SPI / application jlink | 3 | 7.114 | 5,796.62 | 12.608 | 12.508–13.252 | 190.91 |
| GuicedEE scanner / application jlink | 3 | 7.700 | 5,686.10 | 13.387 | 12.491–13.478 | 108.01 |
| GuicedEE SPI / native | 3 | 0.579 | 66.08 | 0.647 | 0.627–0.676 | 3.53 |
| Quarkus upstream SDKs / native | 3 | 0.569 | 100.99 | 0.669 | 0.668–0.688 | 2.80 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 90.66 | 101.61 | 101.98 | 302.32 | 294.36–368.83 | 299.30 |
| GuicedEE scanner / full JDK | 93.83 | 104.22 | 104.61 | 310.34 | 304.23–379.26 | 306.77 |
| Quarkus upstream SDKs / fast-JAR | 83.33 | 95.80 | 96.58 | 275.56 | 274.33–339.51 | 271.88 |
| GuicedEE SPI / application jlink | 87.64 | 97.67 | 98.56 | 237.84 | 215.66–242.05 | 233.03 |
| GuicedEE scanner / application jlink | 89.20 | 97.79 | 98.61 | 238.07 | 223.50–239.67 | 234.95 |
| GuicedEE SPI / native | 6.24 | 24.02 | 27.54 | 80.16 | 80.04–80.38 | 76.85 |
| Quarkus upstream SDKs / native | 5.97 | 8.79 | 28.87 | 55.14 | 54.96–55.25 | 51.62 |
<!-- END GENERATED: jvm-default -->

<a id="jvm-c1"></a>
## Full matched matrix: equal C1 JVM tuning

These are the **same immutable images** as the default matrix, with C1 applied equally to
all JVMs. Quarkus native is repeated as a batch reference using the same binary and no JIT flag.

<!-- BEGIN GENERATED: jvm-c1 -->
Displayed rows: **21 starts / 315 passing checks / 630 successful measured requests**. Each start: 10 warmups, 30 measured requests. Batch IDs in [latest measurements](results/latest/measurements.json): `20261115-033137`.

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3 | 4.810 | 11,500.88 | 16.311 | 16.099–17.895 | 22.78 |
| GuicedEE scanner / full JDK | 3 | 5.199 | 11,589.79 | 16.789 | 16.505–17.328 | 94.19 |
| Quarkus upstream SDKs / fast-JAR | 3 | 3.885 | 9,896.50 | 13.782 | 13.659–14.080 | 288.40 |
| GuicedEE SPI / application jlink | 3 | 4.516 | 3,014.24 | 7.519 | 7.457–7.736 | 92.77 |
| GuicedEE scanner / application jlink | 3 | 4.894 | 3,306.18 | 8.201 | 7.565–8.413 | 11.89 |
| GuicedEE SPI / native | 3 | 0.573 | 66.91 | 0.645 | 0.630–0.653 | 3.21 |
| Quarkus upstream SDKs / native | 3 | 0.572 | 120.21 | 0.698 | 0.692–0.704 | 2.59 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 48.20 | 90.87 | 90.91 | 262.46 | 261.05–263.18 | 259.05 |
| GuicedEE scanner / full JDK | 13.44 | 90.11 | 90.84 | 264.76 | 263.51–265.07 | 261.14 |
| Quarkus upstream SDKs / fast-JAR | 25.30 | 88.89 | 90.35 | 241.37 | 241.30–242.29 | 237.68 |
| GuicedEE SPI / application jlink | 33.04 | 89.67 | 90.37 | 187.75 | 187.21–189.74 | 184.30 |
| GuicedEE scanner / application jlink | 48.95 | 92.30 | 92.35 | 191.48 | 189.76–191.85 | 188.17 |
| GuicedEE SPI / native | 5.75 | 26.08 | 27.00 | 79.81 | 79.41–80.00 | 76.31 |
| Quarkus upstream SDKs / native | 5.39 | 24.49 | 25.36 | 55.74 | 55.38–55.82 | 52.09 |
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
| jvm-default | GuicedEE SPI / full JDK | JVM | +30.5% | +24.6% | +8.8% | +6.1% | +9.7% |
| jvm-default | GuicedEE scanner / full JDK | JVM | +35.4% | +22.2% | +12.6% | +8.8% | +12.6% |
| jvm-default | GuicedEE SPI / application jlink | JVM | +2.5% | -46.5% | +5.2% | +1.9% | -13.7% |
| jvm-default | GuicedEE scanner / application jlink | JVM | +10.9% | -43.2% | +7.0% | +2.1% | -13.6% |
| jvm-default | GuicedEE SPI / native | Native | +1.7% | -3.3% | +4.6% | +173.2% | +45.4% |
| jvm-c1 | GuicedEE SPI / full JDK | JVM | +23.8% | +18.4% | +90.5% | +2.2% | +8.7% |
| jvm-c1 | GuicedEE scanner / full JDK | JVM | +33.8% | +21.8% | -46.9% | +1.4% | +9.7% |
| jvm-c1 | GuicedEE SPI / application jlink | JVM | +16.2% | -45.4% | +30.6% | +0.9% | -22.2% |
| jvm-c1 | GuicedEE scanner / application jlink | JVM | +26.0% | -40.5% | +93.5% | +3.8% | -20.7% |
| jvm-c1 | GuicedEE SPI / native | Native | +0.2% | -7.5% | +6.6% | +6.5% | +43.2% |
<!-- END GENERATED: relative -->

<!-- BEGIN GENERATED: findings -->
**Default JVM:** linked SPI/scanner complete the first business response in **12.608/13.387 s**, versus **23.553 s** for Quarkus JVM. SPI jlink uses **46.5% less time**. The separate readiness and first-request columns show where that difference occurs.

**C1 JVM:** linked SPI/scanner complete the first business response in **7.519/8.201 s**, versus **13.782 s** for Quarkus JVM. SPI jlink uses **45.4% less time**. The separate readiness and first-request columns show where that difference occurs.
<!-- END GENERATED: findings -->

<a id="local-windows"></a>
## Local Windows profile

These are unrestricted-host, default-tiered JVM runs of the four GuicedEE modes. There is
**no 250m CPU quota, no 500 MiB container limit and no Quarkus row**. They establish the
local mode timings and functional coverage only; they cannot rank against Docker results.
Container memory and image size do not apply to this host profile. OpenAPI request timing
is recorded separately from the first business response.

<!-- BEGIN GENERATED: local-windows -->
Displayed rows: **12 starts / 180 passing checks / 1200 successful measured requests**. Each start: 20 warmups, 100 measured requests. Batch IDs in [latest measurements](results/latest/measurements.json): `20261115-035518`.

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3 | 1.242 | 2,452.72 | 3.688 | 3.672–4.038 | 25.01 |
| GuicedEE scanner / full JDK | 3 | 1.255 | 2,426.32 | 3.696 | 3.657–3.719 | 24.49 |
| GuicedEE SPI / application jlink | 3 | 1.241 | 598.40 | 1.841 | 1.831–1.857 | 24.83 |
| GuicedEE scanner / application jlink | 3 | 1.242 | 581.28 | 1.829 | 1.818–1.842 | 11.26 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 7.41 | 31.38 | 32.05 | — | — | — |
| GuicedEE scanner / full JDK | 7.24 | 31.48 | 32.67 | — | — | — |
| GuicedEE SPI / application jlink | 6.12 | 31.10 | 31.48 | — | — | — |
| GuicedEE scanner / application jlink | 6.10 | 30.61 | 31.57 | — | — | — |
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
| SPI jlink | 3 | `20261115-033737` | `867a886a5d8c` |
| Scanner jlink | 3 | `20261115-033737` | `b8ea0ab4aef0` |
| Quarkus wrapped JVM | 3 | `20261115-034350` | `8bb83742f618` |
| Quarkus upstream JVM | 3 | `20261115-033737` | `ff1c796950c8` |
| GuicedEE native | 3 | `20261115-033737` | `79b8987c62a9` |
| Quarkus upstream native | 3 | `20261115-033737` | `32153f649fea` |
<!-- END GENERATED: phase-sources -->

### Framework startup phases

<!-- BEGIN GENERATED: phase-startup -->
| Inclusive phase (ms) | SPI jlink | Scanner jlink | GuicedEE native |
| --- | ---: | ---: | ---: |
| Context discovery | 497.27 | 496.40 | 4.68 |
| Discovery | 0.29 | 589.98 | 0.00 |
| ClassGraph scan | — | 491.63 | — |
| Pre-startup hooks | 994.13 | 899.58 | 4.15 |
| Guice module discovery | 403.11 | 408.97 | 0.76 |
| Guice injector creation | 1,602.63 | 1,792.87 | 44.40 |
| OpenAPI provider (within injector) | 897.98 | 994.18 | 4.62 |
| Post-startup hooks | 998.05 | 1,095.50 | 95.16 |
<!-- END GENERATED: phase-startup -->

Phases are inclusive wall time, with nested work, class loading, CPU throttling and scheduling.
Do not add columns or subtract internal timings from external startup timers. Quarkus internal
framework startup has no equivalent capture in this harness.

In the linked captures, SPI performs no ClassGraph scan. Scanner mode accepts **three classes
and seven resources**, all in `bench.guicedee.scan`. Both report **35 startup Guice bindings**,
19 explicit and 16 created on demand. SDK internals and lazy bindings are not represented by
that startup snapshot. The native diagnostic uses the same immutable executable as the
headline native comparison, with instrumentation enabled for the phase capture.

### First-use business phases

<!-- BEGIN GENERATED: sdk-headline -->
**Commercetools first-use initialization:** GuicedEE SPI jlink records **0.996 s** versus **10.999 s** for standard Quarkus JVM: **10.003 s less** (**90.9% less time**). These are instrumented phase diagnostics (GuicedEE n=3, Quarkus n=3), separate from build time and the uninstrumented runtime rankings. The samples identify a first-use cost; they do not establish its cause or a general SDK performance ratio.
<!-- END GENERATED: sdk-headline -->

<!-- BEGIN GENERATED: phase-workload -->
| Inclusive phase (ms) | SPI jlink | Scanner jlink | Quarkus wrapped JVM | Quarkus upstream JVM | GuicedEE native | Quarkus upstream native |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| JDK HTTP client construction | 707.13 | 598.80 | 701.20 | 793.40 | 0.34 | 0.80 |
| Commercetools client initialization | 996.40 | 909.83 | 13,811.62 | 10,999.41 | 49.58 | 56.91 |
| Commercetools REST + first OAuth | 1,398.72 | 1,502.63 | 1,497.84 | 1,394.96 | 9.65 | 12.82 |
| GraphQL completion | 202.51 | 201.64 | 203.84 | 200.61 | 1.72 | 2.54 |
| Firestore client initialization | 1,797.49 | 1,699.99 | 1,603.51 | 1,219.99 | 4.98 | 25.17 |
| Firestore write completion | 1,016.13 | 1,202.90 | 1,211.78 | 795.10 | 11.93 | 50.27 |
| Firestore read completion | 93.23 | 7.31 | 13.11 | 12.64 | 1.90 | 1.75 |
<!-- END GENERATED: phase-workload -->

The commercetools initialization phase is distinct from the first REST/OAuth request.
Each column uses the sample counts shown in the diagnostic source table. The data locates
cold SDK cost but does not isolate class loading, JIT compilation or another initializer
as its cause. Instrumented phase durations remain separate from the runtime rankings.

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
