# Current persistence profile

Diagnostic batch `20261116-170257`; 150 measured reads and CRUD cycles per application.

**Instrumented diagnostics, not benchmark timings.** Use [RESULTS.md](../RESULTS.md) for the uninstrumented comparison.

JFR allocation weights are estimates; inclusive stacks overlap. Execution samples exclude native wait samples and do not measure elapsed phase time. Instrumentation changes timings. SQL statistics describe database work only.

JVM flags: `-Xms128m`, `-Xmx384m`, `-XX:ActiveProcessorCount=2`, `-Dlog4j.shutdownHookEnabled=false`, `-XX:StartFlightRecording=filename=/tmp/persistence.jfr,settings=profile,dumponexit=true,maxsize=64m,jdk.ExecutionSample#period=2ms`.

| Application | Startup sampled allocation (MiB) | Warm sampled allocation (MiB) | Warm SQL calls | Of which transaction control | Warm SQL planning (ms) | Warm SQL execution (ms) |
|---|---:|---:|---:|---:|---:|---:|
| guicedee | 365.21 | 73.02 | 8550 | 900 | 0.00 | 151.26 |
| micronaut | 259.51 | 87.48 | 8100 | 450 | 0.00 | 184.81 |
| quarkus | 167.91 | 45.01 | 8100 | 450 | 0.00 | 153.10 |

Startup includes the first completed business transaction. Warm allocation covers the entire measured interval, not one request or retained memory. SQL times are database execution/planning totals and exclude application work, transport and CPU-quota waits. The table counts top-level SQL only; nested foreign-key checks are retained in the JSON and excluded from these totals to avoid double-counting execution time. They are not end-to-end transaction latency. Driver protocols can produce different transaction-control counters, including whether COMMIT appears as a separate statement. These counts do not imply omitted commits; the independent database checks verify committed visibility and rollback for every application.

## GuicedEE startup phases

Inclusive phase timings overlap and cannot be added.

| Phase | Instrumented duration (ms) |
|---|---:|
| application-startup | 10899.59 |
| context-discovery | 592.88 |
| pre-startup | 1198.28 |
| guice-module-discovery | 597.63 |
| guice-create-injector | 609.20 |
| post-startup | 7703.66 |
| post-hook-complete:com.guicedee.persistence.PersistenceStartup | 6800.01 |
| persistence persistence-xml (all) | 106.40 |
| persistence discovery-scan (scan-root) | 2.23 |
| persistence metadata-bootstrap (bench) | 2812.94 |
| persistence mapping-model (bench) | 893.68 |
| persistence session-factory (bench) | 2994.33 |

The current instrumented sample records **106.40 ms** for descriptor parsing and **2.23 ms** for persistence discovery. Metadata bootstrap (**2.813 s**) and session-factory creation (**2.994 s**) are the largest recorded persistence phases; mapping-model construction takes **0.894 s**. Discovery is nested within metadata bootstrap. These inclusive values must not be summed.


## Startup database work

SQL counters cover application launch through the first committed graph, excluding schema preparation. Database execution time excludes transport, application work and CPU-quota waits.

| Application | SQL calls | Database execution (ms) |
|---|---:|---:|
| guicedee | 23 | 6.69 |
| micronaut | 35 | 4.31 |
| quarkus | 30 | 3.55 |

## GuicedEE execution sample locations

The recording contains 209 startup and 510 warm execution samples. Counts below include any sample containing the method on its stack. Stacks overlap; counts are not elapsed phase times or additive percentages. Zero means that this recording did not sample the method.

| Stack location | Startup samples | Warm samples |
|---|---:|---:|
| `java.lang.ClassLoader.loadClass` | 12 | 0 |
| `org.hibernate.boot.registry.classloading.internal.AggregatedClassLoader.getResources` | 1 | 0 |
| `org.hibernate.boot.registry.classloading.internal.AggregatedClassLoader.findClass` | 0 | 0 |
| `org.hibernate.boot.models.internal.ClassLoaderServiceLoading.classForName` | 0 | 0 |
| `java.math.BigDecimal.<clinit>` | 0 | 0 |
| `org.hibernate.boot.internal.BootstrapContextImpl.createModelBuildingContext` | 5 | 0 |
| `org.hibernate.models.internal.AnnotationDescriptorBuilding.extractAttributeDescriptors` | 0 | 0 |
| `org.hibernate.boot.model.process.spi.MetadataBuildingProcess.complete` | 10 | 0 |
| `org.hibernate.internal.SessionFactoryImpl.<init>` | 23 | 0 |
| `org.hibernate.metamodel.model.domain.internal.MappingMetamodelImpl.finishInitialization` | 17 | 0 |
| `org.hibernate.query.internal.QueryEngineImpl.<init>` | 0 | 0 |
| `org.hibernate.query.internal.QueryEngineImpl.createFunctionRegistry` | 0 | 0 |
| `org.hibernate.engine.internal.UnsavedValueFactory.inferUnsavedVersionValue` | 1 | 0 |
| `org.hibernate.query.hql.internal.StandardHqlTranslator.translate` | 22 | 0 |
| `org.hibernate.metamodel.internal.GuiceEntityProvider.get` | 1 | 0 |
| `com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor.captureCallScope` | 0 | 0 |
| `com.guicedee.rest.pathing.OperationRegistry.handleRequest` | 0 | 7 |
| `org.hibernate.reactive.util.async.impl.AsyncTrampoline$TrampolineInternal.unroll` | 13 | 132 |

