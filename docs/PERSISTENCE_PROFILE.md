# Current persistence profile

Diagnostic batch `20261116-094350`; 150 measured reads and CRUD cycles per application.

**Instrumented diagnostics, not benchmark timings.** Use [RESULTS.md](../RESULTS.md) for the uninstrumented comparison.

JFR allocation weights are estimates; inclusive stacks overlap. Execution samples exclude native wait samples and do not measure elapsed phase time. Instrumentation changes timings. SQL statistics describe database work only.

| Application | Startup sampled allocation (MiB) | Warm sampled allocation (MiB) | Warm SQL calls | Of which transaction control | Warm SQL planning (ms) | Warm SQL execution (ms) |
|---|---:|---:|---:|---:|---:|---:|
| guicedee | 367.31 | 74.56 | 8550 | 900 | 0.00 | 153.25 |
| micronaut | 261.27 | 87.54 | 8100 | 450 | 0.00 | 182.50 |
| quarkus | 166.53 | 44.77 | 8100 | 450 | 0.00 | 153.97 |

Startup includes the first completed business transaction. Warm allocation covers the entire measured interval, not one request or retained memory. SQL times are database execution/planning totals and exclude application work, transport and CPU-quota waits. The table counts top-level SQL only; nested foreign-key checks are retained in the JSON and excluded from these totals to avoid double-counting execution time. They are not end-to-end transaction latency. Driver protocols can produce different transaction-control counters, including whether COMMIT appears as a separate statement. These counts do not imply omitted commits; the independent database checks verify committed visibility and rollback for every application.

## GuicedEE startup phases

Inclusive phase timings overlap and cannot be added.

| Phase | Instrumented duration (ms) |
|---|---:|
| application-startup | 9988.45 |
| context-discovery | 399.36 |
| pre-startup | 1000.98 |
| guice-module-discovery | 514.69 |
| guice-create-injector | 689.25 |
| post-startup | 7190.30 |
| post-hook-complete:com.guicedee.persistence.PersistenceStartup | 6199.68 |
| persistence persistence-xml (all) | 102.14 |
| persistence discovery-scan (scan-root) | 2.54 |
| persistence metadata-bootstrap (bench) | 2797.17 |
| persistence mapping-model (bench) | 800.30 |
| persistence session-factory (bench) | 2403.88 |

The current instrumented sample records **102.14 ms** for descriptor parsing and **2.54 ms** for persistence discovery. Metadata bootstrap (**2.797 s**) and session-factory creation (**2.404 s**) are the largest recorded persistence phases; mapping-model construction takes **0.800 s**. Discovery is nested within metadata bootstrap. These inclusive values must not be summed.


## Startup database work

SQL counters cover application launch through the first committed graph, excluding schema preparation. Database execution time excludes transport, application work and CPU-quota waits.

| Application | SQL calls | Database execution (ms) |
|---|---:|---:|
| guicedee | 23 | 6.28 |
| micronaut | 36 | 3.99 |
| quarkus | 30 | 3.89 |

## Focused allocation samples

These inclusive stack estimates locate work; zero means no allocation sample observed on that stack.

| GuicedEE stack | Startup (MiB) | Warm (MiB) |
|---|---:|---:|
| `com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor.existingScoper` | 0.00 | 0.00 |
| `com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor$ScopedUniSubscription.<init>` | 0.00 | 0.00 |
| `com.guicedee.client.IGuiceContext.loaderToSet` | 0.84 | 0.00 |
| `com.guicedee.persistence.implementations.PersistenceDescriptorParser.parse` | 1.41 | 0.00 |
| `com.guicedee.modules.services.hibernate.scan.ClassGraphScanner.scan` | 0.76 | 0.00 |
| `com.guicedee.modules.services.hibernate.scan.ExplicitPersistenceScanner.scan` | 0.51 | 0.00 |
| `org.hibernate.bytecode.internal.bytebuddy.BytecodeProviderImpl.getReflectionOptimizer` | 0.00 | 0.00 |
| `org.hibernate.bytecode.internal.bytebuddy.BytecodeProviderImpl.<init>` | 0.00 | 0.00 |
| `org.hibernate.jpa.boot.spi.PersistenceXmlParser.loadUrlWithJaxb` | 0.00 | 0.00 |
| `org.hibernate.boot.model.process.spi.MetadataBuildingProcess.complete` | 16.53 | 0.00 |
| `org.hibernate.boot.internal.BootstrapContextImpl.createModelBuildingContext` | 16.92 | 0.00 |
| `org.hibernate.boot.model.source.internal.hbm.ModelBinder.prepare` | 0.00 | 0.00 |
| `org.hibernate.internal.SessionFactoryImpl.<init>` | 54.13 | 0.00 |
| `org.hibernate.metamodel.model.domain.internal.MappingMetamodelImpl.finishInitialization` | 27.01 | 0.00 |
| `org.hibernate.query.internal.QueryEngineImpl.<init>` | 12.66 | 0.00 |
| `org.hibernate.metamodel.internal.EntityInstantiatorPojoStandard.instantiate` | 2.52 | 0.00 |
| `org.hibernate.metamodel.internal.GuiceEntityProvider.get` | 2.52 | 0.00 |

[Machine-readable profile](persistence-profile.json) includes SQL statements, sample counts and JFR hashes. [Reproduce](../persistence/README.md#profile-startup-and-crud) with the same immutable application images. Full JFR recordings remain in ignored `target/`. Only this current diagnostic summary is published.
