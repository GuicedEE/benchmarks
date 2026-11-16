# Current persistence profile

Diagnostic batch `20261116-133122`; 150 measured reads and CRUD cycles per application.

**Instrumented diagnostics, not benchmark timings.** Use [RESULTS.md](../RESULTS.md) for the uninstrumented comparison.

JFR allocation weights are estimates; inclusive stacks overlap. Execution samples exclude native wait samples and do not measure elapsed phase time. Instrumentation changes timings. SQL statistics describe database work only.

JVM flags: `-Xms128m`, `-Xmx384m`, `-XX:ActiveProcessorCount=2`, `-Dlog4j.shutdownHookEnabled=false`, `-XX:StartFlightRecording=filename=/tmp/persistence.jfr,settings=profile,dumponexit=true,maxsize=64m,jdk.ExecutionSample#period=2ms`.

| Application | Startup sampled allocation (MiB) | Warm sampled allocation (MiB) | Warm SQL calls | Of which transaction control | Warm SQL planning (ms) | Warm SQL execution (ms) |
|---|---:|---:|---:|---:|---:|---:|
| guicedee | 366.68 | 73.71 | 8550 | 900 | 0.00 | 151.84 |
| micronaut | 262.51 | 88.25 | 8100 | 450 | 0.00 | 190.70 |
| quarkus | 167.23 | 44.87 | 8100 | 450 | 0.00 | 151.75 |

Startup includes the first completed business transaction. Warm allocation covers the entire measured interval, not one request or retained memory. SQL times are database execution/planning totals and exclude application work, transport and CPU-quota waits. The table counts top-level SQL only; nested foreign-key checks are retained in the JSON and excluded from these totals to avoid double-counting execution time. They are not end-to-end transaction latency. Driver protocols can produce different transaction-control counters, including whether COMMIT appears as a separate statement. These counts do not imply omitted commits; the independent database checks verify committed visibility and rollback for every application.

## GuicedEE startup phases

Inclusive phase timings overlap and cannot be added.

| Phase | Instrumented duration (ms) |
|---|---:|
| application-startup | 11198.04 |
| context-discovery | 494.11 |
| pre-startup | 997.94 |
| guice-module-discovery | 593.61 |
| guice-create-injector | 606.93 |
| post-startup | 8303.94 |
| post-hook-complete:com.guicedee.persistence.PersistenceStartup | 7598.12 |
| persistence persistence-xml (all) | 190.96 |
| persistence discovery-scan (scan-root) | 2.76 |
| persistence metadata-bootstrap (bench) | 3298.24 |
| persistence mapping-model (bench) | 1005.03 |
| persistence session-factory (bench) | 3290.88 |

The current instrumented sample records **190.96 ms** for descriptor parsing and **2.76 ms** for persistence discovery. Metadata bootstrap (**3.298 s**) and session-factory creation (**3.291 s**) are the largest recorded persistence phases; mapping-model construction takes **1.005 s**. Discovery is nested within metadata bootstrap. These inclusive values must not be summed.


## Startup database work

SQL counters cover application launch through the first committed graph, excluding schema preparation. Database execution time excludes transport, application work and CPU-quota waits.

| Application | SQL calls | Database execution (ms) |
|---|---:|---:|
| guicedee | 23 | 6.55 |
| micronaut | 36 | 5.45 |
| quarkus | 30 | 3.86 |

## GuicedEE execution sample locations

The recording contains 228 startup and 473 warm execution samples. Counts below include any sample containing the method on its stack. Stacks overlap; counts are not elapsed phase times or additive percentages. Zero means that this recording did not sample the method.

| Stack location | Startup samples | Warm samples |
|---|---:|---:|
| `java.lang.ClassLoader.loadClass` | 17 | 0 |
| `org.hibernate.boot.registry.classloading.internal.AggregatedClassLoader.getResources` | 0 | 0 |
| `org.hibernate.boot.registry.classloading.internal.AggregatedClassLoader.findClass` | 1 | 0 |
| `org.hibernate.boot.internal.BootstrapContextImpl.createModelBuildingContext` | 7 | 0 |
| `org.hibernate.models.internal.AnnotationDescriptorBuilding.extractAttributeDescriptors` | 1 | 0 |
| `org.hibernate.boot.model.process.spi.MetadataBuildingProcess.complete` | 9 | 0 |
| `org.hibernate.internal.SessionFactoryImpl.<init>` | 27 | 0 |
| `org.hibernate.metamodel.model.domain.internal.MappingMetamodelImpl.finishInitialization` | 19 | 0 |
| `org.hibernate.query.internal.QueryEngineImpl.<init>` | 0 | 0 |
| `org.hibernate.query.hql.internal.StandardHqlTranslator.translate` | 25 | 0 |
| `org.hibernate.metamodel.internal.GuiceEntityProvider.get` | 3 | 0 |
| `com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor.captureCallScope` | 0 | 0 |
| `com.guicedee.rest.pathing.OperationRegistry.handleRequest` | 0 | 4 |
| `org.hibernate.reactive.util.async.impl.AsyncTrampoline$TrampolineInternal.unroll` | 17 | 115 |

