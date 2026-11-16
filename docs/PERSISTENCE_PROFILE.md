# Current persistence profile

Diagnostic batch `20261116-112001`; 150 measured reads and CRUD cycles per application.

**Instrumented diagnostics, not benchmark timings.** Use [RESULTS.md](../RESULTS.md) for the uninstrumented comparison.

JFR allocation weights are estimates; inclusive stacks overlap. Execution samples exclude native wait samples and do not measure elapsed phase time. Instrumentation changes timings. SQL statistics describe database work only.

JVM flags: `-Xms128m`, `-Xmx384m`, `-XX:ActiveProcessorCount=2`, `-Dlog4j.shutdownHookEnabled=false`, `-XX:StartFlightRecording=filename=/tmp/persistence.jfr,settings=profile,dumponexit=true,maxsize=64m,jdk.ExecutionSample#period=2ms`.

| Application | Startup sampled allocation (MiB) | Warm sampled allocation (MiB) | Warm SQL calls | Of which transaction control | Warm SQL planning (ms) | Warm SQL execution (ms) |
|---|---:|---:|---:|---:|---:|---:|
| guicedee | 367.40 | 74.63 | 8550 | 900 | 0.00 | 160.60 |
| micronaut | 259.97 | 88.58 | 8100 | 450 | 0.00 | 181.45 |
| quarkus | 167.98 | 46.02 | 8100 | 450 | 0.00 | 158.71 |

Startup includes the first completed business transaction. Warm allocation covers the entire measured interval, not one request or retained memory. SQL times are database execution/planning totals and exclude application work, transport and CPU-quota waits. The table counts top-level SQL only; nested foreign-key checks are retained in the JSON and excluded from these totals to avoid double-counting execution time. They are not end-to-end transaction latency. Driver protocols can produce different transaction-control counters, including whether COMMIT appears as a separate statement. These counts do not imply omitted commits; the independent database checks verify committed visibility and rollback for every application.

## GuicedEE startup phases

Inclusive phase timings overlap and cannot be added.

| Phase | Instrumented duration (ms) |
|---|---:|
| application-startup | 10996.71 |
| context-discovery | 404.58 |
| pre-startup | 1006.95 |
| guice-module-discovery | 502.49 |
| guice-create-injector | 703.57 |
| post-startup | 7994.45 |
| post-hook-complete:com.guicedee.persistence.PersistenceStartup | 6901.61 |
| persistence persistence-xml (all) | 96.44 |
| persistence discovery-scan (scan-root) | 2.11 |
| persistence metadata-bootstrap (bench) | 2707.91 |
| persistence mapping-model (bench) | 794.73 |
| persistence session-factory (bench) | 3197.97 |

The current instrumented sample records **96.44 ms** for descriptor parsing and **2.11 ms** for persistence discovery. Metadata bootstrap (**2.708 s**) and session-factory creation (**3.198 s**) are the largest recorded persistence phases; mapping-model construction takes **0.795 s**. Discovery is nested within metadata bootstrap. These inclusive values must not be summed.


## Startup database work

SQL counters cover application launch through the first committed graph, excluding schema preparation. Database execution time excludes transport, application work and CPU-quota waits.

| Application | SQL calls | Database execution (ms) |
|---|---:|---:|
| guicedee | 23 | 7.14 |
| micronaut | 35 | 3.75 |
| quarkus | 30 | 3.70 |

## GuicedEE execution sample locations

The recording contains 219 startup and 622 warm execution samples. Counts below include any sample containing the method on its stack. Stacks overlap; counts are not elapsed phase times or additive percentages. Zero means that this recording did not sample the method.

