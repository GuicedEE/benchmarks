# Running and interpreting the benchmarks

The current measurements and mode coverage are in [RESULTS.md](RESULTS.md). Commands below run from the DevSuite root unless marked as standalone.

## Run

To use the complete workspace, initialize `benchmarks` with
`git submodule update --init benchmarks` from DevSuite. The commands below use that layout.
On Windows, deeply nested checkouts of SDK native metadata need
`git -c core.longpaths=true submodule update --init benchmarks`. For a standalone clone,
use `git -c core.longpaths=true clone https://github.com/GuicedEE/benchmarks.git`.
GuicedEE builds require the matching locally built framework artifacts described in the
[source requirements](docs/FRAMEWORK_SOURCES.md); those unpublished inputs are not bundled here.

For the independent Quarkus project, a standalone checkout is supported:

```powershell
git clone https://github.com/GuicedEE/benchmarks.git
cd benchmarks
./docker/build-quarkus-standard.ps1 -Native
npm ci --prefix fixtures/firebase --ignore-scripts --no-audit
node fixtures/firebase/node_modules/firebase-tools/lib/bin/firebase.js setup:emulators:firestore
python tools/compare.py --docker --firebase --framework quarkus --quarkus-dependencies standard --runtime native --diagnostics --runs 1 --requests 3 --warmup 1
python -m unittest discover -s tools -p test_harness.py
python tools/verify_retained_evidence.py
```

The single-framework diagnostic validates capabilities; it cannot establish a comparative
performance result. Comparing both frameworks requires the corresponding GuicedEE images.

From DevSuite, with Java 25, Maven, Python 3 and Node installed:

```powershell
./benchmarks/build.ps1 -InstallGuicedEE
python benchmarks/tools/compare.py --firebase --runs 5 --requests 100 --warmup 20
# Separate equally tuned comparison (never compare one tuned stack to the other untuned):
python benchmarks/tools/compare.py --firebase --tiered --runs 5
# Linux containers at the report's per-instance CPU/memory limits:
./benchmarks/docker/build.ps1
python benchmarks/tools/compare.py --docker --firebase --runs 5
# Scanner-only GuicedEE artifact versus Quarkus:
python benchmarks/tools/compare.py --docker --firebase --discovery scan --runs 5
# Five variants: SPI / scanner on the full JDK and application jlink, plus Quarkus fast-JAR:
python benchmarks/tools/compare.py --docker --firebase --runtime both --runs 3 --requests 30 --warmup 10
# Equal startup-oriented JVM tuning, separate from default-tiered results:
python benchmarks/tools/compare.py --docker --firebase --runtime both --tiered --runs 3 --requests 30 --warmup 10
# Harness checks:
python -m unittest discover -s benchmarks/tools -p test_harness.py -v
# Add GuicedEE SPI and Quarkus native executables (seven variants):
./benchmarks/docker/build.ps1 -Native
python benchmarks/tools/compare.py --docker --firebase --runtime both --native --runs 3 --requests 30 --warmup 10
# Native-only comparison, same compiler and container limits:
./benchmarks/docker/build-guicedee-native.ps1
python benchmarks/tools/compare.py --docker --firebase --runtime native --runs 5 --requests 30 --warmup 10
# Independent Quarkus upstream dependencies versus the current GuicedEE native image:
./benchmarks/docker/build-quarkus-standard.ps1 -Native
python benchmarks/tools/compare.py --docker --firebase --runtime native --quarkus-dependencies standard --runs 7 --requests 30 --warmup 10
```

`-InstallGuicedEE` installs the current local feature modules before building the fixture. Omit it when the intended artifacts are already installed. Inspect the recorded hashes to establish exactly what was measured. The root benchmark reactor is independent of DevSuite's production build.

The runner owns local processes only: its mock upstream, applications and official Firestore emulator on port 18088. It refuses an occupied emulator port. No vendor account, production Firebase project, credential file or cloud deployment is required. The project is `demo-devsuite`. Mock OAuth credentials are literal `fixture` values. The emulator's open rules are for this local fixture only.

The default run without `--firebase` is diagnostic and **cannot pass full parity**. A single variant cannot declare a comparative result. Every selected variant/run must appear exactly once and pass the capability gate. Failed startup, wrong bodies, failed capabilities and warm-request failures remain in JSON and produce a nonzero exit. Process cleanup runs even after failure.

The [guicedee project](guicedee/pom.xml) defaults to SPI through its `.env`, and the [guicedee-scan project](guicedee-scan/pom.xml) defaults to scanning through its own `.env`. The runner defaults to `--discovery both`. `--discovery scan` selects `comparison-guicedee-scan-1.0-SNAPSHOT.jar`, whose named module is `bench.guicedee.scan`; no `BenchmarkDiscovery` class or registration is present. `--discovery spi` selects `comparison-guicedee-1.0-SNAPSHOT.jar`, where `BenchmarkDiscovery` registers Main, Resource and Service. Neither project excludes its descriptor. Main, Resource and Service sources are deliberately identical across the two self-contained applications; the packaging check catches drift. These are fixture choices; framework defaults are unchanged.