## Focused allocation samples

These inclusive stack estimates locate work; zero means no allocation sample observed on that stack.

| GuicedEE stack | Startup (MiB) | Warm (MiB) |
|---|---:|---:|
| `com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor.existingScoper` | 0.41 | 0.00 |
| `com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor$ScopedUniSubscription.<init>` | 0.00 | 0.00 |
| `com.guicedee.client.IGuiceContext.loaderToSet` | 0.00 | 0.00 |
| `org.hibernate.boot.registry.classloading.internal.AggregatedClassLoader.getResources` | 0.24 | 0.00 |
| `org.hibernate.boot.registry.classloading.internal.AggregatedClassLoader.findClass` | 0.33 | 0.00 |
| `org.hibernate.boot.models.internal.ClassLoaderServiceLoading.classForName` | 0.65 | 0.00 |
| `java.math.BigDecimal.<clinit>` | 0.00 | 0.00 |
| `com.guicedee.persistence.implementations.PersistenceDescriptorParser.parse` | 1.27 | 0.00 |
| `com.guicedee.modules.services.hibernate.scan.ClassGraphScanner.scan` | 0.67 | 0.00 |
| `com.guicedee.modules.services.hibernate.scan.ExplicitPersistenceScanner.scan` | 0.32 | 0.00 |
| `org.hibernate.bytecode.internal.bytebuddy.BytecodeProviderImpl.getReflectionOptimizer` | 0.00 | 0.00 |
| `org.hibernate.bytecode.internal.bytebuddy.BytecodeProviderImpl.<init>` | 0.00 | 0.00 |
| `org.hibernate.jpa.boot.spi.PersistenceXmlParser.loadUrlWithJaxb` | 0.00 | 0.00 |
| `org.hibernate.boot.model.process.spi.MetadataBuildingProcess.complete` | 16.33 | 0.00 |
| `org.hibernate.boot.internal.BootstrapContextImpl.createModelBuildingContext` | 14.33 | 0.00 |
| `org.hibernate.models.CompleteAnnotationDescriptor.<init>` | 3.35 | 0.00 |
| `org.hibernate.models.CompleteAnnotationDescriptor.getAttributes` | 0.00 | 0.00 |
| `org.hibernate.models.internal.AnnotationDescriptorBuilding.extractAttributeDescriptors` | 3.35 | 0.00 |
| `org.hibernate.boot.model.source.internal.hbm.ModelBinder.prepare` | 0.00 | 0.00 |
| `org.hibernate.internal.SessionFactoryImpl.<init>` | 53.37 | 0.00 |
| `org.hibernate.metamodel.model.domain.internal.MappingMetamodelImpl.finishInitialization` | 27.22 | 0.00 |
| `org.hibernate.query.internal.QueryEngineImpl.<init>` | 12.93 | 0.00 |
| `org.hibernate.query.internal.QueryEngineImpl.createFunctionRegistry` | 8.00 | 0.00 |
| `org.hibernate.engine.internal.UnsavedValueFactory.inferUnsavedVersionValue` | 2.23 | 0.00 |
| `org.hibernate.metamodel.internal.EntityInstantiatorPojoStandard.instantiate` | 2.23 | 0.00 |
| `org.hibernate.metamodel.internal.GuiceEntityProvider.get` | 2.23 | 0.00 |
| `com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor.captureCallScope` | 0.00 | 0.44 |
| `com.guicedee.rest.pathing.OperationRegistry.handleRequest` | 0.68 | 0.00 |
| `org.hibernate.query.sqm.tree.select.SqmQuerySpec.containsCollectionFetches` | 0.00 | 1.03 |
| `org.hibernate.reactive.util.impl.CompletionStages.loop` | 1.98 | 3.39 |
| `org.hibernate.reactive.util.async.impl.AsyncTrampoline$TrampolineInternal.unroll` | 29.73 | 45.49 |

[Machine-readable profile](persistence-profile.json) includes SQL statements, sample counts and JFR hashes. [Reproduce](../persistence/README.md#profile-startup-and-crud) with the same immutable application images. Full JFR recordings remain in ignored `target/`. Only this current diagnostic summary is published.