| Stack location | Startup samples | Warm samples |
|---|---:|---:|
| `java.lang.ClassLoader.loadClass` | 15 | 0 |
| `org.hibernate.boot.internal.BootstrapContextImpl.createModelBuildingContext` | 2 | 0 |
| `org.hibernate.models.internal.AnnotationDescriptorBuilding.extractAttributeDescriptors` | 0 | 0 |
| `org.hibernate.boot.model.process.spi.MetadataBuildingProcess.complete` | 5 | 0 |
| `org.hibernate.internal.SessionFactoryImpl.<init>` | 37 | 0 |
| `org.hibernate.metamodel.model.domain.internal.MappingMetamodelImpl.finishInitialization` | 18 | 0 |
| `org.hibernate.query.internal.QueryEngineImpl.<init>` | 3 | 0 |
| `org.hibernate.query.hql.internal.StandardHqlTranslator.translate` | 25 | 0 |
| `org.hibernate.metamodel.internal.GuiceEntityProvider.get` | 2 | 0 |
| `com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor.captureCallScope` | 0 | 0 |
| `com.guicedee.rest.pathing.OperationRegistry.handleRequest` | 0 | 1 |
| `org.hibernate.reactive.util.async.impl.AsyncTrampoline$TrampolineInternal.unroll` | 18 | 180 |

## Focused allocation samples

These inclusive stack estimates locate work; zero means no allocation sample observed on that stack.

| GuicedEE stack | Startup (MiB) | Warm (MiB) |
|---|---:|---:|
| `com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor.existingScoper` | 0.00 | 0.00 |
| `com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor$ScopedUniSubscription.<init>` | 0.00 | 0.00 |
| `com.guicedee.client.IGuiceContext.loaderToSet` | 0.42 | 0.00 |
| `com.guicedee.persistence.implementations.PersistenceDescriptorParser.parse` | 1.49 | 0.00 |
| `com.guicedee.modules.services.hibernate.scan.ClassGraphScanner.scan` | 0.56 | 0.00 |
| `com.guicedee.modules.services.hibernate.scan.ExplicitPersistenceScanner.scan` | 0.28 | 0.00 |
| `org.hibernate.bytecode.internal.bytebuddy.BytecodeProviderImpl.getReflectionOptimizer` | 0.00 | 0.00 |
| `org.hibernate.bytecode.internal.bytebuddy.BytecodeProviderImpl.<init>` | 0.00 | 0.00 |
| `org.hibernate.jpa.boot.spi.PersistenceXmlParser.loadUrlWithJaxb` | 0.00 | 0.00 |
| `org.hibernate.boot.model.process.spi.MetadataBuildingProcess.complete` | 16.47 | 0.00 |
| `org.hibernate.boot.internal.BootstrapContextImpl.createModelBuildingContext` | 16.97 | 0.00 |
| `org.hibernate.models.CompleteAnnotationDescriptor.<init>` | 3.03 | 0.00 |
| `org.hibernate.models.CompleteAnnotationDescriptor.getAttributes` | 0.00 | 0.00 |
| `org.hibernate.models.internal.AnnotationDescriptorBuilding.extractAttributeDescriptors` | 3.03 | 0.00 |
| `org.hibernate.boot.model.source.internal.hbm.ModelBinder.prepare` | 0.00 | 0.00 |
| `org.hibernate.internal.SessionFactoryImpl.<init>` | 52.75 | 0.00 |
| `org.hibernate.metamodel.model.domain.internal.MappingMetamodelImpl.finishInitialization` | 26.35 | 0.00 |
| `org.hibernate.query.internal.QueryEngineImpl.<init>` | 12.57 | 0.00 |
| `org.hibernate.metamodel.internal.EntityInstantiatorPojoStandard.instantiate` | 2.59 | 0.00 |
| `org.hibernate.metamodel.internal.GuiceEntityProvider.get` | 2.59 | 0.00 |
| `com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor.captureCallScope` | 0.00 | 1.86 |
| `com.guicedee.rest.pathing.OperationRegistry.handleRequest` | 0.71 | 1.60 |
| `org.hibernate.query.sqm.tree.select.SqmQuerySpec.containsCollectionFetches` | 0.00 | 2.64 |
| `org.hibernate.reactive.util.async.impl.AsyncTrampoline$TrampolineInternal.unroll` | 32.14 | 45.49 |

[Machine-readable profile](persistence-profile.json) includes SQL statements, sample counts and JFR hashes. [Reproduce](../persistence/README.md#profile-startup-and-crud) with the same immutable application images. Full JFR recordings remain in ignored `target/`. Only this current diagnostic summary is published.
