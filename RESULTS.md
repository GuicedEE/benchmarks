# Current performance state

**Report: 15 November 2026.** All tables are generated from the latest retained samples.
The complete default/C1 matrices were rerun together for this report; diagnostic
profiles have their own recorded batch identities.

<!-- BEGIN GENERATED: host-condition -->
All timing profiles were rerun after the host boot at **2026-11-15T00:45:50.5000000Z**. Across 6 retained one-second host samples, CPU utilization ranged **5.8–13.0%**, available physical memory **22.2–26.9 GiB**. Build, runtime and diagnostic stages ran sequentially. Host observations have partial coverage and are boundary snapshots, not continuous measurements of background load during each run. Available observations and their coverage are included in the latest measurement dataset. The six retained one-second snapshots precede the earlier native and clean-build cohorts. The current JVM runtime and diagnostic batches ran sequentially afterwards; no continuous background-load sampler was used for them.
<!-- END GENERATED: host-condition -->

<!-- BEGIN GENERATED: headline -->
GuicedEE native completes the first full business request in **656 ms**, versus **678 ms** for Quarkus native (**3.2% less time**). Warm p50 is **5.21 / 5.11 ms** (GuicedEE / Quarkus). Peak charged memory is **68.47 / 55.30 MiB**; executables are **142.35 / 143.31 MiB**. The native sample contains **28 starts and 420 passing capability checks**.
<!-- END GENERATED: headline -->

<!-- BEGIN GENERATED: runtime-findings -->
GuicedEE native records the lower median full-business startup; Quarkus native records the lower warm p50. Quarkus native has the lower peak container memory. The JVM grids separately report HTTP readiness and completion of the cold SDK/Firestore business request, so both startup costs remain visible.
<!-- END GENERATED: runtime-findings -->

## Build performance

<!-- BEGIN GENERATED: build-headline -->
**Clean JVM build:** GuicedEE SPI compiles in **3.14 s** versus **3.66 s** for Quarkus (**14.1% less time**). Complete runnable JVM packaging takes **3.61 / 6.29 s** (GuicedEE / Quarkus), **42.6% less time**. Medians of 3 clean, offline builds per task; dependency preparation is excluded.

**jlink versus native build:** GuicedEE SPI/scanner jlink packages in **17.68 / 17.34 s**, versus **66.36 s** for Quarkus native (**73.4% less time / 73.9% less time**).
<!-- END GENERATED: build-headline -->

![Clean compilation and complete packaging](docs/builds.svg)

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
| GuicedEE SPI / native | 3 | 8.50 | 8.35–8.59 |
| Quarkus upstream SDKs / native | 3 | 7.97 | 7.95–8.01 |
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
| GuicedEE SPI / full JDK | 3.61 | 22.928 | 91.55 |
| GuicedEE scanner / full JDK | 3.68 | 23.706 | 93.71 |
| Quarkus upstream SDKs / fast-JAR | 6.29 | 23.387 | 90.58 |
| GuicedEE SPI / application jlink | 17.68 | 12.966 | 91.14 |
| GuicedEE scanner / application jlink | 17.34 | 13.556 | 91.29 |
| GuicedEE SPI / native | 65.05 | 0.656 | 5.21 |
| Quarkus upstream SDKs / native | 66.36 | 0.678 | 5.11 |
<!-- END GENERATED: build-runtime -->

<!-- BEGIN GENERATED: build-findings -->
GuicedEE's JVM package requires **42.6% less time** than Quarkus fast-JAR.

**jlink versus native:** SPI/scanner jlink take **17.68 / 17.34 s**. Against Quarkus native's **66.36 s**, that is **73.4% less time / 73.9% less time**; against GuicedEE native's **65.05 s**, it is **72.8% less time / 73.3% less time**.

The complete GuicedEE native build takes **65.05 s** versus **66.36 s**, or **2.0% less time**. jlink produces a bundled JVM runtime; native builds produce ahead-of-time executables. The runtime grid shows the startup and request-latency tradeoffs for each artifact.

Native build ranges overlap: **64.97–80.24 s** for GuicedEE and **66.07–66.67 s** for Quarkus. With 3 samples each, the median difference does not establish a consistent build-time lead.
<!-- END GENERATED: build-findings -->

