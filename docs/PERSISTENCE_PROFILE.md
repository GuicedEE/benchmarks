# Current persistence profile

Diagnostic batch `20261115-210514`; 150 measured reads and CRUD cycles per application.

**Instrumented diagnostics, not benchmark timings.** Use [RESULTS.md](../RESULTS.md) for the uninstrumented comparison.

JFR allocation weights are estimates; inclusive stacks overlap. Execution samples exclude native wait samples and do not measure elapsed phase time. Instrumentation changes timings. SQL statistics describe database work only.

| Application | Startup sampled allocation (MiB) | Warm sampled allocation (MiB) | Warm SQL calls | Of which transaction control | Warm SQL planning (ms) | Warm SQL execution (ms) |
|---|---:|---:|---:|---:|---:|---:|
| guicedee | 368.37 | 76.88 | 8550 | 900 | 0.00 | 154.88 |
| micronaut | 259.21 | 87.61 | 8100 | 450 | 0.00 | 181.71 |
| quarkus | 166.27 | 43.80 | 8100 | 450 | 0.00 | 142.04 |

Startup includes the first completed business transaction. Warm allocation covers the entire measured interval, not one request or retained memory. SQL times are database execution/planning totals and exclude application work, transport and CPU-quota waits. The table counts top-level SQL only; nested foreign-key checks are retained in the JSON and excluded from these totals to avoid double-counting execution time. They are not end-to-end transaction latency. Driver protocols can produce different transaction-control counters, including whether COMMIT appears as a separate statement. These counts do not imply omitted commits; the independent database checks verify committed visibility and rollback for every application.

## GuicedEE startup phases

Inclusive phase timings overlap and cannot be added.

| Phase | Instrumented duration (ms) |
|---|---:|
| application-startup | 10297.97 |
| context-discovery | 403.44 |
| pre-startup | 994.02 |
| guice-module-discovery | 518.08 |
| guice-create-injector | 602.21 |
| post-startup | 7504.74 |
| post-hook-complete:com.guicedee.persistence.PersistenceStartup | 6606.92 |
| persistence persistence-xml (all) | 104.27 |
| persistence metadata-bootstrap (bench) | 2998.94 |
| persistence mapping-model (bench) | 803.69 |
| persistence session-factory (bench) | 2701.42 |

## Startup database work

SQL counters cover application launch through the first committed graph, excluding schema preparation. Database execution time excludes transport, application work and CPU-quota waits.

| Application | SQL calls | Database execution (ms) |
|---|---:|---:|
| guicedee | 23 | 48.02 |
| micronaut | 35 | 4.22 |
| quarkus | 30 | 6.59 |

## Focused allocation samples

These inclusive stack estimates locate work; zero means no allocation sample observed on that stack.

| GuicedEE stack | Startup (MiB) | Warm (MiB) |
|---|---:|---:|
| `com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor.existingScoper` | 0.00 | 0.00 |
| `com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor$ScopedUniSubscription.<init>` | 0.00 | 0.00 |
| `com.guicedee.client.IGuiceContext.loaderToSet` | 0.86 | 3.34 |
| `com.guicedee.persistence.implementations.PersistenceDescriptorParser.parse` | 1.23 | 0.00 |
| `org.hibernate.bytecode.internal.bytebuddy.BytecodeProviderImpl.getReflectionOptimizer` | 0.00 | 0.00 |
| `org.hibernate.bytecode.internal.bytebuddy.BytecodeProviderImpl.<init>` | 0.00 | 0.00 |
| `org.hibernate.jpa.boot.spi.PersistenceXmlParser.loadUrlWithJaxb` | 0.00 | 0.00 |
| `org.hibernate.boot.model.process.spi.MetadataBuildingProcess.complete` | 17.24 | 0.00 |

[Machine-readable profile](persistence-profile.json) includes SQL statements, sample counts and JFR hashes. [Reproduce](../persistence/README.md#profile-startup-and-crud) with the same immutable application images. Full JFR recordings remain in ignored `target/`. Only this current diagnostic summary is published.
