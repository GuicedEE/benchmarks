# Quarkus with normal upstream dependencies

This standalone Maven application imports Quarkus's BOM directly. It does not inherit
the DevSuite/GuicedEE BOM, depend on `comparison-common`, or use GuicedEE's SDK wrappers,
relocated native metadata or application-specific substitutions from `quarkus-native`.
The older projects remain available for the historical comparison with identical SDK JARs.

It compiles the **same shared business Java sources and Quarkus adapter sources** directly
into a conventional Quarkus classpath application. The existing shared JPMS module is
untouched; no `module-info.class` is removed or excluded from any artifact.

Dependencies:

- Quarkus 3.40.1 and its REST/Jackson, fault tolerance, Micrometer/Prometheus and OpenAPI extensions.
- Upstream commercetools API and HTTP-client dependencies 20.4.0. The
  [SDK's normal HTTP-client alias](https://github.com/commercetools/commercetools-sdk-java-v2)
  selects its async HTTP client; this project does not replace it with a custom transport.
- Upstream Firebase Admin 9.12.0, supplied through the published Quarkiverse Google Cloud
  [Firebase Admin](https://docs.quarkiverse.io/quarkus-google-cloud-services/main/firebase-admin.html)
  and [Firestore](https://docs.quarkiverse.io/quarkus-google-cloud-services/main/firestore.html)
  extensions 2.25.1. These are community extensions with their own native support.

The two top-level SDK versions match the GuicedEE fixture. Transitive dependencies resolve
normally under the Quarkus BOM and extension dependency graph; their versions and JAR hashes
are deliberately not forced to match GuicedEE's repackaging. Each image records all resolved
JAR paths/hashes and the actual source contents/hashes in `/app/build-provenance.json`.
The inventory rejects GuicedEE dependencies and requires both upstream SDK JARs.

Configuration enables the measured documentation/metrics routes and sets the fixture's
host/port. It leaves Quarkus's Vert.x pool sizing at its default. Analytics and Dev Services
are disabled for this local benchmark with externally owned fixtures. The full SDK/Firestore
business flow and capability gate are unchanged.

Application integration requirements found by the capability checks and native compiler:

- `jackson-annotations` is aligned to 2.23 because commercetools's Jackson 3.2.3 calls
  `JsonTypeInfo.Value.getWriteTypeIdForDefaultImpl()`. The Quarkus BOM's older annotations
  produced `NoSuchMethodError` even on the JVM. Quarkus's Jackson 2 mapper is unchanged.
- Native commercetools needs service-provider resources and reflective model registrations.
  The committed metadata comes from a **new passing trace of this upstream-dependency JVM**,
  following Quarkus's [native metadata guidance](https://quarkus.io/guides/native-reference/).
  It contains observed commercetools, AsyncHttpClient, Jackson 3 and money types/resources, plus constructors
  for providers declared by the upstream SDK JARs (the agent misses these MethodHandle calls). Published
  extensions supply Firebase/Firestore and framework native support. There are no custom
  substitutions or copied wrapper configurations in this project.
- AsyncHttpClient initializes at runtime. Its static default resolver otherwise captures
  a runtime-only Netty executor in the native image heap, which the compiler correctly rejects.
- `javax.activation:activation:1.1.1` supplies the legacy API and implementation referenced by
  AsyncHttpClient's multipart support. Quarkus's Jakarta Activation API uses a different
  package and cannot satisfy that reference. Native analysis checks this path even though
  the measured workload sends JSON. Quarkus core excludes `com.sun.activation:javax.activation`
  from packaging, so that otherwise compatible coordinate cannot supply this legacy API here.

The first native attempt compiled but failed the commercetools SPI capability check.
Enabling automatic registration of every service also reached an incompatible optional
gRPC xDS backend, so the final configuration retains Quarkus's default and supplies targeted
metadata. Those failed attempts are excluded from performance comparisons. This is a working
Quarkus application integration, not a claim that arbitrary vendor SDKs work natively with
zero configuration.

To regenerate native metadata after SDK changes, build the JVM image first, obtain the
`libnative-image-agent.so` from the pinned Mandrel builder, then run:

```powershell
python benchmarks/tools/trace_native.py <agent.so> <fresh-trace-directory> --quarkus-dependencies standard
python benchmarks/tools/import_standard_native_trace.py <fresh-trace-directory>
./benchmarks/docker/build-quarkus-standard.ps1 -NativeOnly
```

The importer requires all 15 capabilities to pass and verifies the relevant SDK and transitive
dependency hashes against the JVM image before accepting the trace. Native image packaging
also rejects stale SDK metadata; JVM packaging remains available so changed dependencies can
be traced again. Traces run with extra resources and are
always excluded from timings; the finished native executable must pass the same full gate.

From the DevSuite root:

```powershell
# Independent Docker/Maven resolution; no GuicedEE rebuild or SDK staging required.
./benchmarks/docker/build-quarkus-standard.ps1 -Native
# Reuse the current GuicedEE native image and compare seven alternating fresh starts.
python benchmarks/tools/compare.py --docker --firebase --runtime native --quarkus-dependencies standard --runs 7 --requests 30 --warmup 10
python benchmarks/tools/summarize_native.py benchmarks/results/<batch>
# Optional full-JDK SPI/scanner comparison against the standard Quarkus fast-JAR.
python benchmarks/tools/compare.py --docker --firebase --quarkus-dependencies standard --runs 5
```

`--quarkus-dependencies wrapped` remains the harness default for reproducing old commands;
use `standard` explicitly for the independent comparison. Native images use the same pinned
Mandrel compiler and OS base as the GuicedEE images. All measured images receive the same
250m CPU / 500 MiB container limits, heap limits and processor count. Native build work is
outside the startup timer. Business completion waits for real SDK OAuth, REST, GraphQL and
Firestore write/read responses; HTTP route readiness is recorded separately.
