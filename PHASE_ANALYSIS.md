# Startup, scan and injector diagnostics — 14 November 2026

The scanner is already restricted to the application. The larger measured costs are OpenAPI construction inside Guice and cold SDK initialization. These are **instrumented diagnostics**, not a replacement performance ranking or evidence of a startup improvement.

Follow-up: the [OpenAPI provider optimization](OPENAPI_OPTIMIZATION.md) now has its own alternating, uninstrumented before/after comparison and new phase captures. The original observations below are retained unchanged as its baseline.

Three fresh starts each of GuicedEE SPI jlink, GuicedEE scanner jlink and Quarkus JVM passed all 15 capability checks: **9 starts, 135 checks and 27 measured requests**, at the existing **250m CPU / 500 MiB** limits with default JVM tiering. Every phase capture passed validation. Their `eligibleComparison` is deliberately false. Guice provisioning listeners and diagnostic output add overhead; durations include CPU throttling, class loading and scheduling, not just CPU execution.

Evidence: [GuicedEE batch](results/20261114-192338/summary.json), [Quarkus JVM batch](results/20261114-192928/summary.json), [combined phase summary](results/phase-diagnostics-summary.json), and [verification record](results/phase-verification.json). The original native executable was not rebuilt or instrumented for this investigation.

## What ClassGraph actually scans

Both scanner runs and SPI runs retain their application module descriptors. The scanner inventory comes from GuicedEE's **existing live `ScanResult`** after startup; no second scan is created, and the diagnostic does not close the framework-owned result.

All three scanner runs accepted:

- Module: `bench.guicedee.scan`, from `jrt:/bench.guicedee.scan`.
- Classes: `bench.guicedee.Main`, `bench.guicedee.rest.Resource`, `bench.guicedee.service.Service`.
- Resources: seven, all from that application module.

SPI runs created **no ClassGraph scan**. Firebase, commercetools, JDK modules and other libraries do not appear as accepted scan sources. ClassGraph can still read superclass/interface/annotation metadata outside the accepted set to answer hierarchy queries; this inventory does not claim zero metadata reads outside the application.

