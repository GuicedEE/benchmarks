# Current performance state

**Report: 15 November 2026.** All tables are generated from the latest retained samples.
The complete default/C1 matrices were rerun together for this report; diagnostic and local
profiles have their own recorded batch identities.

<!-- BEGIN GENERATED: host-condition -->
All timing profiles were rerun after the host boot at **2026-11-15T00:45:50.5000000Z**. Across 3 retained one-second preflight samples, host CPU utilization ranged **9.4–13.5%**, available physical memory **32.0–32.3 GiB**. Build, runtime and diagnostic stages ran sequentially. Host observations have partial coverage and are boundary snapshots, not continuous measurements of background load during each run. Available observations and their coverage are included in the latest measurement dataset.
<!-- END GENERATED: host-condition -->

<!-- BEGIN GENERATED: headline -->
GuicedEE native completes the first full business request in **654 ms**, versus **678 ms** for Quarkus native (**3.6% less time**). Warm p50 is **5.96 / 5.85 ms** (GuicedEE / Quarkus). Peak charged memory is **68.77 / 55.04 MiB**; executables are **166.93 / 143.31 MiB**. The native sample contains **28 starts and 420 passing capability checks**.
<!-- END GENERATED: headline -->

<!-- BEGIN GENERATED: runtime-findings -->
GuicedEE native records the lower median full-business startup; Quarkus native records the lower warm p50. Quarkus native has the lower peak container memory. The JVM grids separately report HTTP readiness and completion of the cold SDK/Firestore business request, so both startup costs remain visible.
<!-- END GENERATED: runtime-findings -->

## Build performance

<!-- BEGIN GENERATED: build-headline -->
**Clean JVM build:** GuicedEE SPI compiles in **3.31 s** versus **3.92 s** for Quarkus (**15.6% less time**). Complete runnable JVM packaging takes **3.89 / 6.68 s** (GuicedEE / Quarkus), **41.8% less time**. Medians of 3 clean, offline builds per task; dependency preparation is excluded.

**jlink versus native build:** GuicedEE SPI/scanner jlink packages in **18.11 / 17.95 s**, versus **69.77 s** for Quarkus native (**74.0% less time / 74.3% less time**).
<!-- END GENERATED: build-headline -->

<!-- BEGIN GENERATED: build-grid -->
| Artifact | Clean compile (s) | Compile min–max (s) | Complete package (s) | Package min–max (s) | Build baseline | Package difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3.31 | 3.28–3.39 | 3.89 | 3.81–3.92 | Quarkus fast-JAR | -41.8% |
| GuicedEE scanner / full JDK | 3.28 | 3.21–3.33 | 3.81 | 3.77–3.89 | Quarkus fast-JAR | -43.0% |
| Quarkus upstream SDKs / fast-JAR | 3.92 | 3.69–4.02 | 6.68 | 6.54–6.85 | Quarkus fast-JAR | Baseline |
| GuicedEE SPI / application jlink | — | — | 18.11 | 18.11–18.20 | Quarkus native | -74.0% |
| GuicedEE scanner / application jlink | — | — | 17.95 | 17.90–18.01 | Quarkus native | -74.3% |
| GuicedEE SPI / native | — | — | 71.17 | 70.04–71.56 | Quarkus native | +2.0% |
| Quarkus upstream SDKs / native | — | — | 69.77 | 69.31–72.51 | Quarkus native | Baseline |
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

### Native compiler memory

<!-- BEGIN GENERATED: build-memory -->
| Native compiler | Builds | Median peak RSS (GB) | Min–max (GB) |
| --- | ---: | ---: | ---: |
| GuicedEE SPI / native | 3 | 8.70 | 8.66–8.89 |
| Quarkus upstream SDKs / native | 3 | 8.04 | 7.97–8.11 |
<!-- END GENERATED: build-memory -->

These are the compiler-reported peak RSS values from each timed native build, in the
compiler's decimal GB units and rounded log precision. They describe the native compiler
process, not the application at runtime or the combined Maven/container peak. Both builders
use the same 8 GiB heap limit; RSS also includes memory outside that heap.

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
| GuicedEE SPI / full JDK | 3.89 | 26.533 | 91.64 |
| GuicedEE scanner / full JDK | 3.81 | 26.758 | 92.00 |
| Quarkus upstream SDKs / fast-JAR | 6.68 | 21.882 | 87.02 |
| GuicedEE SPI / application jlink | 18.11 | 13.103 | 90.05 |
| GuicedEE scanner / application jlink | 17.95 | 13.844 | 91.41 |
| GuicedEE SPI / native | 71.17 | 0.654 | 5.96 |
| Quarkus upstream SDKs / native | 69.77 | 0.678 | 5.85 |
<!-- END GENERATED: build-runtime -->

