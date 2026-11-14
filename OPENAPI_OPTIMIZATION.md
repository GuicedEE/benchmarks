# OpenAPI provider optimization — 14 November 2026

The standard OpenAPI setup now avoids Swagger's configuration serialization/deserialization round trips and generates OpenAPI 3.1 directly. The model and JSON/YAML codecs are still built during startup. In the alternating image comparison, median readiness improved **5.0% for SPI jlink and 5.5% for scanner jlink**. The separately instrumented provider phase fell **28.4% and 39.9%**, respectively.

These are incremental improvements. They do not close the gap to Quarkus native, and three starts per role/discovery mode are a small sample.

## Uninstrumented comparison

The [alternating batch](results/20261114-200551/summary.json) ran the original and updated images in the same process, with reversed order in the second round. All **12 fresh starts, 180 capability checks and 60 measured warm requests passed**, with no OOM kills. Each container had **250m CPU / 500 MiB**, no extra swap and the same default JVM tiering. First business completion includes commercetools OAuth/REST/GraphQL and Firestore write/read completion.

| Median | SPI before | SPI after | Change | Scanner before | Scanner after | Change |
|---|---:|---:|---:|---:|---:|---:|
| Launch → readiness | 8.062 s | **7.661 s** | **−5.0%** | 8.504 s | **8.037 s** | **−5.5%** |
| Launch → first business completion | 14.355 s | **13.745 s** | **−4.2%** | 14.508 s | **13.987 s** | **−3.6%** |
| First OpenAPI JSON request | 192 ms | 103 ms | −46.3% | 174 ms | 191 ms | +9.5% |

The documentation request runs after the first business request and other capability checks, so it is not a documentation-first startup measurement. Its latency is mixed across variants; there is no claim of a uniform documentation-request speedup. Spec generation remains eager, verified by provider tests and startup provisioning spans.

All individual samples and percentages are in [openapi-verification.json](results/openapi-verification.json). The paired run also records the served JSON documents. Before this control, the [original image batch](results/20261114-194654/summary.json), [direct-generation-only batch](results/20261114-195349/summary.json) and [separate final-candidate batch](results/20261114-200110/summary.json) were run. The last of these was noisy and had worse median end-to-end times; it remains available and is not pooled away. That observation prompted the alternating control, rather than selecting favorable individual starts.

The harness previously combined rotation and reversal in a way that canceled the reversal for two variants. It now reverses the second round, then rotates subsequent pairs of rounds. `--baseline-image-tag` makes original/candidate execution and immutable image identities explicit.

## Provider phases and scope

These are instrumented observations, separate from the performance comparison above:

| Inclusive provider provisioning median | Before | After | Reduction |
|---|---:|---:|---:|
| SPI jlink | 1,396 ms | **1,000 ms** | **28.4%** |
| Scanner jlink | 1,501 ms | **902 ms** | **39.9%** |

Evidence: [original phase batch](results/20261114-192338/summary.json), [updated phase batch](results/20261114-200341/summary.json), [updated phase summary](results/openapi-phase-summary.json). The six updated starts passed another **90 capability checks and 18 measured requests**. Provisioning spans include class loading and CPU throttling; nested startup durations cannot be added together.

Both inventories still have 35 startup Guice bindings. SPI performs no ClassGraph scan; scanner mode accepts only the three application classes from `bench.guicedee.scan`. The existing framework `ScanResult` remains shared.

## Changes and compatibility

- `OpenAPIProvider` now passes the effective configuration to the reader and context as well as the scanner. Previously its SPI configuration did not reach the reader. Configuration files are actually loaded, followed by SPI contributions, including contributions that replace the configuration object.
- Standard configurations use a provider-owned reader configuration and initialize the existing Swagger context through its public setters. This avoids three JSON configuration-copy round trips. The standard model is read once and retained by the existing context cache.
- Seed models, custom mapper processors/converters, sorted output, custom response codes/versions, finite cache lifetimes and legacy conversion use Swagger's full initialization path. Caller-owned seed models remain isolated. There is no upstream Swagger fork or new dependency in GuicedEE core.
- The default generates 3.1 directly. Applications can still select 3.0 or the former 3.0-to-3.1 conversion through `IGuicedSwaggerConfiguration`. Configuration files use Swagger's document format and should explicitly specify `openAPI31: true` when selecting 3.1.

Direct 3.1 output is **not byte-for-byte or schema-shape identical** to converted 3.0. In this fixture, the default `jsonSchemaDialect` field is omitted and the opaque `UniResponse` component becomes `{}` instead of `{"type":"object"}`. The latter is a less restrictive schema, reflecting Swagger's different implicit-object default in direct 3.1 mode. All paths, the typed `Order` schema and the quote response are unchanged in [all six paired document comparisons](results/openapi-spec-verification.json). Typed map/reference round trips are covered in both codecs. Consumers requiring the previous opaque-schema constraints can retain the legacy path:

```java
((SwaggerConfiguration) configuration)
    .openAPI31(false)
    .convertToOpenAPI31(true);
```

This change preserves runtime discovery and API behavior, but applications using generated clients or schema-diff gates should review the generated document when switching to direct 3.1. See the [OpenAPI module configuration](docs/FRAMEWORK_SOURCES.md#openapi).

## Packaged inputs and validation

The [module fingerprint tool](tools/ModuleFingerprint.java) reads every resource from each installed module without initializing application classes. For each discovery mode, **105 of 107 module fingerprints are identical** between original and candidate, including the application, shared workload, commercetools, Firebase and Swagger library modules. The changed modules are `com.guicedee.openapi` and `java.base`; the latter differs only in 12 jlink-generated method-handle classes. These generated runtime differences are recorded in the verification ledger rather than claiming an otherwise byte-identical image.

The original `:phases` and six-variant `:local` images were retained. Updated images are tagged `:openapi-fast`; immutable IDs and source/artifact provenance are in each batch. The staged SDK artifacts were retained throughout.

**14 OpenAPI module tests and 14 harness tests passed.** Coverage includes eager generation, JSON/YAML HTTP output, typed map/reference round trips, configuration SPI mutation/replacement, file-before-SPI precedence, seed isolation, custom mapper processing/sorting, legacy conversion, response-code overrides, reactive registry merging, image pairing and run-order reversal.

```powershell
mvn -B -ntp -f GuicedEE/openapi/pom.xml package -Dmaven.javadoc.skip=true
./benchmarks/docker/build-phases.ps1 -Tag openapi-fast -UpdateOpenApi -GuicedeeOnly
python benchmarks/tools/compare.py --docker --firebase --framework guicedee --runtime jlink --baseline-image-tag phases --image-tag openapi-fast --runs 3 --warmup 2 --requests 5
python benchmarks/tools/compare.py --docker --firebase --framework guicedee --runtime jlink --image-tag openapi-fast --diagnostics --runs 3 --warmup 1 --requests 3
```

The earlier [commercetools phase finding](PHASE_ANALYSIS.md#first-use-sdk-phases) remains important: client initialization was **14.300 s on Quarkus JVM versus 1.108 s on GuicedEE SPI jlink**, before REST/OAuth. That is a cold initialization measurement, not a Quarkus native or throughput result. This OpenAPI change does not alter those SDK binaries or explain Quarkus's initialization cost.