The installed version is ClassGraph **6.0.2**. `ClassGraph` configures a scan; `ScanResult` holds its metadata. GuicedEE already shares that result. ClassGraph 6 removed `ScanResult.toJSON()` / `fromJSON()`, so a serialized scan cannot simply be restored through the old API. Build-generated, application-owned discovery metadata can instead feed the existing SPI. See the [upstream migration guide](https://github.com/classgraph/classgraph/wiki/Porting-ClassGraph-4.x-code-to-ClassGraph-6.x).

## Startup phases

Median wall-clock milliseconds from three starts per variant:

| Inclusive phase | SPI jlink | Scanner jlink |
|---|---:|---:|
| Context discovery | 499 | 493 |
| Discovery, including scanner setup/resource processing | 0.3 | 696 |
| Actual ClassGraph scan, within discovery | — | 404 |
| Pre-startup hooks | 1,090 | 897 |
| Vert.x pre-startup hook preparation, within pre-startup | 800 | 700 |
| Guice module discovery | 492 | 408 |
| Guice injector creation | 1,999 | 2,304 |
| `OpenAPIProvider` provisioning, within injector creation | **1,396** | **1,501** |
| Post-startup hooks through completion | 1,005 | 1,101 |
| Web-server hook completion, within post-startup | 697 | 701 |

Nested phases overlap and must not be added together. Pre-hook completion spans begin before hook invocation and finish when the returned future completes. Post-hook completion spans include event-loop queueing and await the returned reactive operation. Multiple futures from one hook produce multiple spans. Application-startup timestamps use a process-local monotonic origin after diagnostics initialization; the external launch-to-response timers still capture the surrounding JVM/container startup.

The OpenAPI provider constructs Swagger configuration, discovers its configuration SPI, initializes its reader/context and calls `read()` in its constructor. Its provisioning time is a clear next profiling target. These measurements do not yet separate its file probes, model building, class loading or schema conversion. Moving all of it to the first documentation request would shift work rather than establish that it has been removed; generated OpenAPI metadata is another candidate to investigate while retaining the capability gate.

## What Guice exposes

The diagnostic uses [Guice's `ProvisionListener`](https://google.github.io/guice/api-docs/7.0.0/javadoc/com/google/inject/spi/ProvisionListener.html) to time construction and [its binding snapshot API](https://google.github.io/guice/api-docs/7.0.0/javadoc/com/google/inject/Injector.html) to record dependency edges and available interceptor metadata. It adds one observer module only when enabled.

Every GuicedEE startup snapshot contains **35 bindings: 19 explicit and 16 created on demand**. No `getInstance()` or `Provider.get()` is called to produce that snapshot. Instance contents and qualifier values are omitted. The [SPI binding graph](results/20261114-192338/guicedee-jlink-1-bindings.dot) and [scanner binding graph](results/20261114-192338/guicedee-scan-jlink-1-bindings.dot) can be opened with GraphViz.

This is the injector at the startup barrier. Lazy resource/service bindings created by subsequent HTTP requests are not yet in it. Manually constructed SDK internals are not Guice bindings either. Therefore the **107 packaged JPMS modules, three accepted scan classes and 35 startup bindings describe different things**. Neither the scan inventory nor the Guice snapshot is a safe list of classes to delete. Guice introspection is not a facility for serializing and restoring a live injector.

## First-use SDK phases

The shared workload records actual completion of asynchronous SDK stages. The REST span includes first OAuth acquisition; there is no separate client-side OAuth timer in this instrumentation. Firestore still uses its existing worker-thread waits, and those waits are included.

| Median phase, milliseconds | SPI jlink | Scanner jlink | Quarkus JVM |
|---|---:|---:|---:|
| Workload JDK HTTP client construction | 598 | 602 | 698 |
| Commercetools client initialization | 1,108 | 1,004 | **14,300** |
| Commercetools REST including first OAuth | 1,407 | 1,497 | 1,596 |
| GraphQL request | 197 | 197 | 209 |
| Firestore client initialization | 1,713 | 1,407 | 1,502 |
| Firestore write completion | 1,302 | 1,305 | 1,407 |
| Firestore read completion | 8 | 86 | 8 |

**The commercetools initialization result is a substantial advantage for this GuicedEE workload: SPI jlink uses 92.3% less time than Quarkus JVM (1.108 s versus 14.300 s).** The delay is localized to client initialization, before the measured REST/OAuth request. The table does not establish whether class loading, runtime compilation or another initialization step causes it. Quarkus native's earlier result comes from another compilation strategy and is not a phase measurement here.

There are **two workload constructions per Quarkus run**, versus one per GuicedEE run. Generated `Service_ClientProxy` and `Service_Subclass` constructors both call the `Service` constructor, executing its field initializer. Only one quote/Firestore chain is exercised. The HTTP-client row sums constructions within each run before taking the median; the additional construction itself was sub-millisecond in these runs. This fixture behavior is recorded, not silently removed. The initial Quarkus diagnostic batch `20261114-192632` passed its capabilities but was rejected by an overly strict capture-count check; it is retained separately and excluded from this summary. The collector now retains repeated constructions and still rejects missing or repeated first business flows.

## Native and SDK sizes

Using the exact staged SDK artifacts from the earlier native comparison:

| Artifact measurement | MiB |
|---|---:|
| Firebase and commercetools JAR files combined, compressed | 106.14 |
| Their expanded ZIP entries combined | 286.53 |
| Their stored resources in the linked module image | 82.01 |
| Quarkus native executable | 174.81 |

The native executable is smaller than the expanded SDK contents, but larger than the compressed JAR files. Native analysis can remove unreachable classes/methods inside a library; jlink retains required modules and their contents. Different compression, debug stripping, machine-code size and native metadata also affect these numbers, so they do not quantify the exact number of SDK bytes eliminated. Docker store accounting is a separate measurement, covered in [JLINK_AUDIT.md](JLINK_AUDIT.md).

## Reproduction and validation

The instrumentation is opt-in through `GUICEDEE_DIAGNOSTICS_DIR`; configuration uses GuicedEE's normal environment resolver. No Jackson/config dependency is added to core. `BENCH_PHASE_DIAGNOSTICS` enables the shared workload observer through each framework's configuration resolver. With it disabled, the workload observer preserves asynchronous stage identity and does not allocate a trace per request.

Start with a staged benchmark Docker repository. The phase builder keeps its SDK artifacts isolated from concurrent host builds, updates the inject JAR, and compiles application sources inside Linux. The initial host Maven attempt encountered an in-progress commercetools artifact without its module descriptor; it was not used for these measurements. The original `:local` image tags remain unchanged.

```powershell
./benchmarks/docker/build-phases.ps1
python benchmarks/tools/compare.py --docker --firebase --framework guicedee --runtime jlink --diagnostics --image-tag phases --runs 3 --requests 3 --warmup 1
python benchmarks/tools/compare.py --docker --firebase --framework quarkus --diagnostics --image-tag phases --runs 3 --requests 3 --warmup 1
# Supply the two result directories printed by those commands:
python benchmarks/tools/summarize_phases.py <guicedee-results> <quarkus-results> --output <summary.json>
```

Each GuicedEE run writes `startup.json` into its diagnostic directory. SDK phase records are retained in both the application log and row JSON. Failed/missing captures reject the diagnostic batch; even successful diagnostic batches cannot become ranked comparisons. Source and image identities accompany each batch. For these initial phase images, `phaseDiagnosticInputs` identifies the replacement inject artifact and framework sources; host `packagedJars` entries in inherited provenance are not the artifacts compiled by the Linux builder. The repeatable preparation tool now excludes those host entries and records staged repository hashes explicitly.

Validation passed: **20 core lifecycle/shutdown/scan tests and 13 harness tests**, including deferred reactive completion, failure preservation, disabled-observer stage identity, repeated CDI construction capture and rejection of instrumented performance rankings.

The [disabled-observer smoke batch](results/20261114-193232/summary.json) also passed all 15 capabilities for both linked GuicedEE applications. It emitted no diagnostic output and retained the normal ten Guice modules. Its single start per variant is functional validation, not a new repeated performance baseline.
