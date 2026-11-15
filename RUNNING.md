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

The build defaults to GuicedEE **2.6.0** and normal upstream Quarkus dependencies. It installs
the benchmark applications, prepares the Firestore emulator and builds all selected images.
The first build downloads dependencies and native compilation can take several minutes.
PowerShell users can use `./build.ps1` with the same Python CLI arguments, or the thin
wrappers under `docker/`.

## GuicedEE artifacts

For the independent **15-entity PostgreSQL persistence comparison**, run
`python tools/build_persistence.py`, then
`python tools/compare_persistence.py --runs 3 --requests 30 --warmup 10`.
The [persistence protocol](persistence/README.md) describes the shared schema, Narayana and
reactive stateless adapters, checks, limits and publication commands. It uses Docker's
PostgreSQL image and does not require the Firebase/Node.js fixture.
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
| Full-JDK SPI, scanner and Quarkus | `python tools/build.py --docker` | `python tools/compare.py --docker --firebase` |
| Application jlink, SPI and scanner | `python tools/build.py --docker --framework guicedee --runtime jlink` | `python tools/compare.py --docker --firebase --framework guicedee --runtime jlink` |
| Native, SPI and Quarkus | `python tools/build.py --docker --runtime native` | `python tools/compare.py --docker --firebase --runtime native` |
| All seven modes | `python tools/build.py --docker --runtime both --native` | `python tools/compare.py --docker --firebase --runtime both --native` |
| Local JVMs | `python tools/build.py` | `python tools/compare.py --firebase` |
| Local GuicedEE application jlink | `python tools/build.py --framework guicedee --runtime both` | `python tools/compare.py --firebase --framework guicedee --runtime both` |
| Quarkus independently | `python tools/build.py --framework quarkus --docker --native` | `python tools/compare.py --docker --firebase --framework quarkus --runtime native --diagnostics --runs 1 --requests 3 --warmup 1` |

Add `--discovery spi` or `--discovery scan` to select a GuicedEE discovery mode. Scanner
native and Quarkus application jlink are not implemented. The CLI's `jre` name means the
full-JDK JVM baseline. Every GuicedEE artifact retains its JPMS descriptor. Linked images
contain the application and dependencies and use the generated module launcher.

For equal startup tuning, repeat a matrix with `--tiered`: every JVM gets C1 and the
native binaries retain their unchanged flags. Use `--reverse-initial-order` for a second
counterbalanced batch. `--tag <name>` builds separate images; `--image-tag <name>` selects
them for measurement. The runner resolves every tag to an immutable image ID before starting.

The optional `--quarkus-dependencies wrapped` selects the Quarkus control projects using
GuicedEE SDK wrappers. Use it for both building and running that experiment. The normal
comparison defaults to `standard` and uses the independent Quarkus BOM/dependency graph.

## Workload and configuration

Each business request uses the actual commercetools SDK for OAuth, REST and GraphQL, then
awaits a Firebase Admin SDK Firestore write/read. The deterministic vendor server and
Firestore emulator run locally. No production credentials or vendor account is needed.
REST/DI, retry/timeout, metrics and OpenAPI/Swagger integrations belong to each framework.

GuicedEE settings live in `guicedee/.env` and `guicedee-scan/.env`. Override them in the
selected application's ignored `.env.local`, process environment or system properties.
The precedence is system properties, process environment, `.env.local`, `.env`, then
framework defaults. Quarkus uses its own `application.properties`.

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

After building/staging the applications with `tools/build.py`, measure all seven artifact
types on the same Linux JDK/Maven toolchain:

```shell
python tools/compare_builds.py --docker --runs 3
```

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
The published grid uses all seven variants, with jlink build times compared against native
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
