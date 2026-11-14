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

## All execution modes

Values are median launch to completed business response in seconds. The default and C1
matrices measure the same seven immutable images. The primary native-only comparison has
a larger counterbalanced sample. Full grids retain every start and measured request.

<!-- BEGIN GENERATED: overview -->
| Application | Full JDK default (s) | Full JDK C1 (s) | Application jlink default (s) | Application jlink C1 (s) | Native (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI | [28.177](RESULTS.md#jvm-default) | [16.746](RESULTS.md#jvm-c1) | [15.138](RESULTS.md#jvm-default) | [7.938](RESULTS.md#jvm-c1) | [0.657](RESULTS.md#native-standard) |
| GuicedEE scanner | [27.831](RESULTS.md#jvm-default) | [17.431](RESULTS.md#jvm-c1) | [14.155](RESULTS.md#jvm-default) | [8.387](RESULTS.md#jvm-c1) | SPI only |
| Quarkus / upstream SDKs | [24.074](RESULTS.md#jvm-default) | [14.168](RESULTS.md#jvm-c1) | Not implemented | Not implemented | [0.684](RESULTS.md#native-standard) |
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
Displayed rows: **21 starts / 315 passing checks / 630 successful measured requests**. Each start: 10 warmups, 30 measured requests. Batch IDs in [latest measurements](results/latest/measurements.json): `20261115-003904`.

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3 | 9.202 | 19,609.51 | 28.177 | 28.167–29.408 | 199.95 |
| GuicedEE scanner / full JDK | 3 | 9.320 | 18,396.49 | 27.831 | 27.717–29.153 | 94.88 |
| Quarkus upstream SDKs / fast-JAR | 3 | 6.856 | 16,696.91 | 24.074 | 23.165–24.135 | 406.22 |
| GuicedEE SPI / application jlink | 3 | 8.355 | 6,609.92 | 15.138 | 14.082–15.634 | 185.08 |
| GuicedEE scanner / application jlink | 3 | 7.919 | 6,292.14 | 14.155 | 13.513–14.816 | 192.01 |
| GuicedEE SPI / native | 3 | 0.572 | 78.99 | 0.653 | 0.644–0.676 | 3.80 |
| Quarkus upstream SDKs / native | 3 | 0.580 | 118.32 | 0.704 | 0.682–0.731 | 1.99 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 90.82 | 99.54 | 99.74 | 294.89 | 289.29–376.50 | 290.98 |
| GuicedEE scanner / full JDK | 92.55 | 100.41 | 102.65 | 306.52 | 293.48–379.23 | 302.56 |
| Quarkus upstream SDKs / fast-JAR | 91.15 | 99.77 | 101.38 | 278.01 | 274.36–343.62 | 274.67 |
| GuicedEE SPI / application jlink | 92.63 | 103.13 | 163.71 | 241.35 | 238.33–244.37 | 237.70 |
| GuicedEE scanner / application jlink | 90.92 | 99.77 | 101.15 | 235.72 | 232.80–248.47 | 232.06 |
| GuicedEE SPI / native | 6.05 | 20.36 | 27.73 | 79.34 | 79.32–79.44 | 76.04 |
| Quarkus upstream SDKs / native | 5.06 | 24.98 | 26.23 | 55.26 | 55.15–55.38 | 51.85 |
<!-- END GENERATED: jvm-default -->

<a id="jvm-c1"></a>
## Full matched matrix: equal C1 JVM tuning

These are the **same immutable images** as the default matrix, with C1 applied equally to
all JVMs. Quarkus native is repeated as a batch reference using the same binary and no JIT flag.

<!-- BEGIN GENERATED: jvm-c1 -->
Displayed rows: **21 starts / 315 passing checks / 630 successful measured requests**. Each start: 10 warmups, 30 measured requests. Batch IDs in [latest measurements](results/latest/measurements.json): `20261115-004632`.

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3 | 5.330 | 11,416.28 | 16.746 | 16.657–17.737 | 23.96 |
| GuicedEE scanner / full JDK | 3 | 5.419 | 11,901.74 | 17.431 | 17.093–17.575 | 10.04 |
| Quarkus upstream SDKs / fast-JAR | 3 | 3.869 | 10,311.20 | 14.168 | 13.875–14.572 | 217.44 |
| GuicedEE SPI / application jlink | 3 | 4.848 | 3,177.72 | 7.938 | 7.665–8.126 | 21.95 |
| GuicedEE scanner / application jlink | 3 | 4.947 | 3,197.93 | 8.387 | 8.051–8.495 | 84.68 |
| GuicedEE SPI / native | 3 | 0.568 | 71.20 | 0.638 | 0.638–0.657 | 3.53 |
| Quarkus upstream SDKs / native | 3 | 0.572 | 100.81 | 0.673 | 0.642–0.689 | 2.07 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 22.24 | 91.60 | 92.04 | 260.93 | 260.30–261.72 | 257.57 |
| GuicedEE scanner / full JDK | 48.32 | 92.01 | 93.19 | 263.72 | 262.31–263.81 | 259.80 |
| Quarkus upstream SDKs / fast-JAR | 13.07 | 89.73 | 92.25 | 240.52 | 239.52–242.63 | 237.42 |
| GuicedEE SPI / application jlink | 27.08 | 92.50 | 93.44 | 188.05 | 187.40–188.50 | 184.45 |
| GuicedEE scanner / application jlink | 31.71 | 89.40 | 92.13 | 191.25 | 190.69–191.46 | 187.82 |
| GuicedEE SPI / native | 5.01 | 22.75 | 26.66 | 79.30 | 79.09–80.07 | 75.96 |
| Quarkus upstream SDKs / native | 4.91 | 19.82 | 27.41 | 55.50 | 55.02–56.04 | 52.04 |
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
| jvm-default | GuicedEE SPI / full JDK | JVM | +34.2% | +17.0% | -0.4% | -0.2% | +6.1% |
| jvm-default | GuicedEE scanner / full JDK | JVM | +35.9% | +15.6% | +1.5% | +0.6% | +10.3% |
| jvm-default | GuicedEE SPI / application jlink | JVM | +21.9% | -37.1% | +1.6% | +3.4% | -13.2% |
| jvm-default | GuicedEE scanner / application jlink | JVM | +15.5% | -41.2% | -0.3% | +0.0% | -15.2% |
| jvm-default | GuicedEE SPI / native | Native | -1.2% | -7.3% | +19.6% | -18.5% | +43.6% |
| jvm-c1 | GuicedEE SPI / full JDK | JVM | +37.8% | +18.2% | +70.2% | +2.1% | +8.5% |
| jvm-c1 | GuicedEE scanner / full JDK | JVM | +40.1% | +23.0% | +269.9% | +2.5% | +9.6% |
| jvm-c1 | GuicedEE SPI / application jlink | JVM | +25.3% | -44.0% | +107.3% | +3.1% | -21.8% |
| jvm-c1 | GuicedEE scanner / application jlink | JVM | +27.9% | -40.8% | +142.7% | -0.4% | -20.5% |
| jvm-c1 | GuicedEE SPI / native | Native | -0.7% | -5.3% | +2.1% | +14.8% | +42.9% |
<!-- END GENERATED: relative -->

<!-- BEGIN GENERATED: findings -->
**Default JVM:** linked SPI/scanner complete the first business response in **15.138/14.155 s**, versus **24.074 s** for Quarkus JVM. SPI jlink uses **37.1% less time**. The separate readiness and first-request columns show where that difference occurs.

**C1 JVM:** linked SPI/scanner complete the first business response in **7.938/8.387 s**, versus **14.168 s** for Quarkus JVM. SPI jlink uses **44.0% less time**. The separate readiness and first-request columns show where that difference occurs.
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
| GuicedEE SPI / full JDK | jvm-default | 1,003.74 | — | `7412efd0dc63` |
| GuicedEE scanner / full JDK | jvm-default | 1,003.73 | — | `76668c563592` |
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
| jvm-default | GuicedEE SPI / full JDK | `sha256:7412efd0dc63066789101b2323b6111f225a8146d80b804a8d603787eb09db1b` |
| jvm-default | GuicedEE scanner / full JDK | `sha256:76668c56359263c7e7a003c58108a8fe7b9b6a8328cad1a1f9090781827b5257` |
| jvm-default | Quarkus upstream SDKs / fast-JAR | `sha256:ff1c796950c84a86c8bc4f833fb17794bf4d4343ab52b98b51ffc0df436d45a8` |
| jvm-default | GuicedEE SPI / application jlink | `sha256:867a886a5d8cf020d5d9320b93d521acf995535480c7f18d259620f031d7f86a` |
| jvm-default | GuicedEE scanner / application jlink | `sha256:b8ea0ab4aef0522b489a9ab6e42a4944a996758f813c5395c4c66af4703df2ac` |
| jvm-default | GuicedEE SPI / native | `sha256:79b8987c62a9eee01a6592332310c714031d75c986a98319a5f77ae9dcdb0868` |
| jvm-default | Quarkus upstream SDKs / native | `sha256:32153f649fea73fc6143645f48a1c3969851a318903d308a32a7b3876869ec69` |
| jvm-c1 | GuicedEE SPI / full JDK | `sha256:7412efd0dc63066789101b2323b6111f225a8146d80b804a8d603787eb09db1b` |
| jvm-c1 | GuicedEE scanner / full JDK | `sha256:76668c56359263c7e7a003c58108a8fe7b9b6a8328cad1a1f9090781827b5257` |
| jvm-c1 | Quarkus upstream SDKs / fast-JAR | `sha256:ff1c796950c84a86c8bc4f833fb17794bf4d4343ab52b98b51ffc0df436d45a8` |
| jvm-c1 | GuicedEE SPI / application jlink | `sha256:867a886a5d8cf020d5d9320b93d521acf995535480c7f18d259620f031d7f86a` |
| jvm-c1 | GuicedEE scanner / application jlink | `sha256:b8ea0ab4aef0522b489a9ab6e42a4944a996758f813c5395c4c66af4703df2ac` |
| jvm-c1 | GuicedEE SPI / native | `sha256:79b8987c62a9eee01a6592332310c714031d75c986a98319a5f77ae9dcdb0868` |
| jvm-c1 | Quarkus upstream SDKs / native | `sha256:32153f649fea73fc6143645f48a1c3969851a318903d308a32a7b3876869ec69` |
<!-- END GENERATED: image-identities -->
