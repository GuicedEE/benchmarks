# GuicedEE and Quarkus: current performance

**Latest measurements: 14 November 2026. Report reviewed: 15 November 2026.**

This repository compares a shared service workload across GuicedEE SPI, application
scanning, linked JVM runtimes and native executables, and Quarkus JVM/native applications.
The primary Quarkus comparison uses **normal upstream SDK dependencies** and unmodified
Quarkus framework sources. A separate wrapped-SDK comparison controls for SDK packaging.

At **250m CPU / 500 MiB**, GuicedEE native completes the first full business request in
**668 ms**, versus **706 ms** for normal-dependency Quarkus native: **5.4% less time**.
Warm request medians are **5.18 ms / 6.02 ms**. Quarkus uses less memory and disk:
**55.33 / 79.58 MiB** peak container memory and **143.31 / 191.83 MiB** executables
(Quarkus / GuicedEE). These are observed medians for this fixture, not a universal ranking.

## All run modes

**Median launch to completed business response, seconds.** Each linked cell identifies its
measurement group. This is an overview of available evidence across different image revisions;
comparative rankings belong within the matched groups in the detailed report.

<!-- BEGIN GENERATED: overview -->
| Application / dependencies | Full JDK default (s) | Full JDK C1 (s) | Application jlink default (s) | Application jlink C1 (s) | Native (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| GuicedEE SPI / wrapped SDKs | [31.019](RESULTS.md#jvm-default) | [18.546](RESULTS.md#jvm-c1) | [13.745](RESULTS.md#jlink-default) | [8.781](RESULTS.md#jvm-c1) | [0.668](RESULTS.md#native-standard) primary; [0.659](RESULTS.md#native-wrapped) control |
| GuicedEE scanner / wrapped SDKs | [32.975](RESULTS.md#jvm-default) | [19.432](RESULTS.md#jvm-c1) | [13.987](RESULTS.md#jlink-default) | [8.854](RESULTS.md#jvm-c1) | Unsupported |
| Quarkus / upstream SDKs | Diagnostic only | Unmeasured | No variant | No variant | [0.706](RESULTS.md#native-standard) |
| Quarkus / wrapped SDKs (control) | [30.026](RESULTS.md#jvm-default) | [17.812](RESULTS.md#jvm-c1) | No variant | No variant | [0.655](RESULTS.md#native-wrapped) |
<!-- END GENERATED: overview -->

The current evidence does **not** contain one freshly rebuilt matrix covering every mode.
JVM/C1 figures use the last complete matched matrix; default-jlink figures use the latest
controlled linked-image batch. Native figures use the latest applicable dependency comparison.
Normal-dependency Quarkus JVM has passed a diagnostic capability run but has no eligible
repeated performance batch. These measurements are not a GuicedEE 2.6.0 release benchmark.

## Detailed results

The **[full performance report](RESULTS.md)** contains:

- All startup grids: HTTP readiness, first request alone, complete business response,
  observed ranges, and first OpenAPI response.
- Warm p50/p95/p99 latency, peak/end container memory, executable and image sizes.
- Separate default JVM, C1, linked application, native and unrestricted local profiles.
- Instrumented startup/Guice/scan and commercetools/Firestore phase grids.
- Capability coverage, sample counts, missing modes, interpretation and immutable image IDs.

The headline native comparison includes **28 starts, 420 passing capability checks and
840 successful measured requests**. The completed business response waits for commercetools
SDK OAuth/REST/GraphQL and Firebase Admin SDK Firestore write/read. Timing includes the reactive
flow's completion, not just an available HTTP port. [Measurement definitions](RESULTS.md#measurement-contract)
explain the exact boundaries.

## Use the repository

- [Build, run, configure and validate](RUNNING.md)
- [Machine-readable grids (JSON)](docs/current-performance.json) and [spreadsheet data (CSV)](docs/current-performance.csv)
- [Companion GuicedEE sources and version requirements](docs/FRAMEWORK_SOURCES.md)
- [Evidence retention policy](docs/RETENTION.md)
- [Detailed investigations and archived measurements](docs/history/README.md)

From this repository's root, verify the published grids and their underlying evidence:

```powershell
python tools/render_performance.py --check
python tools/verify_retained_evidence.py
python -m unittest discover -s tools -p test_harness.py
```

This is a reference service using deterministic local vendor fixtures and the official
Firestore emulator. The original comparison application's template was unavailable.
Production network latency, sustained concurrent load and Kubernetes scale-out are unmeasured.
