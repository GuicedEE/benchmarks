# Current persistence profile

Diagnostic batch `20261115-170712`; 150 measured reads and CRUD cycles per application.

**Instrumented diagnostics, not benchmark timings.** Use [RESULTS.md](../RESULTS.md) for the uninstrumented comparison.

JFR allocation weights are estimates; inclusive stacks overlap. Execution samples exclude native wait samples and do not measure elapsed phase time. Instrumentation changes timings. SQL statistics describe database work only.

| Application | Startup sampled allocation (MiB) | Warm sampled allocation (MiB) | Warm SQL calls | Warm SQL planning (ms) | Warm SQL execution (ms) |
|---|---:|---:|---:|---:|---:|
| guicedee | 410.20 | 77.32 | 8550 | 0.00 | 134.88 |
| quarkus | 166.77 | 44.47 | 8100 | 0.00 | 168.58 |

Startup includes the first completed business transaction. Warm allocation covers the entire measured interval, not one request or retained memory. SQL times are database execution/planning totals and exclude application work, transport and CPU-quota waits. The table counts top-level SQL only; nested foreign-key checks are retained in the JSON and excluded from these totals to avoid double-counting execution time. They are not end-to-end transaction latency.

## GuicedEE startup phases

Inclusive phase timings overlap and cannot be added.

| Phase | Instrumented duration (ms) |
|---|---:|
| application-startup | 11685.56 |
| context-discovery | 408.34 |
| pre-startup | 903.66 |
| guice-module-discovery | 1012.22 |
| guice-create-injector | 885.66 |
| post-startup | 8194.58 |
| post-hook-complete:com.guicedee.persistence.PersistenceStartup | 7206.22 |

## Focused allocation samples

These inclusive stack estimates locate work; zero means no allocation sample observed on that stack.

| GuicedEE stack | Startup (MiB) | Warm (MiB) |
|---|---:|---:|
| `com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor.existingScoper` | 0.00 | 0.00 |
| `org.hibernate.bytecode.internal.bytebuddy.BytecodeProviderImpl.getReflectionOptimizer` | 12.74 | 0.00 |
| `org.hibernate.bytecode.internal.bytebuddy.BytecodeProviderImpl.<init>` | 15.24 | 0.00 |
| `org.hibernate.jpa.boot.spi.PersistenceXmlParser.loadUrlWithJaxb` | 12.73 | 0.00 |
| `org.hibernate.boot.model.process.spi.MetadataBuildingProcess.complete` | 17.00 | 0.00 |

[Machine-readable profile](persistence-profile.json) includes SQL statements, sample counts and JFR hashes. [Reproduce](../persistence/README.md#profile-startup-and-crud) with the same immutable application images. Full JFR recordings remain in ignored `target/`. Only this current diagnostic summary is published.
