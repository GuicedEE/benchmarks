# Run the benchmarks

Commands run from this repository root on Windows, Linux or macOS. The Python build entry
point owns the benchmark applications and images; it does not inspect or rebuild neighboring
framework repositories.

## Requirements

- JDK 25 and Maven 4 on PATH for local/GuicedEE application builds.
- Python 3.11 or newer; the harness uses only the standard library.
- Node.js 22 or newer and npm for the pinned Firebase emulator tools.
- Docker with Linux containers for capped JVM, application-jlink and native comparisons.
- Native compilation needs substantially more build RAM than the measured application's
  500 MiB runtime quota; the native projects allow an 8 GiB compiler heap.

```shell
git -c core.longpaths=true clone --depth 1 https://github.com/GuicedEE/benchmarks.git
cd benchmarks
python tools/build.py --docker --runtime both --native
python tools/compare.py --docker --firebase --runtime both --native --runs 5 --requests 100 --warmup 20
```

The build defaults to GuicedEE **2.6.0**, normal upstream Quarkus dependencies, and **Micronaut Platform 5.2.6**. It installs
the benchmark applications, prepares the Firestore emulator and builds all selected images.
The first build downloads dependencies and native compilation can take several minutes.
PowerShell users can use `./build.ps1` with the same Python CLI arguments, or the thin
wrappers under `docker/`.

## Java formatting

Java sources and tests are automatically formatted during Maven's `process-sources`
phase, before compilation, using Open Java Format 21.0.2 and `fmt-maven-plugin`
2.27.0.2. This also applies to the Python build entry points and Docker builds.
The standalone Quarkus, Micronaut and persistence projects use the same formatter,
including shared Java source directories.

```shell
mvn fmt:format
mvn fmt:check
mvn -f micronaut/pom.xml fmt:check
mvn -f persistence/micronaut/pom.xml fmt:check
```

The root commands cover the active reactor modules; enable the relevant Maven
profiles to include optional variants. For other standalone projects, use
`-f quarkus-standard/pom.xml`, `-f persistence/model/pom.xml` or
`-f persistence/quarkus/pom.xml`. Use `-Dfmt.skip=true` to skip formatting.
Align the IDE's Open Java Format version with the pinned build version.

## GuicedEE artifacts

For the independent **15-entity PostgreSQL persistence comparison**, run
`python tools/build_persistence.py`, then
`python tools/compare_persistence.py --runs 3 --requests 30 --warmup 10`.
The [persistence protocol](persistence/README.md) describes the shared schema, Narayana and
reactive stateless adapters, checks, limits and publication commands. It uses Docker's
PostgreSQL image and does not require the Firebase/Node.js fixture.

To measure the fast descriptor parser against the secured Hibernate fallback in the same
image, run `python tools/compare_persistence_parser.py --runs 3 --requests 150 --warmup 20`.
It runs the normal three-framework matrix and three additional GuicedEE starts, alternating
the control before/after the default parser. Only controls set
`GUICEDEE_PERSISTENCE_XML_PARSER=hibernate`; descriptor security checks remain enabled.
Controls are kept in the current raw dataset and reported separately from framework rankings.
Both JVMs receive `-Dlog4j.shutdownHookEnabled=false` so Log4j cannot stop logging
before framework shutdown finishes. The runner verifies clean lifecycle completion
and zero remaining database connections after each measured start.

Maven resolves the framework release and its BOM normally. To benchmark a different version
or an explicitly prepared Maven repository:

```shell
python tools/build.py --docker --runtime both --guicedee-version 2.6.0 --maven-repository /path/to/maven-repository
```

`--maven-repository` uses standard Maven repository layout and defaults to `~/.m2/repository`.
The build verifies the discovery SPI and, for native mode, the optional `native-image`
artifact. It stages only resolved dependencies and framework POMs for Linux builds.
The version override is a testing input; actual artifact and image hashes are recorded.

## Select a mode

| Mode | Build command | Measurement command |
|---|---|---|
| Full-JDK SPI, scanner, Quarkus and Micronaut | `python tools/build.py --docker` | `python tools/compare.py --docker --firebase` |
| Application jlink, SPI and scanner | `python tools/build.py --docker --framework guicedee --runtime jlink` | `python tools/compare.py --docker --firebase --framework guicedee --runtime jlink` |
| Native, SPI, Quarkus and Micronaut | `python tools/build.py --docker --runtime native` | `python tools/compare.py --docker --firebase --runtime native` |
| All nine modes | `python tools/build.py --docker --runtime both --native` | `python tools/compare.py --docker --firebase --runtime both --native` |
| All fourteen modes, including CDI/config | `python tools/build.py --docker --runtime both --native --cdi-config` | `python tools/compare.py --docker --firebase --runtime both --native --cdi-config` |
| Local JVMs | `python tools/build.py` | `python tools/compare.py --firebase` |
| Local GuicedEE application jlink | `python tools/build.py --framework guicedee --runtime both` | `python tools/compare.py --firebase --framework guicedee --runtime both` |
| Quarkus independently | `python tools/build.py --framework quarkus --docker --native` | `python tools/compare.py --docker --firebase --framework quarkus --runtime native --diagnostics --runs 1 --requests 3 --warmup 1` |