## Focused allocation samples

These inclusive stack estimates locate work; zero means no allocation sample observed on that stack.

| GuicedEE stack | Startup (MiB) | Warm (MiB) |
|---|---:|---:|
| `com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor.existingScoper` | 0.00 | 0.00 |
| `com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor$ScopedUniSubscription.<init>` | 0.00 | 0.00 |
| `com.guicedee.client.IGuiceContext.loaderToSet` | 0.42 | 0.00 |
| `org.hibernate.boot.registry.classloading.internal.AggregatedClassLoader.getResources` | 0.00 | 0.00 |
| `org.hibernate.boot.registry.classloading.internal.AggregatedClassLoader.findClass` | 0.28 | 0.00 |
| `com.guicedee.persistence.implementations.PersistenceDescriptorParser.parse` | 1.22 | 0.00 |
| `com.guicedee.modules.services.hibernate.scan.ClassGraphScanner.scan` | 0.49 | 0.00 |
| `com.guicedee.modules.services.hibernate.scan.ExplicitPersistenceScanner.scan` | 0.25 | 0.00 |
| `org.hibernate.bytecode.internal.bytebuddy.BytecodeProviderImpl.getReflectionOptimizer` | 0.00 | 0.00 |
| `org.hibernate.bytecode.internal.bytebuddy.BytecodeProviderImpl.<init>` | 0.00 | 0.00 |
| `org.hibernate.jpa.boot.spi.PersistenceXmlParser.loadUrlWithJaxb` | 0.00 | 0.00 |
| `org.hibernate.boot.model.process.spi.MetadataBuildingProcess.complete` | 16.36 | 0.00 |
| `org.hibernate.boot.internal.BootstrapContextImpl.createModelBuildingContext` | 16.45 | 0.00 |
| `org.hibernate.models.CompleteAnnotationDescriptor.<init>` | 3.57 | 0.00 |
| `org.hibernate.models.CompleteAnnotationDescriptor.getAttributes` | 0.00 | 0.00 |
| `org.hibernate.models.internal.AnnotationDescriptorBuilding.extractAttributeDescriptors` | 3.57 | 0.00 |
| `org.hibernate.boot.model.source.internal.hbm.ModelBinder.prepare` | 0.00 | 0.00 |
| `org.hibernate.internal.SessionFactoryImpl.<init>` | 53.79 | 0.00 |
| `org.hibernate.metamodel.model.domain.internal.MappingMetamodelImpl.finishInitialization` | 26.74 | 0.00 |
| `org.hibernate.query.internal.QueryEngineImpl.<init>` | 13.42 | 0.00 |
| `org.hibernate.metamodel.internal.EntityInstantiatorPojoStandard.instantiate` | 2.52 | 0.00 |
| `org.hibernate.metamodel.internal.GuiceEntityProvider.get` | 2.52 | 0.00 |
| `com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor.captureCallScope` | 0.00 | 0.00 |
| `com.guicedee.rest.pathing.OperationRegistry.handleRequest` | 0.73 | 0.00 |
| `org.hibernate.query.sqm.tree.select.SqmQuerySpec.containsCollectionFetches` | 0.00 | 0.57 |
| `org.hibernate.reactive.util.impl.CompletionStages.loop` | 1.98 | 8.57 |
| `org.hibernate.reactive.util.async.impl.AsyncTrampoline$TrampolineInternal.unroll` | 29.31 | 47.32 |

[Machine-readable profile](persistence-profile.json) includes SQL statements, sample counts and JFR hashes. [Reproduce](../persistence/README.md#profile-startup-and-crud) with the same immutable application images. Full JFR recordings remain in ignored `target/`. Only this current diagnostic summary is published.
