# Micronaut comparison

Independent **Micronaut Platform 5.2.6** application, using its normal Netty HTTP server,
compile-time dependency injection, Micronaut Serialization, Reactor, retry interceptor,
Micrometer Prometheus and generated OpenAPI/Swagger UI. It compiles the same shared
commercetools REST/GraphQL and Firebase/Firestore workload as the other applications.

The platform version was verified against [Maven Central metadata](https://repo.maven.apache.org/maven2/io/micronaut/platform/micronaut-platform/maven-metadata.xml)
on 15 November 2026. The benchmark pins it for reproducibility.

```shell
python tools/build.py --framework micronaut --docker --native
python tools/compare.py --framework all --docker --firebase --runtime both --native --runs 3
```

Run from the repository root. `--framework all` selects all three frameworks; `both`
retains its original GuicedEE/Quarkus meaning. Micronaut has full-JDK and native rows.
There is no application-jlink Micronaut row: its normal classpath application is not
presented as a modular linked application.

JVM packaging uses a thin application JAR plus separate dependency JARs, preserving SDK
classpath/resource discovery and every dependency module descriptor. The Maven parent
shade execution is disabled. Annotation processing and dependency copying are included
in the measured build lifecycle. Native compilation uses the same pinned Mandrel image
and 8 GiB compiler heap as the other native applications.

Native SDK metadata comes from exercising the full capability workload with the GraalVM
tracing agent. Micronaut and Google Cloud retain their published native support; the
additional metadata describes exercised upstream SDK reflection and declared service
providers. No GuicedEE wrappers or Quarkus extensions are dependencies of this project.

To refresh metadata after SDK changes, build the JVM image, obtain the agent library from
the pinned Mandrel image, then run:

```shell
python tools/trace_native.py /path/to/libnative-image-agent.so target/micronaut-trace --framework micronaut
python tools/import_standard_native_trace.py target/micronaut-trace --framework micronaut
python tools/build.py --framework micronaut --docker --runtime native --skip-emulator
```

The trace must pass all fifteen capability checks. Image provenance verifies SDK hashes;
the native executable must subsequently pass the same HTTP checks before its timings can
be published. Trace runs are instrumented diagnostics and never performance results.

Configuration lives in `src/main/resources/application.properties`. `HTTP_HOST`,
`HTTP_PORT`, `BENCH_UPSTREAM`, `FIRESTORE_EMULATOR_HOST` and `GCLOUD_PROJECT` are supplied
by the harness. The separate [persistence application](../persistence/micronaut) uses
Micronaut Hibernate ORM with local transactions and the shared fifteen-entity model.