Resource and Service have distinct `@Verticle` names **and packages**, because GuicedEE groups verticles by package. Configuration remains in `.env`, without options annotations on Main or package-info. The resource still invokes its injected service directly; two deployments do not turn that Java call into an event-bus request.

Both GuicedEE applications use `com.google.inject.Inject` and `com.google.inject.Singleton` directly.

## jlink runtime comparison

`docker/build.ps1` packages the generated runtime dependencies and builds five images: GuicedEE SPI/scanner on the full Oracle JDK, their fully linked application images, and the Quarkus fast-JAR baseline. The CLI's existing `--runtime jre` name selects the full JDK baseline; `--runtime both` selects all five variants. Quarkus does not gain an application-linked image by trimming its JDK.

Dedicated `guicedee-jlink` and `guicedee-scan-jlink` Maven modules use `packaging: jlink` and `maven-jlink-plugin`, each depending on its application. Maven resolves and links the complete dependency graph. Docker builds these modules on Oracle JDK 25 and copies `target/maven-jlink/default` whole. The generated `bin/benchmark` launcher starts the embedded application; no loose application JARs or classpath fallback are used. This follows the GuicedEE cloud-app jlink packaging skill.

The plugin currently roots every resolved dependency module. The resulting 107-module images are valid but not minimal: application-root resolution reaches 96 modules, or 101 with service binding restricted to installed providers. SDK bundles dominate their size. See the [audit](JLINK_AUDIT.md) before treating successful linking as dependency minimization.

The runner records image IDs, artifact hashes, runtime modules and launch commands. Successful linking is only packaging evidence; capability and performance measurements require new runs against these exact images.

## Configuration

GuicedEE runtime settings live in [guicedee/.env](guicedee/.env). [Main.java](guicedee/src/main/java/bench/guicedee/Main.java) only anchors the application module and starts GuicedEE. Metrics/Prometheus, JMX, telemetry, Vert.x pools, HTTP defaults and discovery use the existing `com.guicedee.client.Environment` resolver. No `config-core` dependency is needed.

The precedence is system properties, process environment, `.env.local`, `.env`, then annotation/framework defaults. Put local changes in the selected project's `.env.local` (Git-ignored), and restart after changing a file. The runner starts local Java processes in their application's directory. For an IDE/manual launch, use `benchmarks/guicedee` or `benchmarks/guicedee-scan` as appropriate.

Docker packages the selected project's committed `.env` at `/app/.env`; rebuild the images after changing it. The runner mounts that project's existing `.env.local` read-only and records its hash, not its contents. Explicit host GuicedEE/Vert.x/metrics/telemetry environment settings are forwarded. The driver supplies dynamic ports and local vendor/Firestore addresses as process environment variables. An explicit `--discovery` overrides the file setting. File defaults are included in image provenance; `.env.local` contents are never archived there.

Quarkus retains its native `application.properties` configuration and receives the same dynamic fixture addresses and ports.

## Workload and capability gate

| Capability | Exercised behavior |
|---|---|
| REST | Framework-managed `POST /quote`, JSON binding/serialization, exact expected response; omitted primitive query parameter tested separately |
| Vendor SDK | Real commercetools client credentials, typed project GET, bearer-token validation by fixture |
| GraphQL client | Real SDK GraphQL POST for inventory, parsed response used to compute the quote; no claim of an inbound GraphQL server |
| Firebase | Firebase Admin SDK writes and reads Firestore through the official emulator; included in first business request with `--firebase` |
| Retry | Framework `@Retry` around a reactive upstream call; fixture verifies exactly three attempts and exhaustion |
| Timeout | Framework `@Timeout` must bound asynchronous completion; a concurrent readiness request is also recorded |
| Metrics | Framework integration must expose the application quote counter and increment it on another business request |
| OpenAPI / Swagger | Generated document must contain `/quote`; bundled UI, JavaScript bundle and stylesheet must be served |
| Errors | Shared application validation/exhaustion/timeout envelopes; malformed JSON and unsupported media status checks |

Business validation and upstream error envelopes are explicit application code in both adapters. Framework-generated errors are retained as observed bodies; the initial suite checks their status, not complete error-envelope parity. Authentication, telemetry propagation, Secret Manager, circuit breakers, bulkheads, cancellation of upstream work and the original application's acceptance matrix are not covered yet. Firebase here means Firestore, not every Firebase product.

The fixture uses shared SDK calls rather than a framework-specific GraphQL client, making its cost identical on both sides. Do not describe this as testing Quarkus SmallRye GraphQL Client against a GuicedEE equivalent. Each framework does supply its own REST/DI, metrics, OpenAPI and fault-tolerance path. The ledger makes shared/custom versus framework behavior explicit.