<!-- BEGIN GENERATED: build-findings -->
GuicedEE's JVM package requires **41.8% less time** than Quarkus fast-JAR.

**jlink versus native:** SPI/scanner jlink take **18.11 / 17.95 s**. Against Quarkus native's **69.77 s**, that is **74.0% less time / 74.3% less time**; against GuicedEE native's **71.17 s**, it is **74.6% less time / 74.8% less time**.

The complete GuicedEE native build takes **71.17 s** versus **69.77 s**, or **2.0% more time**. jlink produces a bundled JVM runtime; native builds produce ahead-of-time executables. The runtime grid shows the startup and request-latency tradeoffs for each artifact.
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
| GuicedEE SPI | [26.533](RESULTS.md#jvm-default) | [16.769](RESULTS.md#jvm-c1) | [13.103](RESULTS.md#jvm-default) | [7.875](RESULTS.md#jvm-c1) | [0.654](RESULTS.md#native-standard) |
| GuicedEE scanner | [26.758](RESULTS.md#jvm-default) | [16.885](RESULTS.md#jvm-c1) | [13.844](RESULTS.md#jvm-default) | [7.975](RESULTS.md#jvm-c1) | SPI only |
| Quarkus / upstream SDKs | [21.882](RESULTS.md#jvm-default) | [14.138](RESULTS.md#jvm-c1) | Not implemented | Not implemented | [0.678](RESULTS.md#native-standard) |
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
Displayed rows: **28 starts / 420 passing checks / 840 successful measured requests**. Each start: 10 warmups, 30 measured requests. Batch IDs in [latest measurements](results/latest/measurements.json): `20261115-103846`, `20261115-103923`.

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | 14 | 0.577 | 80.03 | 0.654 | 0.639–1.057 | 3.51 |
| Quarkus upstream SDKs / native | 14 | 0.569 | 104.93 | 0.678 | 0.656–0.995 | 2.12 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | 5.96 | 26.27 | 29.99 | 68.77 | 68.35–69.64 | 65.36 |
| Quarkus upstream SDKs / native | 5.85 | 30.39 | 31.25 | 55.04 | 54.43–56.26 | 51.58 |
<!-- END GENERATED: native-standard -->

<!-- BEGIN GENERATED: native-deltas -->
| Metric | GuicedEE native | Quarkus upstream native | GuicedEE difference |
| --- | ---: | ---: | ---: |
| Full-business startup | 653.70 ms | 678.38 ms | -3.6% |
| First business request | 80.03 ms | 104.93 ms | -23.7% |
| Warm p50 | 5.96 ms | 5.85 ms | +2.0% |
| Warm p95 | 26.27 ms | 30.39 ms | -13.6% |
| Warm p99 | 29.99 ms | 31.25 ms | -4.0% |
| Peak container memory | 68.77 MiB | 55.04 MiB | +25.0% |
| Executable size | 166.93 MiB | 143.31 MiB | +16.5% |
| Docker local image size | 389.03 MiB | 353.04 MiB | +10.2% |
<!-- END GENERATED: native-deltas -->

Negative differences mean GuicedEE uses less time or space. Readiness polling is 50 ms,
so small readiness differences are not precise internal startup measurements. Warm p95/p99
are medians of per-start percentiles; these sequential samples do not establish sustained
throughput. First-use outliers remain included. The [native grid](#native-standard) makes
the startup/latency and memory/size tradeoff explicit.

### Extended native request sequence

This separate cohort uses the same native images, heap settings and container limits,
with **1,000 measured requests per start**. It checks behavior beyond the shorter primary
sample. Requests remain sequential; this is not a concurrent throughput or soak benchmark.

<!-- BEGIN GENERATED: native-extended -->
Displayed rows: **6 starts / 90 passing checks / 6000 successful measured requests**. Each start: 20 warmups, 1000 measured requests. Batch IDs in [latest measurements](results/latest/measurements.json): `20261115-104001`.

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | 3 | 0.580 | 104.23 | 0.685 | 0.669–0.977 | 3.30 |
| Quarkus upstream SDKs / native | 3 | 0.572 | 80.37 | 0.658 | 0.648–0.661 | 1.88 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | 4.79 | 29.97 | 40.95 | 77.51 | 76.62–83.37 | 74.09 |
| Quarkus upstream SDKs / native | 4.49 | 28.03 | 33.61 | 81.00 | 78.87–84.44 | 77.21 |
<!-- END GENERATED: native-extended -->

<!-- BEGIN GENERATED: extended-findings -->
In this separate 3-start-per-framework cohort, median peak charged memory is **77.51 / 81.00 MiB** (GuicedEE / Quarkus), a GuicedEE difference of **-4.3%**. Its full-business startup medians are **685 / 658 ms**. Keep this smaller startup sample separate from the primary counterbalanced comparison; longer request sequences also change allocation and GC behavior.
<!-- END GENERATED: extended-findings -->

### Native inclusion and allocation audit

The current application excludes 15 unused xDS, RLS, legacy grpclb and Google C2P service
providers from native compilation. DNS, ordinary load balancing, transports and TLS
providers remain registered. SDK JARs and JPMS descriptors are preserved. The optional
control-plane providers can be restored with `--include-cloud-control-plane`.

The application's native SPI sets pooled Netty allocators to 64 KiB chunks, including the
relocated SDK copies with their own property names. Runtime `-D` overrides are supported.
These are application defaults; the normal Quarkus implementation is unchanged. Both
native compilers still use O2, Serial GC, x86-64-v3 and an 8 GiB builder heap.
[Configuration and overrides](guicedee-native/README.md) describe the scope.

<!-- BEGIN GENERATED: native-audit -->
| Metric | Previous GuicedEE artifact | Current GuicedEE artifact | Difference |
| --- | ---: | ---: | ---: |
| Executable | 191.83 MiB | 166.93 MiB | -13.0% |
| Reachable methods | 232,581 | 175,092 | -24.7% |
| Compiled code area | 83.13 MiB | 67.74 MiB | -18.5% |
| Image heap | 108.31 MiB | 98.81 MiB | -8.8% |
| Artifact compiler peak RSS | 9856.12 MiB | 8697.71 MiB | -11.8% |
| Full-business startup | 670.27 ms | 650.51 ms | -2.9% |
| Peak charged memory | 79.89 MiB | 68.95 MiB | -13.7% |

Runtime rows use 7 alternating starts per artifact, with the same CPU, memory, heap and request settings. Compiler counts and peak RSS describe the single builds that produced the two artifacts; clean-build time is measured separately in the build grid. The full-provider override also passed **90 capability checks** across 6 starts. This validates the existing workload with the override, not connectivity to a real xDS control plane. [Raw audit evidence](results/latest/native-audit.json).
<!-- END GENERATED: native-audit -->

The retained compiler breakdown identifies `java.base`, Firebase and commercetools as the
largest remaining code origins. XML, Jackson, Log4j, OpenAPI and HTTP/Vert.x code also remain.
These are candidates for more targeted reachability work, not evidence that their whole
modules can be removed. Reflection metadata and SDK model types still contribute to the
image heap. The [audit evidence](results/latest/native-audit.json) retains the compiler's
top code origins and heap object types alongside its counts.

The headline memory figures are **peak charged container memory**, not process RSS. The
harness reads executable files to verify identity before launching each process, so these
are process starts with a warm filesystem cache. Separate end-of-run RSS/PSS snapshots
below come from the instrumented native phase captures. They include resident file mappings
and diagnostic overhead and must not be substituted for the uninstrumented peak figures.

<!-- BEGIN GENERATED: native-memory -->
| Instrumented native process | Starts | End RSS (MiB) | End PSS (MiB) | Anonymous PSS (MiB) | File-backed PSS (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: |
| GuicedEE native | 3 | 167.67 | 166.96 | 59.68 | 107.28 |
| Quarkus upstream native | 3 | 129.90 | 129.16 | 42.49 | 86.66 |
<!-- END GENERATED: native-memory -->

<a id="jvm-default"></a>
<a id="current-linux-native-comparison"></a>
## Full matched matrix: default JVMs

The full-JDK, application-jlink and native modes use **normal-dependency Quarkus** as the
baseline. Every image passes the same business and capability checks. The native rows
show the alternative compilation strategy within this matched batch.

<!-- BEGIN GENERATED: jvm-default -->
Displayed rows: **21 starts / 315 passing checks / 630 successful measured requests**. Each start: 10 warmups, 30 measured requests. Batch IDs in [latest measurements](results/latest/measurements.json): `20261115-104139`.

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3 | 8.305 | 18,259.12 | 26.533 | 25.912–28.290 | 103.38 |
| GuicedEE scanner / full JDK | 3 | 8.750 | 17,997.57 | 26.758 | 26.707–27.642 | 198.72 |
| Quarkus upstream SDKs / fast-JAR | 3 | 6.384 | 15,497.65 | 21.882 | 21.080–24.007 | 410.48 |
| GuicedEE SPI / application jlink | 3 | 7.411 | 5,707.80 | 13.103 | 13.091–13.198 | 188.00 |
| GuicedEE scanner / application jlink | 3 | 8.161 | 5,801.08 | 13.844 | 13.160–13.962 | 173.80 |
| GuicedEE SPI / native | 3 | 0.577 | 77.07 | 0.654 | 0.653–0.655 | 25.30 |
| Quarkus upstream SDKs / native | 3 | 0.574 | 113.76 | 0.688 | 0.679–0.705 | 2.05 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 91.64 | 97.89 | 98.55 | 299.10 | 294.73–375.63 | 295.64 |
| GuicedEE scanner / full JDK | 92.00 | 98.88 | 99.43 | 307.20 | 300.46–381.36 | 298.01 |
| Quarkus upstream SDKs / fast-JAR | 87.02 | 96.67 | 97.61 | 275.88 | 273.81–357.88 | 272.45 |
| GuicedEE SPI / application jlink | 90.05 | 97.68 | 98.66 | 235.65 | 233.33–241.33 | 232.45 |
| GuicedEE scanner / application jlink | 91.41 | 97.63 | 100.16 | 232.79 | 222.28–239.10 | 229.66 |
| GuicedEE SPI / native | 5.21 | 30.45 | 31.11 | 69.57 | 69.45–70.11 | 66.81 |
| Quarkus upstream SDKs / native | 5.27 | 25.54 | 26.50 | 55.44 | 54.75–55.70 | 51.71 |
<!-- END GENERATED: jvm-default -->

<a id="jvm-c1"></a>
## Full matched matrix: equal C1 JVM tuning

These are the **same immutable images** as the default matrix, with C1 applied equally to
all JVMs. Quarkus native is repeated as a batch reference using the same binary and no JIT flag.

<!-- BEGIN GENERATED: jvm-c1 -->
Displayed rows: **21 starts / 315 passing checks / 630 successful measured requests**. Each start: 10 warmups, 30 measured requests. Batch IDs in [latest measurements](results/latest/measurements.json): `20261115-104831`.

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3 | 5.065 | 11,703.39 | 16.769 | 16.479–22.637 | 21.92 |
| GuicedEE scanner / full JDK | 3 | 5.234 | 11,698.60 | 16.885 | 16.831–17.201 | 99.30 |
| Quarkus upstream SDKs / fast-JAR | 3 | 4.117 | 10,000.39 | 14.138 | 14.017–14.292 | 296.86 |
| GuicedEE SPI / application jlink | 3 | 4.683 | 3,192.39 | 7.875 | 7.839–7.898 | 81.71 |
| GuicedEE scanner / application jlink | 3 | 4.862 | 3,113.56 | 7.975 | 7.948–8.227 | 91.79 |
| GuicedEE SPI / native | 3 | 0.582 | 80.45 | 0.663 | 0.634–0.688 | 3.53 |
| Quarkus upstream SDKs / native | 3 | 0.579 | 118.21 | 0.691 | 0.689–0.712 | 2.18 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 19.60 | 89.55 | 89.62 | 262.79 | 262.24–262.80 | 258.71 |
| GuicedEE scanner / full JDK | 34.96 | 89.73 | 89.86 | 265.22 | 265.21–265.35 | 262.05 |
| Quarkus upstream SDKs / fast-JAR | 18.01 | 89.75 | 89.80 | 241.42 | 240.41–241.76 | 237.76 |
| GuicedEE SPI / application jlink | 30.67 | 91.34 | 91.60 | 188.64 | 187.61–188.88 | 185.06 |
| GuicedEE scanner / application jlink | 50.22 | 90.29 | 90.85 | 191.35 | 187.82–192.31 | 187.52 |
| GuicedEE SPI / native | 5.82 | 28.83 | 29.83 | 69.11 | 68.92–69.39 | 65.50 |
| Quarkus upstream SDKs / native | 5.06 | 28.97 | 30.12 | 54.96 | 54.46–55.27 | 51.82 |
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
| jvm-default | GuicedEE SPI / full JDK | JVM | +30.1% | +21.3% | +5.3% | +1.3% | +8.4% |
| jvm-default | GuicedEE scanner / full JDK | JVM | +37.1% | +22.3% | +5.7% | +2.3% | +11.4% |
| jvm-default | GuicedEE SPI / application jlink | JVM | +16.1% | -40.1% | +3.5% | +1.0% | -14.6% |
| jvm-default | GuicedEE scanner / application jlink | JVM | +27.8% | -36.7% | +5.1% | +1.0% | -15.6% |
| jvm-default | GuicedEE SPI / native | Native | +0.5% | -4.9% | -1.2% | +19.2% | +25.5% |
| jvm-c1 | GuicedEE SPI / full JDK | JVM | +23.0% | +18.6% | +8.8% | -0.2% | +8.9% |
| jvm-c1 | GuicedEE scanner / full JDK | JVM | +27.1% | +19.4% | +94.1% | -0.0% | +9.9% |
| jvm-c1 | GuicedEE SPI / application jlink | JVM | +13.8% | -44.3% | +70.2% | +1.8% | -21.9% |
| jvm-c1 | GuicedEE scanner / application jlink | JVM | +18.1% | -43.6% | +178.7% | +0.6% | -20.7% |
| jvm-c1 | GuicedEE SPI / native | Native | +0.6% | -4.0% | +15.0% | -0.5% | +25.8% |
<!-- END GENERATED: relative -->

<!-- BEGIN GENERATED: findings -->
**Default JVM:** linked SPI/scanner complete the first business response in **13.103/13.844 s**, versus **21.882 s** for Quarkus JVM. SPI jlink uses **40.1% less time**. The separate readiness and first-request columns show where that difference occurs.

**C1 JVM:** linked SPI/scanner complete the first business response in **7.875/7.975 s**, versus **14.138 s** for Quarkus JVM. SPI jlink uses **44.3% less time**. The separate readiness and first-request columns show where that difference occurs.
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
| GuicedEE SPI / native | native-standard | 389.03 | 166.93 | `22c33c17f637` |
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
performance grids.** The columns below come from separate diagnostic batches, with three
starts per variant. They provide coverage and hypotheses, not a matched phase-level framework
ranking. Missing phases mean unmeasured,
not zero cost.

<!-- BEGIN GENERATED: phase-sources -->
| Diagnostic variant | Starts | Evidence | Image ID prefix |
| --- | ---: | ---: | ---: |
| SPI jlink | 3 | `20261115-033737` | `867a886a5d8c` |
| Scanner jlink | 3 | `20261115-033737` | `b8ea0ab4aef0` |
| Quarkus wrapped JVM | 3 | `20261115-034350` | `8bb83742f618` |
| Quarkus upstream JVM | 3 | `20261115-033737` | `ff1c796950c8` |
| GuicedEE native | 3 | `20261115-104115` | `22c33c17f637` |
| Quarkus upstream native | 3 | `20261115-104115` | `32153f649fea` |
<!-- END GENERATED: phase-sources -->

### Framework startup phases

<!-- BEGIN GENERATED: phase-startup -->
| Inclusive phase (ms) | SPI jlink | Scanner jlink | GuicedEE native |
| --- | ---: | ---: | ---: |
| Context discovery | 497.27 | 496.40 | 5.21 |
| Discovery | 0.29 | 589.98 | 0.00 |
| ClassGraph scan | — | 491.63 | — |
| Pre-startup hooks | 994.13 | 899.58 | 5.24 |
| Guice module discovery | 403.11 | 408.97 | 1.04 |
| Guice injector creation | 1,602.63 | 1,792.87 | 60.10 |
| OpenAPI provider (within injector) | 897.98 | 994.18 | 5.40 |
| Post-startup hooks | 998.05 | 1,095.50 | 93.15 |
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
| JDK HTTP client construction | 707.13 | 598.80 | 701.20 | 793.40 | 0.40 | 0.56 |
| Commercetools client initialization | 996.40 | 909.83 | 13,811.62 | 10,999.41 | 33.64 | 44.63 |
| Commercetools REST + first OAuth | 1,398.72 | 1,502.63 | 1,497.84 | 1,394.96 | 9.70 | 11.04 |
| GraphQL completion | 202.51 | 201.64 | 203.84 | 200.61 | 2.33 | 2.63 |
| Firestore client initialization | 1,797.49 | 1,699.99 | 1,603.51 | 1,219.99 | 5.43 | 37.80 |
| Firestore write completion | 1,016.13 | 1,202.90 | 1,211.78 | 795.10 | 86.15 | 8.78 |
| Firestore read completion | 93.23 | 7.31 | 13.11 | 12.64 | 1.70 | 1.41 |
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
| native-standard | GuicedEE SPI / native | `sha256:22c33c17f6378602a853a4e869dcbe40f8f9152a6622a6348e572c18347b59ee` |
| native-standard | Quarkus upstream SDKs / native | `sha256:32153f649fea73fc6143645f48a1c3969851a318903d308a32a7b3876869ec69` |
| jvm-default | GuicedEE SPI / full JDK | `sha256:fad5ba9c31502a0d22bc8a2ddb31c8de9d7d49b05e773eb40de43a5ff9ee4cfb` |
| jvm-default | GuicedEE scanner / full JDK | `sha256:a9817e6465b054e8d2419cc03883ce6b81f4ec1bbaeedaa3631a0a5ec6a4ec8f` |
| jvm-default | Quarkus upstream SDKs / fast-JAR | `sha256:ff1c796950c84a86c8bc4f833fb17794bf4d4343ab52b98b51ffc0df436d45a8` |
| jvm-default | GuicedEE SPI / application jlink | `sha256:867a886a5d8cf020d5d9320b93d521acf995535480c7f18d259620f031d7f86a` |
| jvm-default | GuicedEE scanner / application jlink | `sha256:b8ea0ab4aef0522b489a9ab6e42a4944a996758f813c5395c4c66af4703df2ac` |
| jvm-default | GuicedEE SPI / native | `sha256:22c33c17f6378602a853a4e869dcbe40f8f9152a6622a6348e572c18347b59ee` |
| jvm-default | Quarkus upstream SDKs / native | `sha256:32153f649fea73fc6143645f48a1c3969851a318903d308a32a7b3876869ec69` |
| jvm-c1 | GuicedEE SPI / full JDK | `sha256:fad5ba9c31502a0d22bc8a2ddb31c8de9d7d49b05e773eb40de43a5ff9ee4cfb` |
| jvm-c1 | GuicedEE scanner / full JDK | `sha256:a9817e6465b054e8d2419cc03883ce6b81f4ec1bbaeedaa3631a0a5ec6a4ec8f` |
| jvm-c1 | Quarkus upstream SDKs / fast-JAR | `sha256:ff1c796950c84a86c8bc4f833fb17794bf4d4343ab52b98b51ffc0df436d45a8` |
| jvm-c1 | GuicedEE SPI / application jlink | `sha256:867a886a5d8cf020d5d9320b93d521acf995535480c7f18d259620f031d7f86a` |
| jvm-c1 | GuicedEE scanner / application jlink | `sha256:b8ea0ab4aef0522b489a9ab6e42a4944a996758f813c5395c4c66af4703df2ac` |
| jvm-c1 | GuicedEE SPI / native | `sha256:22c33c17f6378602a853a4e869dcbe40f8f9152a6622a6348e572c18347b59ee` |
| jvm-c1 | Quarkus upstream SDKs / native | `sha256:32153f649fea73fc6143645f48a1c3969851a318903d308a32a7b3876869ec69` |
| native-extended | GuicedEE SPI / native | `sha256:22c33c17f6378602a853a4e869dcbe40f8f9152a6622a6348e572c18347b59ee` |
| native-extended | Quarkus upstream SDKs / native | `sha256:32153f649fea73fc6143645f48a1c3969851a318903d308a32a7b3876869ec69` |
<!-- END GENERATED: image-identities -->