Runtime columns use the default-JVM cohort and the larger native-only cohort, each under
250m CPU / 500 MiB. This table connects artifact choices to the measured runtime behavior;
builds and runtime samples are not paired observations. C1 changes launch flags, not the
artifact build, so its startup improvements do not incur a separate compilation cost.
The [C1 grid](#jvm-c1) retains its own runtime results.

## All execution modes

Values are median launch to completed business response in seconds. The default and C1
matrices measure the same five immutable JVM/jlink images. The primary native-only comparison has
a larger counterbalanced sample. Full grids retain every start and measured request.

![Startup by execution mode](docs/startup.svg)

<!-- BEGIN GENERATED: overview -->
| Application | Full JDK default (s) | Full JDK C1 (s) | Application jlink default (s) | Application jlink C1 (s) | Native (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI | [22.928](RESULTS.md#jvm-default) | [13.353](RESULTS.md#jvm-c1) | [12.966](RESULTS.md#jvm-default) | [7.567](RESULTS.md#jvm-c1) | [0.656](RESULTS.md#native-standard) |
| GuicedEE scanner | [23.706](RESULTS.md#jvm-default) | [13.364](RESULTS.md#jvm-c1) | [13.556](RESULTS.md#jvm-default) | [7.874](RESULTS.md#jvm-c1) | SPI only |
| Quarkus / upstream SDKs | [23.387](RESULTS.md#jvm-default) | [14.311](RESULTS.md#jvm-c1) | Not implemented | Not implemented | [0.678](RESULTS.md#native-standard) |
<!-- END GENERATED: overview -->

Read the [native comparison](#native-standard), [default JVM matrix](#jvm-default),
[C1 matrix](#jvm-c1), [percentage differences](#relative-differences),
[packaging](#packaging), and [phase diagnostics](#phase-diagnostics).

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
Displayed rows: **28 starts / 420 passing checks / 840 successful measured requests**. Each start: 10 warmups, 30 measured requests. Batch IDs in [latest measurements](results/latest/measurements.json): `20261115-124931`, `20261115-125007`.

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | 14 | 0.576 | 77.70 | 0.656 | 0.614–0.950 | 3.52 |
| Quarkus upstream SDKs / native | 14 | 0.573 | 105.04 | 0.678 | 0.658–1.005 | 2.39 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | 5.21 | 27.40 | 29.93 | 68.47 | 67.91–69.38 | 65.06 |
| Quarkus upstream SDKs / native | 5.11 | 26.02 | 28.22 | 55.30 | 54.41–55.87 | 52.00 |
<!-- END GENERATED: native-standard -->

<!-- BEGIN GENERATED: native-deltas -->
| Metric | GuicedEE native | Quarkus upstream native | GuicedEE difference |
| --- | ---: | ---: | ---: |
| Full-business startup | 656.09 ms | 677.71 ms | -3.2% |
| First business request | 77.70 ms | 105.04 ms | -26.0% |
| Warm p50 | 5.21 ms | 5.11 ms | +1.9% |
| Warm p95 | 27.40 ms | 26.02 ms | +5.3% |
| Warm p99 | 29.93 ms | 28.22 ms | +6.1% |
| Peak container memory | 68.47 MiB | 55.30 MiB | +23.8% |
| Executable size | 142.35 MiB | 143.31 MiB | -0.7% |
| Docker local image size | 357.23 MiB | 353.04 MiB | +1.2% |
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
Displayed rows: **6 starts / 90 passing checks / 6000 successful measured requests**. Each start: 20 warmups, 1000 measured requests. Batch IDs in [latest measurements](results/latest/measurements.json): `20261115-125042`.

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | 3 | 0.578 | 92.65 | 0.669 | 0.651–0.944 | 3.34 |
| Quarkus upstream SDKs / native | 3 | 0.586 | 125.92 | 0.712 | 0.701–0.717 | 2.13 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | 4.07 | 28.01 | 40.42 | 78.88 | 77.14–118.12 | 75.04 |
| Quarkus upstream SDKs / native | 4.12 | 27.73 | 41.72 | 80.09 | 79.62–81.73 | 76.65 |
<!-- END GENERATED: native-extended -->

<!-- BEGIN GENERATED: extended-findings -->
In this separate 3-start-per-framework cohort, median peak charged memory is **78.88 / 80.09 MiB** (GuicedEE / Quarkus), a GuicedEE difference of **-1.5%**. Its full-business startup medians are **669 / 712 ms**. Keep this smaller startup sample separate from the primary counterbalanced comparison; longer request sequences also change allocation and GC behavior.
<!-- END GENERATED: extended-findings -->

### Native inclusion and allocation profile

The current application excludes 15 unused xDS, RLS, legacy grpclb and Google C2P service
providers from native compilation. DNS, ordinary load balancing, transports and TLS
providers remain registered. SDK JARs and JPMS descriptors are preserved. The optional
control-plane providers can be restored with `--include-cloud-control-plane`.

The Linux x86-64 recipe excludes native-library resources for Windows, macOS and ARM,
while retaining Linux x86-64 Conscrypt, gRPC TLS and epoll libraries.

Class-query-only commercetools model metadata is conditional on the model being reachable.
Retained models keep member queries and annotations; actual traced invocation entries remain.
Protobuf accessors keep reflection invocation support, while static parsing convenience overloads
remain callable directly without becoming reflection roots. `--full-sdk-reflection` restores the
original traced model/protobuf metadata. This policy covers the verified workload; additional
SDK operations still require their own native trace and capability checks.

The application's native SPI sets pooled Netty allocators to 64 KiB chunks, including the
relocated SDK copies with their own property names. Runtime `-D` overrides are supported.
These are application defaults; the normal Quarkus implementation is unchanged. Both
native compilers still use O2, Serial GC, x86-64-v3 and an 8 GiB builder heap.
[Configuration and overrides](guicedee-native/README.md) describe the scope.

<!-- BEGIN GENERATED: native-profile -->
| Metric | Current GuicedEE native artifact |
| --- | ---: |
| Reachable types | 33,493 |
| Methods registered for reflection | 53,073 |
| Reachable methods | 172,953 |
| Compiled code area | 67.41 MiB |
| Embedded resources | 281 |
| Image heap | 74.56 MiB |
| Artifact compiler peak RSS | 7969.84 MiB |

Compiler counts and peak RSS describe the single build that produced the currently measured executable. Repeated clean-build time and compiler memory are measured separately in the build grid. [Current compiler profile](results/latest/native-profile.json).
<!-- END GENERATED: native-profile -->

The retained compiler breakdown identifies `java.base`, Firebase and commercetools as the
largest remaining code origins. XML, Jackson, Log4j, OpenAPI and HTTP/Vert.x code also remain.
These are candidates for more targeted reachability work, not evidence that their whole
modules can be removed. Reflection metadata and SDK model types still contribute to the
image heap. The [compiler profile](results/latest/native-profile.json) retains the compiler's
top code origins and heap object types alongside its counts.

The headline memory figures are **peak charged container memory**, not process RSS. The
harness reads executable files to verify identity before launching each process, so these
are process starts with a warm filesystem cache. Separate end-of-run RSS/PSS snapshots
below come from the instrumented native phase captures. They include resident file mappings
and diagnostic overhead and must not be substituted for the uninstrumented peak figures.

<!-- BEGIN GENERATED: native-memory -->
| Instrumented native process | Starts | End RSS (MiB) | End PSS (MiB) | Anonymous PSS (MiB) | File-backed PSS (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: |
| GuicedEE native | 3 | 160.59 | 159.86 | 59.57 | 100.28 |
| Quarkus upstream native | 3 | 129.89 | 129.17 | 42.46 | 86.71 |
<!-- END GENERATED: native-memory -->

<a id="jvm-default"></a>
<a id="current-linux-native-comparison"></a>
## Full matched matrix: default JVMs

The full-JDK, application-jlink and native modes use **normal-dependency Quarkus** as the
baseline. Every image passes the same business and capability checks. The native rows
show the alternative compilation strategy within this matched batch.

<!-- BEGIN GENERATED: jvm-default -->
Displayed rows: **15 starts / 225 passing checks / 450 successful measured requests**. Each start: 10 warmups, 30 measured requests. Batch IDs in [latest measurements](results/latest/measurements.json): `20261115-135709`.

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3 | 10.153 | 12,707.35 | 22.928 | 21.781–23.969 | 99.93 |
| GuicedEE scanner / full JDK | 3 | 10.696 | 13,009.86 | 23.706 | 22.859–25.965 | 187.26 |
| Quarkus upstream SDKs / fast-JAR | 3 | 6.860 | 16,688.65 | 23.387 | 22.469–24.641 | 499.87 |
| GuicedEE SPI / application jlink | 3 | 8.000 | 4,893.75 | 12.966 | 12.790–13.195 | 97.37 |
| GuicedEE scanner / application jlink | 3 | 8.556 | 4,698.86 | 13.556 | 13.153–13.668 | 101.59 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 91.55 | 98.25 | 99.56 | 292.98 | 286.30–296.30 | 289.59 |
| GuicedEE scanner / full JDK | 93.71 | 101.72 | 102.55 | 301.05 | 297.24–305.10 | 297.53 |
| Quarkus upstream SDKs / fast-JAR | 90.58 | 98.38 | 98.56 | 279.12 | 276.70–353.44 | 275.90 |
| GuicedEE SPI / application jlink | 91.14 | 99.75 | 100.02 | 234.10 | 217.48–240.12 | 230.74 |
| GuicedEE scanner / application jlink | 91.29 | 98.64 | 98.88 | 225.54 | 225.41–229.16 | 221.90 |
<!-- END GENERATED: jvm-default -->

<a id="jvm-c1"></a>
## Full matched matrix: equal C1 JVM tuning

These are the **same immutable images** as the default matrix, with C1 applied equally to
all JVMs. Quarkus native is repeated as a batch reference using the same binary and no JIT flag.

<!-- BEGIN GENERATED: jvm-c1 -->
Displayed rows: **15 starts / 225 passing checks / 450 successful measured requests**. Each start: 10 warmups, 30 measured requests. Batch IDs in [latest measurements](results/latest/measurements.json): `20261115-140354`.

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3 | 6.208 | 7,115.84 | 13.353 | 13.166–13.414 | 74.06 |
| GuicedEE scanner / full JDK | 3 | 6.367 | 7,007.77 | 13.364 | 13.334–13.559 | 56.41 |
| Quarkus upstream SDKs / fast-JAR | 3 | 4.192 | 10,105.08 | 14.311 | 14.182–14.500 | 288.89 |
| GuicedEE SPI / application jlink | 3 | 4.972 | 2,595.56 | 7.567 | 7.463–7.718 | 11.80 |
| GuicedEE scanner / application jlink | 3 | 5.266 | 2,602.80 | 7.874 | 7.869–7.889 | 12.24 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 41.30 | 89.14 | 90.48 | 258.95 | 258.57–259.53 | 255.70 |
| GuicedEE scanner / full JDK | 65.39 | 91.02 | 91.84 | 262.56 | 262.55–262.59 | 259.09 |
| Quarkus upstream SDKs / fast-JAR | 23.16 | 89.42 | 90.77 | 241.18 | 240.47–241.23 | 237.57 |
| GuicedEE SPI / application jlink | 45.26 | 92.63 | 93.27 | 186.52 | 186.43–186.94 | 183.00 |
| GuicedEE scanner / application jlink | 31.09 | 90.17 | 92.59 | 190.94 | 188.50–191.26 | 187.51 |
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
| jvm-default | GuicedEE SPI / full JDK | JVM | +48.0% | -2.0% | +1.1% | -0.1% | +5.0% |
| jvm-default | GuicedEE scanner / full JDK | JVM | +55.9% | +1.4% | +3.5% | +3.4% | +7.9% |
| jvm-default | GuicedEE SPI / application jlink | JVM | +16.6% | -44.6% | +0.6% | +1.4% | -16.1% |
| jvm-default | GuicedEE scanner / application jlink | JVM | +24.7% | -42.0% | +0.8% | +0.3% | -19.2% |
| jvm-c1 | GuicedEE SPI / full JDK | JVM | +48.1% | -6.7% | +78.3% | -0.3% | +7.4% |
| jvm-c1 | GuicedEE scanner / full JDK | JVM | +51.9% | -6.6% | +182.4% | +1.8% | +8.9% |
| jvm-c1 | GuicedEE SPI / application jlink | JVM | +18.6% | -47.1% | +95.4% | +3.6% | -22.7% |
| jvm-c1 | GuicedEE scanner / application jlink | JVM | +25.6% | -45.0% | +34.2% | +0.8% | -20.8% |
<!-- END GENERATED: relative -->

<!-- BEGIN GENERATED: findings -->
**Default JVM:** full-JDK SPI/scanner complete the first business response in **22.928/23.706 s**, versus **23.387 s** for Quarkus JVM. SPI uses **2.0% less time**. Use the retained ranges to judge the median difference; each mode has three starts.

**Default JVM, linked workload:** linked SPI/scanner complete the first business response in **12.966/13.556 s**, versus **23.387 s** for Quarkus JVM. SPI jlink uses **44.6% less time** for this workload. The SDK scanner reports zero linked-image URLs, so this is not evidence of equivalent complete SDK model discovery.

**C1 JVM:** full-JDK SPI/scanner complete the first business response in **13.353/13.364 s**, versus **14.311 s** for Quarkus JVM. SPI uses **6.7% less time**. Use the retained ranges to judge the median difference; each mode has three starts.

**C1 JVM, linked workload:** linked SPI/scanner complete the first business response in **7.567/7.874 s**, versus **14.311 s** for Quarkus JVM. SPI jlink uses **47.1% less time** for this workload. The SDK scanner reports zero linked-image URLs, so this is not evidence of equivalent complete SDK model discovery.
<!-- END GENERATED: findings -->

<a id="packaging"></a>
## Packaging and module footprint

Image sizes below cover each measured binary once. Runtime memory is in the performance
grids above; it is not the same quantity as disk size.

<!-- BEGIN GENERATED: packaging -->
| Variant | Evidence group | Docker local image (MiB) | Executable (MiB) | Image ID prefix |
| --- | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | native-standard | 357.23 | 142.35 | `cba41d26ee56` |
| Quarkus upstream SDKs / native | native-standard | 353.04 | 143.31 | `32153f649fea` |
| GuicedEE SPI / full JDK | jvm-default | 1,027.28 | — | `81dc069a9833` |
| GuicedEE scanner / full JDK | jvm-default | 1,027.27 | — | `b08deee9eafc` |
| Quarkus upstream SDKs / fast-JAR | jvm-default | 976.77 | — | `ff1c796950c8` |
| GuicedEE SPI / application jlink | jvm-default | 498.16 | — | `328a1e99248b` |
| GuicedEE scanner / application jlink | jvm-default | 498.16 | — | `c394e88f4118` |
<!-- END GENERATED: packaging -->

The linked-runtime audit applies specifically to the images in the full JVM matrix:

<!-- BEGIN GENERATED: jlink-size -->
| Measured jlink payload | SPI | Scanner |
| --- | ---: | ---: |
| Runtime including application (MiB) | 180.78 | 180.77 |
| Module image (MiB) | 147.11 | 147.11 |
| Unpacked Docker layers (MiB) | 299.51 | 299.51 |
| Installed modules | 124 | 124 |
| Mandatory module closure | 112 | 112 |
| Closure including installed service providers | 117 | 117 |
<!-- END GENERATED: jlink-size -->

The roughly 498 MiB Docker-store value contains a **181 MiB linked application runtime**.
The graph is valid but not minimal: 124 installed modules versus 112 in the mandatory closure
and 117 when resolving providers already present. The current dataset retains the application roots, installed module names and both closure
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
| Scanner JVM | 1 | `20261115-140817` | `b08deee9eafc` |
| SPI JVM | 1 | `20261115-140817` | `81dc069a9833` |
| SPI jlink | 1 | `20261115-140817` | `328a1e99248b` |
| Scanner jlink | 1 | `20261115-140817` | `c394e88f4118` |
| Quarkus upstream JVM | 1 | `20261115-140817` | `ff1c796950c8` |
| GuicedEE native | 3 | `20261115-125151` | `cba41d26ee56` |
| Quarkus upstream native | 3 | `20261115-125151` | `32153f649fea` |
<!-- END GENERATED: phase-sources -->

### Framework startup phases

<!-- BEGIN GENERATED: phase-startup -->
| Inclusive phase (ms) | SPI JVM | Scanner JVM | SPI jlink | Scanner jlink | GuicedEE native |
| --- | ---: | ---: | ---: | ---: | ---: |
| Context discovery | 889.69 | 510.58 | 602.26 | 596.62 | 4.60 |
| Discovery | 0.32 | 594.50 | 0.37 | 500.93 | 0.00 |
| ClassGraph scan | — | 398.11 | — | 397.85 | — |
| Pre-startup hooks | 1,304.09 | 705.12 | 1,098.52 | 812.70 | 4.51 |
| Guice module discovery | 698.48 | 402.60 | 403.66 | 493.46 | 0.88 |
| Guice injector creation | 2,093.55 | 1,792.94 | 1,704.25 | 1,795.82 | 17.14 |
| OpenAPI provider (within injector) | 1,198.38 | 1,094.22 | 998.91 | 1,089.73 | 5.02 |
| Post-startup hooks | 1,496.76 | 994.11 | 897.30 | 1,100.48 | 92.42 |
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
**Commercetools first-use initialization:** GuicedEE SPI JVM records **13.995 s** versus **11.503 s** for standard Quarkus JVM: **2.492 s more** (**21.7% more time**). These are instrumented phase diagnostics (GuicedEE n=1, Quarkus n=1), separate from build time and the uninstrumented runtime rankings. The samples identify a first-use cost; they do not establish a general SDK performance ratio. The linked-image SDK scanner reports zero URLs; jlink timings cover the tested workload, not complete SDK mixin/subtype discovery.
<!-- END GENERATED: sdk-headline -->

<!-- BEGIN GENERATED: phase-workload -->
| Inclusive phase (ms) | Scanner JVM | SPI JVM | SPI jlink | Scanner jlink | Quarkus upstream JVM | GuicedEE native | Quarkus upstream native |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| JDK HTTP client construction | 1,600.31 | 2,798.89 | 1,194.39 | 1,005.29 | 708.12 | 0.35 | 0.60 |
| Commercetools client initialization | 9,105.06 | 13,995.06 | 499.97 | 509.15 | 11,502.78 | 42.15 | 38.85 |
| Commercetools REST + first OAuth | 897.15 | 1,093.52 | 999.97 | 993.26 | 1,303.63 | 8.17 | 10.54 |
| GraphQL completion | 194.85 | 102.10 | 99.40 | 199.05 | 199.99 | 1.43 | 2.15 |
| Firestore client initialization | 1,414.18 | 1,804.74 | 1,613.67 | 1,697.33 | 1,498.43 | 4.95 | 31.35 |
| Firestore write completion | 1,110.47 | 2,062.01 | 1,699.96 | 1,297.93 | 814.49 | 9.97 | 8.01 |
| Firestore read completion | 8.70 | 38.52 | 10.46 | 8.37 | 86.12 | 1.33 | 1.39 |
<!-- END GENERATED: phase-workload -->

The commercetools initialization phase is distinct from the first REST/OAuth request.
Each column uses the sample counts shown in the diagnostic source table. The data locates
cold SDK cost but does not isolate class loading, JIT compilation or another initializer
as its entire cause. The SDK constructs two identical Reflections scans during mapper
creation; the current JVM wrapper shares their index only for that construction.
Instrumented phase durations remain separate from the runtime rankings.

<a id="jvm-discovery-boundaries"></a>
### JVM discovery and measurement boundaries

The current JVM artifacts use the packaged Commercetools wrapper with scoped scan reuse
and its current external dependency graph. Named-module smoke checks discover all four SDK
mixins and 2,047 annotated SDK subtypes, plus application-defined extensions. Unit checks
compare discovery with the original scanner and cover mapper options, independent scans,
nested scopes, context class loaders and cleanup after provider failure.

The native images and clean-build samples retain their separately identified earlier
artifact cohort. Shared workload sources are unchanged; the updated JVM dependency graph
has not had its clean build times or native images remeasured. The build/runtime tradeoff
table juxtaposes those identified cohorts, not a rebuild of the new JVM wrapper as native.

In the linked images, the SDK's Reflections scanner reports **zero scan URLs**. The complete
benchmark workload passes, but those runs do not establish full SDK mixin/subtype discovery
from `jrt:/`. The jlink SDK initialization gap must not be presented as an equivalent full
model-discovery speedup. This is separate from GuicedEE's own application discovery checks.

SDK spans wait for completion of the asynchronous operations. The shared Firestore adapter
currently waits on SDK futures inside `CompletableFuture.supplyAsync`; both applications
wait for it, so the work is timed, although that adapter is not fully nonblocking. The HTTP
client construction phase sums repeated constructions within each start before taking its
median. Quarkus CDI proxy/subclass construction can initialize the workload twice; a second
construction is retained in the capture rather than counted as a second business operation.

<a id="postgresql-persistence"></a>
## PostgreSQL persistence

This separate workload uses 15 related entities and 19 foreign keys, with the same graph
and query in both applications. Readiness includes the database lifecycle; the first business
response includes the committed graph. The graph precedes the detailed measurements below.

<!-- BEGIN GENERATED: persistence -->
Measured **2026-11-15**, **default JVM profile**, batch `20261115-165957`. **6 fresh starts / 84 passing checks**. Each start has 20 warmup reads and CRUD cycles, then 60 measured reads and 60 measured CRUD cycles. All samples are retained.

![PostgreSQL startup and transaction latency](docs/persistence.svg)

| Application | Starts | DB-ready (s) | First transaction (ms) | Launch to committed graph (s) | Full startup min–max (s) | Peak charged memory (MiB) | Hibernate ORM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE reactive stateless | 3 | 14.226 | 1895.58 | 16.118 | 16.116–16.432 | 243.45 | 7.4.15.Final |
| Quarkus ORM / Narayana | 3 | 9.918 | 1881.92 | 11.618 | 11.471–12.278 | 216.87 | 7.4.9.Final |

| Operation | GuicedEE p50 (ms) | p95 | p99 | Quarkus p50 (ms) | p95 | p99 | GuicedEE p50 difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Joined graph read | 2.61 | 75.61 | 86.26 | 2.50 | 62.97 | 77.50 | +4.4% |
| Create 15 rows | 7.87 | 97.06 | 104.30 | 8.07 | 81.62 | 95.19 | -2.4% |
| Update 15 rows | 8.22 | 95.74 | 97.07 | 8.69 | 84.65 | 91.77 | -5.3% |
| Delete 15 rows | 7.83 | 94.45 | 98.12 | 7.85 | 78.66 | 90.19 | -0.3% |
| Complete CRUD cycle | 93.84 | 199.38 | 205.80 | 85.22 | 174.82 | 197.40 | +10.1% |

Per-start warm medians expose the variation within this small, CPU-capped cohort. No individual start is dropped.

| Application | Start | Read p50 (ms) | Create p50 (ms) | Update p50 (ms) | Delete p50 (ms) | CRUD cycle p50 (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE reactive stateless | 1 | 2.55 | 7.87 | 8.21 | 7.82 | 92.87 |
| Quarkus ORM / Narayana | 1 | 2.71 | 8.35 | 9.95 | 8.03 | 89.99 |
| Quarkus ORM / Narayana | 2 | 2.50 | 7.30 | 8.11 | 7.85 | 85.22 |
| GuicedEE reactive stateless | 2 | 2.61 | 8.18 | 9.10 | 8.13 | 98.68 |
| GuicedEE reactive stateless | 3 | 2.73 | 7.64 | 8.22 | 7.83 | 93.84 |
| Quarkus ORM / Narayana | 3 | 2.44 | 8.07 | 8.69 | 7.44 | 83.99 |

Update p50 spans **8.21–9.10 ms** for GuicedEE and **8.11–9.95 ms** for Quarkus across starts. Every container records CPU throttling; these measurements do not separate database work from quota waits. Individual operation medians do not add up to the median of a complete CRUD cycle.

GuicedEE's launch-to-commit median differs by **+38.7%**; its peak charged container memory differs by **+12.3%**. Negative differences mean less time or memory. Warm percentiles are medians of per-start percentiles. A CRUD cycle includes four HTTP requests, three completed write transactions and one read without an explicit transaction; its latency is not one transaction. Database memory is separate from the application memory figures.

Both full-JDK applications use the same immutable JDK base, schema, graph/query source and five-connection limit. The database runs separately at 2 CPU / 1 GiB with durable commit settings. Application limits are 250m CPU / 500 MiB. These are different persistence patterns: managed stateful JPA/Narayana versus explicit reactive stateless operations. This is not a distributed-transaction, saturation-throughput, native or jlink result.

[Protocol and reproduction](persistence/README.md) · [All current raw samples](results/latest/persistence.json) · [CSV](docs/persistence-performance.csv) · [Separate diagnostic profile](docs/PERSISTENCE_PROFILE.md)

| Application | Immutable image |
| --- | ---: |
| GuicedEE reactive stateless | `sha256:722fd5790181982ec46e64ee6394063fc8c214ffe09946bec619ca2169b0c6b2` |
| Quarkus ORM / Narayana | `sha256:808c8da5d2b6f3a44f04b0519765ae570a0326391635330d03736e5986e7a1ad` |

PostgreSQL image: `sha256:0d938e975177bef9f1f61f3f9dbcf2e0aa0a139568f66d3415ed8892eb97f6ac`. JDK base: `eclipse-temurin@sha256:b8705e936964c228dfce359e63dbf08f6c69cb380ed1d576b1f6b1064f15567d`.
<!-- END GENERATED: persistence -->

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
| native-standard | GuicedEE SPI / native | `sha256:cba41d26ee568443fc067010e607b07b6ddc858fd47599402d0190fd9fb96132` |
| native-standard | Quarkus upstream SDKs / native | `sha256:32153f649fea73fc6143645f48a1c3969851a318903d308a32a7b3876869ec69` |
| jvm-default | GuicedEE SPI / full JDK | `sha256:81dc069a9833e36a6767e252c9b8a7a3ba611f179b203bf73a833a650a3bdbbd` |
| jvm-default | GuicedEE scanner / full JDK | `sha256:b08deee9eafc7e07bb6b5d388f1c873c02ae583be7830cfc4cb4ae069672f008` |
| jvm-default | Quarkus upstream SDKs / fast-JAR | `sha256:ff1c796950c84a86c8bc4f833fb17794bf4d4343ab52b98b51ffc0df436d45a8` |
| jvm-default | GuicedEE SPI / application jlink | `sha256:328a1e99248b71d99fb4769f9bd477bc9171a09a01d7e7b6c44caa2fd4e0ce6a` |
| jvm-default | GuicedEE scanner / application jlink | `sha256:c394e88f41189cf0a60fa87df2bd83b41a88ced213c798401834357e208f557a` |
| jvm-c1 | GuicedEE SPI / full JDK | `sha256:81dc069a9833e36a6767e252c9b8a7a3ba611f179b203bf73a833a650a3bdbbd` |
| jvm-c1 | GuicedEE scanner / full JDK | `sha256:b08deee9eafc7e07bb6b5d388f1c873c02ae583be7830cfc4cb4ae069672f008` |
| jvm-c1 | Quarkus upstream SDKs / fast-JAR | `sha256:ff1c796950c84a86c8bc4f833fb17794bf4d4343ab52b98b51ffc0df436d45a8` |
| jvm-c1 | GuicedEE SPI / application jlink | `sha256:328a1e99248b71d99fb4769f9bd477bc9171a09a01d7e7b6c44caa2fd4e0ce6a` |
| jvm-c1 | GuicedEE scanner / application jlink | `sha256:c394e88f41189cf0a60fa87df2bd83b41a88ced213c798401834357e208f557a` |
| native-extended | GuicedEE SPI / native | `sha256:cba41d26ee568443fc067010e607b07b6ddc858fd47599402d0190fd9fb96132` |
| native-extended | Quarkus upstream SDKs / native | `sha256:32153f649fea73fc6143645f48a1c3969851a318903d308a32a7b3876869ec69` |
<!-- END GENERATED: image-identities -->