## Measurements and interpretation

Every sample starts a fresh process (JVM or native executable). Launch order rotates and reverses between rounds. The driver records launch-to-ready, first business status/body/latency, launch-to-first-business completion, upstream requests and warm latency samples after an explicit warm-up. Readiness polling is 50 ms; that sampling delay is included in every variant. The first business result is preserved even if it fails; it is never silently replaced with a later 200. GuicedEE rows also record log evidence that the requested discovery mode ran and both application verticles deployed.

JVM settings are identical: `-Xms128m -Xmx384m -XX:ActiveProcessorCount=2`, with `TieredStopAtLevel=1` added to every JVM variant only when requested. The native executable receives the same heap and processor limits, never the JIT flag; its compilation is outside measurement. Both adapters select two event-loop threads. Parent JVM tuning variables are removed from application processes. SDK initialization is lazy in the same shared code, and the first business request pays that cost.

Local warm samples use one outstanding request. They are latency diagnostics, not an open-loop throughput/knee or overload measurement. The mock and emulator are outside the application JVMs. Host page caches are not flushed. Input JAR hashes, source revision, flags, Java version, platform, individual checks and failures accompany each run under `results/`.

**ActiveProcessorCount is not a CPU quota.** Local Windows results do not satisfy the original 250m/500Mi criterion. `--docker` enforces `--cpus=0.25 --memory=500m --memory-swap=500m`, verifies the effective limits, records image IDs, cgroup CPU/throttling/memory counters and OOM state, and removes only its own containers. All five images use the same Oracle JDK 25 build and Oracle Linux base. The effective Java version, downloaded JDK archive hash, runtime module-image hash and generated launcher are recorded. The Oracle download URL is mutable, so the captured hashes identify the measured build. Each run pins the image IDs before measuring. Image build provenance includes packaged JAR hashes and a fixture source snapshot, separately from the working files observed at run time. Build the Maven reactor before packaging images; a source snapshot alone does not prove that stale JARs were rebuilt. The SDK mock and Firestore emulator stay outside the capped containers and are reachable through Docker Desktop's host gateway.

Container timing starts before `docker run`, including local container creation/start overhead, and excludes image building/pulling. This is still a single-container-at-a-time comparison, not Kubernetes readiness, scheduling, HPA or scale-out under traffic. The first-request client deadline is 60 seconds in Docker, 15 seconds locally. Timeout response validation allows up to 1 second in capped containers versus 225 ms locally because CPU throttling also delays response delivery; the required response remains the same 504 envelope. Neither run mode is comparable numerically with the historical application. Cgroup `memory.peak` is whole-container charged memory, not JVM heap or process RSS.

No ranking is allowed unless `summary.json` has `eligibleComparison: true`. Even a passing local result applies only to the implemented capability contract and the recorded local profile.

## Integration references

- [commercetools SDK customization](https://docs.commercetools.com/dev-tooling/java-sdk-customization): custom auth/API endpoints for the local fixture; actual overloads checked against pinned 20.4.0.
- [Firestore emulator integration](https://firebase.google.com/docs/emulator-suite/connect_firestore): Admin SDK uses `FIRESTORE_EMULATOR_HOST`.
- [Quarkus fault tolerance](https://quarkus.io/guides/smallrye-fault-tolerance/) and [OpenAPI/Swagger UI](https://quarkus.io/guides/openapi-swaggerui/): framework capabilities used by the Quarkus adapter.
- [Framework microbenchmark context](docs/FRAMEWORK_SOURCES.md#microbenchmarks): component-level investigations remain useful but are not this service comparison.

The preserved historical report says Firestore/Secret Manager were not built or tested and its capability checklist was a draft. Its claimed feature coverage is not adopted as evidence for this new fixture.

Firebase/Vert.x dependency mediation is controlled by the GuicedEE BOM. The commercetools
20.4 SDK uses Jackson 3 while Quarkus REST uses Jackson 2; both adapters align Jackson
annotations at 2.23. JSON remains an explicit service dependency. Telemetry export is
disabled for the non-tracing comparison; tracing parity is unmeasured. The independent
Quarkus project uses its own upstream dependency graph, detailed in
[its configuration guide](quarkus-standard/README.md).

### Oracle JDK application-linking validation

Build locally with Oracle JDK 25 and Maven 4:

```powershell
mvn -f benchmarks/pom.xml -pl guicedee-jlink,guicedee-scan-jlink -am package -DskipTests
python benchmarks/tools/compare.py --framework guicedee --runtime both --runs 3 --requests 100 --warmup 20 --firebase
```

Local linked runs execute the generated launchers and use the same capability gates.
They have no Docker CPU/memory quota and must not be presented as container measurements.
Linux Docker validation requires a running Docker Linux engine.
