# Current performance state

**Measured: 14 November 2026. Compiled: 15 November 2026.** All tables below are generated
from retained samples. No measurements were rerun for this reporting change.

GuicedEE native has the lower median full-business startup and warm p50 in the current
comparison against normal-dependency Quarkus native. Quarkus has the smaller executable,
container image and peak container memory. The JVM matrix shows a different tradeoff:
Quarkus fast-JAR reaches HTTP readiness sooner, while application-linked GuicedEE completes
the cold SDK/Firestore business request sooner than Quarkus JVM.

## Mode coverage at a glance

Values are **median launch-to-full-business completion in seconds**. Cells link to the
complete comparable group, including ranges, warm percentiles and memory. The cells span
different image revisions and must not be treated as a single matched experiment.

<!-- BEGIN GENERATED: overview -->
| Application / dependencies | Full JDK default (s) | Full JDK C1 (s) | Application jlink default (s) | Application jlink C1 (s) | Native (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / wrapped SDKs | [31.019](RESULTS.md#jvm-default) | [18.546](RESULTS.md#jvm-c1) | [13.745](RESULTS.md#jlink-default) | [8.781](RESULTS.md#jvm-c1) | [0.668](RESULTS.md#native-standard) primary; [0.659](RESULTS.md#native-wrapped) control |
| GuicedEE scanner / wrapped SDKs | [32.975](RESULTS.md#jvm-default) | [19.432](RESULTS.md#jvm-c1) | [13.987](RESULTS.md#jlink-default) | [8.854](RESULTS.md#jvm-c1) | Unsupported |
| Quarkus / upstream SDKs | Diagnostic only | Unmeasured | No variant | No variant | [0.706](RESULTS.md#native-standard) |
| Quarkus / wrapped SDKs (control) | [30.026](RESULTS.md#jvm-default) | [17.812](RESULTS.md#jvm-c1) | No variant | No variant | [0.655](RESULTS.md#native-wrapped) |
<!-- END GENERATED: overview -->

“Diagnostic only” means functional/phase evidence exists but no eligible repeated performance
measurement. “Unmeasured” means no applicable result. “No variant” means the harness does not
provide that execution mode. Scanner discovery is unsupported by this native integration.
The `jre` CLI name selects the full-JDK JVM baseline; jlink embeds the GuicedEE application
and its named-module graph. A trimmed JDK around Quarkus fast-JAR is not application jlink.

Read the [native comparison](#native-standard), [default JVM matrix](#jvm-default),
[C1 matrix](#jvm-c1), [latest linked images](#jlink-default), [wrapped-SDK native control](#native-wrapped),
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
validation, all 15 capability checks and all measured requests must pass. Raw failures remain
in the archive. All image identities appear in the [identity grid](#image-identities).

The measured GuicedEE artifacts are local 2.5.1 builds containing development changes.
Further framework/SDK work in 2.6.0 is **not measured by these tables**. Recorded image IDs
and artifact hashes define the measured implementation, not a Maven version alone.

<a id="native-standard"></a>
## Native: normal Quarkus dependencies

This is the primary application comparison: GuicedEE SPI native versus Quarkus with upstream
commercetools 20.4.0, Firebase Admin 9.12.0, Quarkus 3.40.1 and Quarkiverse Firebase/Firestore
2.25.1. Quarkus has no GuicedEE SDK wrappers or framework patches. Native compatibility
metadata and application configuration are described in [the project](quarkus-standard/README.md).
Business sources match; dependency packaging and transitive graphs deliberately differ.

The two batches reverse their initial framework order and use identical image IDs and flags.

<!-- BEGIN GENERATED: native-standard -->
Displayed rows: **28 starts / 420 passing checks / 840 successful measured requests**. Each start: 10 warmups, 30 measured requests. Evidence: [20261114-231729](results/20261114-231729/summary.json), [20261114-231959](results/20261114-231959/summary.json).

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | 14 | 0.582 | 86.44 | 0.668 | 0.585–1.025 | 3.55 |
| Quarkus upstream SDKs / native | 14 | 0.577 | 129.03 | 0.706 | 0.671–1.024 | 2.22 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | 5.18 | 27.20 | 29.53 | 79.58 | 79.07–80.76 | 76.33 |
| Quarkus upstream SDKs / native | 6.02 | 26.86 | 31.55 | 55.33 | 54.76–56.50 | 51.78 |
<!-- END GENERATED: native-standard -->

<!-- BEGIN GENERATED: native-deltas -->
| Metric | GuicedEE native | Quarkus upstream native | GuicedEE difference |
| --- | ---: | ---: | ---: |
| Full-business startup | 667.84 ms | 705.75 ms | -5.4% |
| First business request | 86.44 ms | 129.03 ms | -33.0% |
| Warm p50 | 5.18 ms | 6.02 ms | -14.0% |
| Warm p95 | 27.20 ms | 26.86 ms | +1.3% |
| Warm p99 | 29.53 ms | 31.55 ms | -6.4% |
| Peak container memory | 79.58 MiB | 55.33 MiB | +43.8% |
| Executable size | 191.83 MiB | 143.31 MiB | +33.9% |
| Docker local image size | 421.17 MiB | 353.04 MiB | +19.3% |
<!-- END GENERATED: native-deltas -->

Negative differences mean GuicedEE uses less time or space. The full-business median lead
appears in both batches (667/705 ms and 679/707 ms). The 5 ms readiness difference is below
the polling interval. Warm p95 slightly favors Quarkus; the small p99 difference does not
establish a general tail-latency advantage. The first process in each batch takes roughly
1.025 seconds, whichever framework runs first. That is consistent with shared fixture
first-use cost, but its cause is not isolated. Those starts remain included.

The tradeoff is concrete: **5.4% lower median startup and 14.0% lower warm p50**, at
**43.8% more peak charged memory and 33.9% more executable bytes**. Whether that footprint
cost is acceptable depends on deployment density and latency goals. There is no
statistical-confidence or universal-framework claim from these sequential samples.

<a id="jvm-default"></a>
<a id="current-linux-native-comparison"></a>
## Full matched matrix: default JVMs

This is the latest complete matched JVM/jlink matrix, with a Quarkus native reference.
All Quarkus rows here use **GuicedEE's wrapped SDKs**. These image revisions predate the
latest linked OpenAPI and native footprint revisions; the complete table is retained so
every mode is compared within its measured group. It is not normal-dependency Quarkus JVM.

<!-- BEGIN GENERATED: jvm-default -->
Displayed rows: **18 starts / 270 passing checks / 540 successful measured requests**. Each start: 10 warmups, 30 measured requests. Evidence: [20261114-154043](results/20261114-154043/summary.json).

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3 | 10.438 | 22,197.68 | 31.019 | 30.635–33.333 | — |
| GuicedEE scanner / full JDK | 3 | 11.037 | 21,796.53 | 32.975 | 32.530–33.924 | — |
| Quarkus wrapped SDKs / fast-JAR | 3 | 7.014 | 23,201.17 | 30.026 | 29.018–31.927 | — |
| GuicedEE SPI / application jlink | 3 | 8.960 | 6,300.87 | 15.261 | 15.112–16.251 | — |
| GuicedEE scanner / application jlink | 3 | 8.910 | 6,114.24 | 15.673 | 15.025–15.752 | — |
| Quarkus wrapped SDKs / native | 3 | 0.586 | 147.93 | 0.737 | 0.699–0.755 | — |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 95.94 | 105.25 | 190.61 | 298.44 | 291.44–301.42 | 295.17 |
| GuicedEE scanner / full JDK | 94.26 | 107.74 | 185.75 | 297.19 | 295.91–300.29 | 293.31 |
| Quarkus wrapped SDKs / fast-JAR | 97.07 | 102.59 | 103.42 | 298.14 | 297.30–298.93 | 294.52 |
| GuicedEE SPI / application jlink | 95.46 | 103.31 | 104.73 | 223.07 | 217.59–247.62 | 219.64 |
| GuicedEE scanner / application jlink | 95.19 | 107.03 | 187.65 | 226.30 | 222.26–228.36 | 220.55 |
| Quarkus wrapped SDKs / native | 4.97 | 26.27 | 30.19 | 58.92 | 58.81–59.09 | 55.75 |
<!-- END GENERATED: jvm-default -->

GuicedEE SPI jlink completes full startup in about half the Quarkus JVM time (15.261 versus
30.026 seconds, **49.2% less**), although Quarkus reaches HTTP readiness earlier. Full-JDK
GuicedEE SPI and scanner take longer than Quarkus JVM to complete the first business request.
The linked runtime changes the cold business path substantially; readiness alone misses that
effect. Small differences between SPI and scanner are not reliable causal estimates from
three starts. Native is a different compilation strategy and is much faster in this matrix.

<a id="jvm-c1"></a>
## Full matched matrix: equal C1 JVM tuning

These are the **same immutable images** as the default matrix, with C1 applied equally to
all JVMs. Quarkus native is repeated as a batch reference using the same binary and no JIT flag.

<!-- BEGIN GENERATED: jvm-c1 -->
Displayed rows: **18 starts / 270 passing checks / 540 successful measured requests**. Each start: 10 warmups, 30 measured requests. Evidence: [20261114-154849](results/20261114-154849/summary.json).

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 3 | 5.573 | 12,979.19 | 18.546 | 17.983–19.171 | — |
| GuicedEE scanner / full JDK | 3 | 6.011 | 13,297.13 | 19.432 | 18.318–19.810 | — |
| Quarkus wrapped SDKs / fast-JAR | 3 | 4.162 | 13,619.44 | 17.812 | 17.668–17.884 | — |
| GuicedEE SPI / application jlink | 3 | 5.352 | 3,294.31 | 8.781 | 8.348–8.851 | — |
| GuicedEE scanner / application jlink | 3 | 5.450 | 3,402.85 | 8.854 | 8.834–9.147 | — |
| Quarkus wrapped SDKs / native | 3 | 0.580 | 120.34 | 0.701 | 0.658–0.778 | — |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / full JDK | 86.97 | 96.40 | 99.38 | 259.33 | 257.54–260.23 | 255.79 |
| GuicedEE scanner / full JDK | 79.31 | 94.72 | 96.33 | 262.58 | 261.16–263.99 | 259.43 |
| Quarkus wrapped SDKs / fast-JAR | 66.86 | 94.70 | 95.52 | 259.68 | 259.59–260.45 | 256.80 |
| GuicedEE SPI / application jlink | 77.54 | 94.12 | 95.34 | 188.84 | 188.83–189.23 | 185.41 |
| GuicedEE scanner / application jlink | 70.35 | 93.66 | 94.80 | 192.32 | 191.79–192.81 | 188.96 |
| Quarkus wrapped SDKs / native | 4.39 | 20.91 | 28.32 | 59.17 | 59.03–60.04 | 55.73 |
<!-- END GENERATED: jvm-c1 -->

C1 reduces full-business startup to **8.781/8.854 seconds** for linked SPI/scanner and
**17.812 seconds** for Quarkus JVM. SPI jlink is **50.7% lower** than Quarkus JVM within
this group. Compared with each variant's default-JVM batch, startup falls about 40–44%.
Those cross-batch changes describe the recorded profiles; they do not predict sustained
throughput, which this workload does not measure. No normal-dependency Quarkus C1 run exists.

<a id="jlink-default"></a>
## Latest measured linked images: default JVM

These are the complete final-image rows from the controlled linked-image batch, with eager
OpenAPI generation enabled. Both discovery variants pass the full capability gate. The batch
also contains original-image controls; those remain in raw evidence and the
[detailed investigation](OPENAPI_OPTIMIZATION.md). No individual starts were selected or removed.
There is no corresponding Quarkus row or C1 measurement for these linked-image revisions.

<!-- BEGIN GENERATED: jlink-default -->
Displayed rows: **6 starts / 90 passing checks / 30 successful measured requests**. Each start: 2 warmups, 5 measured requests. Evidence: [20261114-200551](results/20261114-200551/summary.json).

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / application jlink | 3 | 7.661 | 6,198.79 | 13.745 | 13.666–13.860 | 103.33 |
| GuicedEE scanner / application jlink | 3 | 8.037 | 5,893.37 | 13.987 | 13.611–14.037 | 190.87 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / application jlink | 94.16 | 94.93 | 94.93 | 235.66 | 220.04–241.87 | 232.17 |
| GuicedEE scanner / application jlink | 93.33 | 95.30 | 95.30 | 233.90 | 231.74–235.14 | 230.10 |
<!-- END GENERATED: jlink-default -->

SPI and scanning now have recorded full-business medians of **13.745/13.987 seconds** and
readiness medians of **7.661/8.037 seconds**. This group has only five measured warm requests
per start; its warm tail percentiles are especially coarse and must not be ranked against
the 30-request JVM/native groups. The first OpenAPI response is also not the first business response.

<a id="native-wrapped"></a>
## Native control: the same wrapped SDKs

This group compares the final native images with the same GuicedEE-repackaged SDK inputs on
both frameworks. It answers a different question from the upstream-dependency comparison.
All final-image starts from the paired experiment are shown; original-image controls remain
in the retained batch and [detailed audit](NATIVE_OPTIMIZATION.md).

<!-- BEGIN GENERATED: native-wrapped -->
Displayed rows: **14 starts / 210 passing checks / 420 successful measured requests**. Each start: 10 warmups, 30 measured requests. Evidence: [20261114-222751](results/20261114-222751/summary.json).

| Variant | Starts | Ready (s) | First request (ms) | Full business (s) | Full business min–max (s) | First OpenAPI (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | 7 | 0.576 | 75.17 | 0.659 | 0.635–0.701 | 4.18 |
| Quarkus wrapped SDKs / native | 7 | 0.572 | 85.84 | 0.655 | 0.648–0.714 | 2.13 |

| Variant | Warm p50 (ms) | Warm p95 (ms) | Warm p99 (ms) | Peak memory median (MiB) | Peak memory min–max (MiB) | End memory median (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | 4.31 | 25.23 | 30.71 | 79.98 | 79.29–80.66 | 76.50 |
| Quarkus wrapped SDKs / native | 4.47 | 29.02 | 31.92 | 62.75 | 62.12–63.52 | 59.13 |
<!-- END GENERATED: native-wrapped -->

Full-business startup is effectively tied at **659/655 ms** in this sample. This reinforces
why the upstream-dependency and identical-wrapper experiments must remain distinct. A
38 ms median lead against upstream Quarkus is not evidence of the same lead against every
Quarkus dependency arrangement.

<a id="local-windows"></a>
## Local Windows profile

These are unrestricted-host, default-tiered JVM runs of the four GuicedEE modes. There is
**no 250m CPU quota, no 500 MiB container limit and no Quarkus row**. They establish the
local mode timings and functional coverage only; they cannot rank against Docker results.
Container memory, image size and OpenAPI request timing were not recorded in this batch.

<!-- BEGIN GENERATED: local-windows -->
Displayed rows: **12 starts / 180 passing checks / 1200 successful measured requests**. Each start: 20 warmups, 100 measured requests. Evidence: [20261114-124721](results/20261114-124721/summary.json).

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

Image rows below retain the exact measurement group because the complete matrix and later
linked/native groups use different binaries. Repeated names are different measured revisions.
Runtime memory is in the performance grids above; it is not the same quantity as disk size.

<!-- BEGIN GENERATED: packaging -->
| Variant | Evidence group | Docker local image (MiB) | Executable (MiB) | Image ID prefix |
| --- | ---: | ---: | ---: | ---: |
| GuicedEE SPI / native | native-standard | 421.17 | 191.83 | `79b8987c62a9` |
| Quarkus upstream SDKs / native | native-standard | 353.04 | 143.31 | `32153f649fea` |
| GuicedEE SPI / application jlink | jlink-default | 473.29 | — | `867a886a5d8c` |
| GuicedEE scanner / application jlink | jlink-default | 473.43 | — | `b8ea0ab4aef0` |
| GuicedEE SPI / full JDK | jvm-default | 1,003.74 | — | `7412efd0dc63` |
| GuicedEE scanner / full JDK | jvm-default | 1,003.73 | — | `76668c563592` |
| Quarkus wrapped SDKs / fast-JAR | jvm-default | 993.61 | — | `c09d28025946` |
| GuicedEE SPI / application jlink | jvm-default | 473.22 | — | `9d6f137227e1` |
| GuicedEE scanner / application jlink | jvm-default | 473.35 | — | `f28c2400c6c6` |
| Quarkus wrapped SDKs / native | jvm-default | 395.23 | 174.81 | `c3928e04b0e4` |
| GuicedEE SPI / native | native-wrapped | 421.17 | 191.83 | `79b8987c62a9` |
| Quarkus wrapped SDKs / native | native-wrapped | 374.96 | 158.01 | `dcd3fbe00102` |
<!-- END GENERATED: packaging -->

The linked-runtime audit applies specifically to the images in the full JVM matrix:

<!-- BEGIN GENERATED: jlink-size -->
| Measured jlink payload | SPI | Scanner |
| --- | ---: | ---: |
| Runtime including application (MiB) | 168.83 | 168.90 |
| Module image (MiB) | 135.16 | 135.23 |
| Unpacked Docker layers (MiB) | 286.18 | 286.24 |
| Installed modules | 107 | 107 |
| Mandatory module closure | 96 | 96 |
| Closure including installed service providers | 101 | 101 |
<!-- END GENERATED: jlink-size -->

The roughly 473 MiB Docker-store value contains a **169 MiB linked application runtime**.
The graph is valid but not minimal: 107 installed modules versus 96 in the mandatory closure
and 101 when resolving providers already present. The two SDK wrappers contribute **82.01 MiB**
of stored module resources. The six modules outside the service-bound closure account for
only **0.62 MiB**; they do not explain the bulk of the image. These are measured contents,
not demonstrated savings from deleting them. [Full module/byte audit](JLINK_AUDIT.md).

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
| SPI jlink | 3 | [20261114-200341](results/20261114-200341/summary.json) | `867a886a5d8c` |
| Scanner jlink | 3 | [20261114-200341](results/20261114-200341/summary.json) | `b8ea0ab4aef0` |
| Quarkus wrapped JVM | 3 | [20261114-192928](results/20261114-192928/summary.json) | `8bb83742f618` |
| Quarkus upstream JVM | 1 | [20261114-231541](results/20261114-231541/summary.json) | `ff1c796950c8` |
| GuicedEE native | 2 | [20261114-221910](results/20261114-221910/summary.json) | `1fa99f53daf7` |
| Quarkus upstream native | 1 | [20261114-231325](results/20261114-231325/summary.json) | `a7c4d1a26a04` |
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

| Missing measurement | Current status |
|---|---|
| One current-build JVM/jlink/native matrix with normal Quarkus dependencies | Not available; latest groups above are explicitly separated |
| Normal-dependency Quarkus JVM default/C1 | One passing instrumented JVM capability run; no eligible repeated timing batch |
| Updated linked-image C1 profile | No measurement for that image revision |
| GuicedEE scanner native / Quarkus application jlink | No supported harness variant |
| Final GuicedEE 2.6.0 artifacts | No release performance matrix |
| Sustained load, concurrency scaling, throughput and allocation rate | Not measured by these sequential service runs |
| Production WAN/TLS, authentication, telemetry, Secret Manager, cancellation and other SDK products | Outside the current capability contract |
| Core JMH measurements | No reproducible core JMH source/results set in this repository |

## Reproduce and verify the report

[RUNNING.md](RUNNING.md) documents the applications, flags, build commands, fixtures and
configuration. Rebuilds with different framework/SDK inputs require new measurements; the
historical local Maven cache and executable images are not distributed in this Git repository.

From the benchmark repository root:

```powershell
python tools/render_performance.py --check
python tools/verify_retained_evidence.py
python -m unittest discover -s tools -p test_harness.py
```

The renderer validates complete variant/start matrices, capability/sample success, container
quotas and image identities before calculating tables. It reads all starts of the explicitly
named variants. Update its group selection deliberately when retaining a new matched run,
then run it without `--check` to refresh the grids. Raw evidence is never rewritten.

[JSON statistics and input hashes](docs/current-performance.json) and [CSV](docs/current-performance.csv)
provide the unrounded values. [Earlier ledgers and investigations](docs/history/README.md)
remain available for provenance; they are not the entry point for current performance.

<a id="image-identities"></a>
## Immutable image identities

Each group's linked `environment.json` also records artifact hashes, source snapshots and flags.
The same image can legitimately appear in more than one profile or dependency experiment.

<!-- BEGIN GENERATED: image-identities -->
| Group | Variant | Immutable Docker image ID |
| --- | ---: | ---: |
| native-standard | GuicedEE SPI / native | `sha256:79b8987c62a9eee01a6592332310c714031d75c986a98319a5f77ae9dcdb0868` |
| native-standard | Quarkus upstream SDKs / native | `sha256:32153f649fea73fc6143645f48a1c3969851a318903d308a32a7b3876869ec69` |
| jvm-default | GuicedEE SPI / full JDK | `sha256:7412efd0dc63066789101b2323b6111f225a8146d80b804a8d603787eb09db1b` |
| jvm-default | GuicedEE scanner / full JDK | `sha256:76668c56359263c7e7a003c58108a8fe7b9b6a8328cad1a1f9090781827b5257` |
| jvm-default | Quarkus wrapped SDKs / fast-JAR | `sha256:c09d2802594658a7fbbe57a72f891d0b8c65e4c493857e578a2346da7199e097` |
| jvm-default | GuicedEE SPI / application jlink | `sha256:9d6f137227e1127c83ce7bb01ebf94167ddb0a721962767cc911e5e7aa8f0c4a` |
| jvm-default | GuicedEE scanner / application jlink | `sha256:f28c2400c6c6af8b7d5117c9657a24289a1e17f3e88cdf4a32c2b5d3cb3e1629` |
| jvm-default | Quarkus wrapped SDKs / native | `sha256:c3928e04b0e4d53f84c4755a10cb71b837806387db509cac6ef99ca2711c109d` |
| jvm-c1 | GuicedEE SPI / full JDK | `sha256:7412efd0dc63066789101b2323b6111f225a8146d80b804a8d603787eb09db1b` |
| jvm-c1 | GuicedEE scanner / full JDK | `sha256:76668c56359263c7e7a003c58108a8fe7b9b6a8328cad1a1f9090781827b5257` |
| jvm-c1 | Quarkus wrapped SDKs / fast-JAR | `sha256:c09d2802594658a7fbbe57a72f891d0b8c65e4c493857e578a2346da7199e097` |
| jvm-c1 | GuicedEE SPI / application jlink | `sha256:9d6f137227e1127c83ce7bb01ebf94167ddb0a721962767cc911e5e7aa8f0c4a` |
| jvm-c1 | GuicedEE scanner / application jlink | `sha256:f28c2400c6c6af8b7d5117c9657a24289a1e17f3e88cdf4a32c2b5d3cb3e1629` |
| jvm-c1 | Quarkus wrapped SDKs / native | `sha256:c3928e04b0e4d53f84c4755a10cb71b837806387db509cac6ef99ca2711c109d` |
| jlink-default | GuicedEE SPI / application jlink | `sha256:867a886a5d8cf020d5d9320b93d521acf995535480c7f18d259620f031d7f86a` |
| jlink-default | GuicedEE scanner / application jlink | `sha256:b8ea0ab4aef0522b489a9ab6e42a4944a996758f813c5395c4c66af4703df2ac` |
| native-wrapped | GuicedEE SPI / native | `sha256:79b8987c62a9eee01a6592332310c714031d75c986a98319a5f77ae9dcdb0868` |
| native-wrapped | Quarkus wrapped SDKs / native | `sha256:dcd3fbe001026fccac0606fd7fa5853e3f46617a3b9378cf3546aa202aac3879` |
<!-- END GENERATED: image-identities -->