Add `--discovery spi` or `--discovery scan` to select a GuicedEE discovery mode. Scanner
native and Quarkus/Micronaut application jlink are not implemented. The CLI's `jre` name means the
full-JDK JVM baseline. Every GuicedEE artifact retains its JPMS descriptor. Linked images
contain the application and dependencies and use the generated module launcher.

For equal startup tuning, repeat a matrix with `--tiered`: every JVM gets C1 and the
native binaries retain their unchanged flags. Use `--reverse-initial-order` for a second
counterbalanced batch. `--tag <name>` builds separate images; `--image-tag <name>` selects
them for measurement. The runner resolves every tag to an immutable image ID before starting.

The optional `--quarkus-dependencies wrapped` selects the Quarkus control projects using
GuicedEE SDK wrappers. Use it for both building and running that experiment. The normal
comparison defaults to `standard` and uses the independent Quarkus BOM/dependency graph.

`--framework all` is the default. `--framework both` retains the GuicedEE/Quarkus pair;
`--framework micronaut` selects the independent Micronaut project. Its [build and native
metadata instructions](micronaut/README.md) describe the upstream dependencies and SDK trace.

## Jakarta CDI and application.properties comparison

The [runtime validation record](docs/CDI-CONFIG-VALIDATION.md) covers Windows/Linux jlink and Linux native checks.

Add `--cdi-config` to both commands to include the separate `guicedee-cdi` JVM case:

```shell
python tools/build.py --framework both --docker --cdi-config
python tools/compare.py --framework both --docker --firebase --cdi-config --runs 5 --requests 100 --warmup 20
```

This compares the GuicedEE SPI and scanner baselines, upstream Quarkus, and the GuicedEE
Jakarta CDI/config bridge on the same workload. Use `--framework all` to include Micronaut.
The additional case uses `@ApplicationScoped`, Jakarta `@Inject` and `@PostConstruct`,
plus MicroProfile `@ConfigProperty` fields loaded from packaged `application.properties`.
`BENCH_UPSTREAM` and `BENCH_PHASE_DIAGNOSTICS` override the corresponding dotted keys.
HTTP, Vert.x and observability settings use matching application annotations and `.env` defaults as the scanner
baseline; this case measures application configuration integration, not a migration of
all GuicedEE bootstrap settings to MicroProfile Config.

The runner verifies the file-only marker, the effective upstream override and completed
Jakarta initialization through `/configuration`, in addition to the existing SDK, retry,
timeout, metrics and OpenAPI checks. Build inputs include the CDI/config dependency JARs
and properties file. The Maven reactor enables this module with `-Pcdi-config`.

The CDI/config matrix includes scanner and SPI JVM cases (`guicedee-cdi`,
`guicedee-cdi-spi`), full application-jlink equivalents, and SPI native
(`guicedee-cdi-native`). `--discovery scan` and `--discovery spi` select their respective
cases. Native runtime scanning is unavailable: GuicedEE's native substitution requires
SPI discovery and rejects scanner mode. Native is never reported as a scanner result.
These cases exercise GuicedEE's Jakarta annotation bridge, not full CDI compliance.
Existing published measurements do not include this new matrix.

```shell
python tools/build.py --framework guicedee --runtime both --cdi-config --docker
python tools/compare.py --framework guicedee --runtime both --cdi-config --docker --firebase
```

Native requires fresh passing traces for the exact SDK artifacts. Collect the base SPI
trace with `tools/trace_native.py <agent.so> <base-trace> --framework guicedee`, and the
CDI SPI trace with the same command plus `--cdi-config` and a different output directory.
Use the matching `--image-tag` for both traces. Then build with:

```shell
python tools/build.py --framework guicedee --runtime native --cdi-config --docker --trace-directory <base-trace> --cdi-trace-directory <cdi-trace>
python tools/compare.py --framework guicedee --runtime native --cdi-config --docker --firebase
```

The optional `com.guicedee:native-image` artifact must first be resolved into the selected
Maven repository. The build rejects SDK metadata from a different artifact hash.

## Workload and configuration

Each business request uses the actual commercetools SDK for OAuth, REST and GraphQL, then
awaits a Firebase Admin SDK Firestore write/read. The deterministic vendor server and
Firestore emulator run locally. No production credentials or vendor account is needed.
REST/DI, retry/timeout, metrics and OpenAPI/Swagger integrations belong to each framework.

GuicedEE settings live in `guicedee/.env` and `guicedee-scan/.env`. Override them in the
selected application's ignored `.env.local`, process environment or system properties.
The precedence is system properties, process environment, `.env.local`, `.env`, then
application annotations, then framework defaults. Quarkus uses its own `application.properties`.

GuicedEE benchmark application classes declare their framework defaults through
`@GuiceOptions`, `@HttpServerOptions`, `@VertX`, `@MetricsOptions` and `@TelemetryOptions`,
including the CDI/config and persistence variants. Application-specific defaults such as
the upstream URL can use repeatable `@EnvironmentProperty`. Persistence connection values
also have inline placeholder defaults in `persistence.xml`. Existing `.env` files remain
deploy-time overrides.

The entry points call `GuiceApplication.run(Main.class)`, which registers bootstrap
defaults before context creation. SPI discovery providers also include `Main.class`
so runtime configuration annotations are visible without scanning. The jlink/native
variants consume these same application JARs. Explicit Vert.x timeout, transport and
classloader values preserve the runtime defaults used before adding annotations.

The runner owns and cleans up its processes and containers. It refuses an occupied
Firestore emulator port (18088). The fixture project `demo-devsuite` and literal `fixture`
OAuth values are local test identifiers. Use `--skip-emulator` when building if its tools
are already installed. `--firebase` is required for full capability parity when measuring.

Docker enforces 250m CPU / 500 MiB with no additional swap. JVM/native flags are
`-Xms128m -Xmx384m -XX:ActiveProcessorCount=2`. Readiness and full-business startup are
separate timers; the latter waits for the complete reactive business response.
[RESULTS.md](RESULTS.md#measurement-contract) defines the statistics and timing boundaries.

## Diagnostics and native metadata

`--diagnostics` captures startup, scan/injector and SDK phases. Instrumented rows cannot
enter performance comparisons. A single-variant functional diagnostic can pass its checks
without declaring an eligible cross-framework comparison.

Native metadata is a build input, not a report archive. It is tied to the SDK hashes used
by a passing capability trace. Dependency changes require a fresh trace and metadata import;
the build rejects stale SDK inputs. See [GuicedEE native](guicedee-native/README.md),
[normal Quarkus native](quarkus-standard/README.md), and the [wrapped SDK control](quarkus-native/README.md).

## Build timing

After building/staging the applications with `tools/build.py`, measure all nine artifact
types on the same Linux JDK/Maven toolchain:

```shell
python tools/compare_builds.py --docker --runs 3
```

For the fourteen-mode matrix, build with `--cdi-config` and pass `--cdi-config` to
`compare_builds.py` as well. This adds CDI/config compilation, JVM packaging, both
application-jlink artifacts and the CDI SPI native executable.

The runner prepares each dependency cache with an untimed successful build, then measures
new offline Maven processes with clean outputs. Java compilation and complete packaging
are separate tasks. Native packaging runs the actual native compiler on every repetition;
Docker build-layer cache hits are never counted as compilation. No runtime container quota
is applied to the builder. All samples and logs go to ignored `target/build-runs/<timestamp>`.
Failed or incomplete matrices cannot be published.

Use `--variants guicedee guicedee-scan quarkus-standard` for JVM-only builds, or omit
`--docker` to use your host JDK/Maven. Host runs support `--maven-repository`; Docker uses
the repository staged by `tools/build.py`. `--guicedee-version` selects the prepared artifacts
explicitly. Changing native SDK inputs still requires matching reachability metadata.
The published grid includes CDI/config variants, with jlink build times compared against native
image builds. See [build results](RESULTS.md#build-performance)
for the measured boundaries, artifact hashes and environment.

## Results and validation

Fresh executions write raw results, logs and provenance to ignored `target/runs/<timestamp>`.
Only the current published measurement set belongs in `results/latest`. Publish a complete
passing batch with `tools/publish_results.py`; [results/README.md](results/README.md) describes
the workflow. Source snapshots, failed experiments and old reports are not duplicated in Git.

```shell
python -m unittest discover -s tools -p test_harness.py
python tools/verify_latest.py
python tools/render_performance.py --check
```

The build/run helpers preserve input hashes and capability failures. Neither a failed first
request nor a failed capability gate can become a performance win. Percentiles are sequential
latency measurements, not sustained throughput or an overload test.

Configuration regression checks (after building the framework and benchmark dependencies):

```powershell
python tools/configuration-contract/verify.py
python tools/configuration-smoke/verify.py
python ../GuicedEE/website/tools/vertx_configuration.py --check
```

The discovery probes check class/package declarations and duplicate rejection in scanner
and SPI modes. The smoke checks use existing application classes and full module paths
with freshly packaged framework jars; they do not substitute for a full benchmark Maven
build or a database workload run. Persistence smoke checks metadata and defaults only.
