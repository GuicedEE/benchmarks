# PostgreSQL persistence comparison

Three independent JVM applications execute the same operations over **15 related entities
and 19 foreign keys**. Quarkus uses Hibernate ORM with Narayana-managed JTA transactions.
GuicedEE uses Hibernate Reactive's stateless sessions, explicit writes and resource-local
transactions through the persistence module. Writes use `withStatelessSession` with
a composed `withTransaction`; Hibernate manages session opening and closing on success
or failure. Reads also use `withStatelessSession`. Micronaut uses Hibernate ORM with its
own transaction interceptor and resource-local Hibernate transaction manager, plus HikariCP.
Blocking operations run on Micronaut's blocking executor. This compares these application patterns;
it does not isolate the transaction manager or compare distributed XA transactions.

| Project | Role |
|---|---|
| `model` | Shared Jakarta Persistence mappings, graph construction and joined read query; JPMS descriptor retained |
| `guicedee` | Modular GuicedEE application, SPI discovery, `DatabaseModule`, reactive stateless operations |
| `quarkus` | Independent Quarkus BOM, Hibernate ORM, PostgreSQL JDBC, explicit Narayana extension |
| `micronaut` | Independent Micronaut platform, Hibernate ORM, HikariCP and Micronaut-managed local transactions |
| `schema.sql` | Identical schema created before each application launch, then validated by Hibernate |

The model comprises Country, Region, Address, Customer, Supplier, Category, Product,
Warehouse, Inventory, PurchaseOrder, OrderLine, Payment, Shipment, ShipmentItem and
AuditEntry. Each graph has one row per entity. Every row has a supplied identifier,
a label and an optimistic-lock version. Associations have explicit foreign keys and
no cascades. All adapters insert in dependency order and delete in reverse order.

The modular GuicedEE launcher grants explicit read edges between Hibernate ORM and the
model module for runtime proxy generation. The model package is opened to Hibernate, and
the application resolves PostgreSQL's optional SCRAM module. All module descriptors remain
intact. The model build attaches an `enhanced` classifier for GuicedEE using Hibernate's
Maven enhancer, following ActivityMaster's parent POM. Quarkus receives the original
compiled model and performs its normal enhancement. Pre-enhancing Quarkus's input would
apply two enhancement pipelines to the same bytecode. Both artifacts come from the same
compiled classes; their hashes and all source hashes are recorded and checked. Hibernate
is a provided model dependency, so each application retains its own runtime ORM version.
The shared entity setter preserves dirty tracking. Micronaut receives the original model
and generates an entity discovery index at compile time with `@Introspected`, without
changing the shared entities. Its read opens a Hibernate session for the same single
projection query, without an explicit transaction; writes use `@Transactional` and verify
an active transaction before touching the graph.

GuicedEE reuses the parsed persistence-unit descriptor during factory creation and
avoids speculative pools outside Hibernate's ownership. Common Jakarta Persistence
descriptors use a streaming XML parser; unsupported descriptor grammar delegates to Hibernate.
Both paths reject DTDs, external entities, malformed XML and excessive XML complexity.
Fallback reads validated byte snapshots. The descriptor size limit defaults to 8 MiB;
`GUICEDEE_PERSISTENCE_XML_MAX_BYTES` allows larger application descriptors.
`GUICEDEE_PERSISTENCE_XML_PARSER=hibernate` selects the original parser after the same
security checks. Environment
placeholders and descriptor values are preserved. Its persistence integration
uses standard Hibernate property access for enhanced entities and defers the default
Byte Buddy provider where the classloader arrangement permits it. Proxy generation,
runtime enhancement and ordinary entities retain Hibernate's provider behavior.
`guicedee.persistence.optimize_enhanced_entities=false` restores the original accessor
generation for applications that benefit from it. No benchmark-specific startup flags
or transaction shortcuts select this behavior. Application source and packaged-JAR hashes
are retained with this persistence cohort.

The Hibernate wrapper resolves a Guice provider once per entity instantiator; each
entity still goes through that provider, preserving injection and configured scopes.
Enhanced entity interception uses Hibernate's existing superclass setup. Annotation-only
units skip the legacy HBM binder when their collected XML binding list is empty.
Nonempty XML bindings retain the complete mapping path; schema validation and transaction
readiness remain part of startup.

## Run

Use the same JDK 25, Maven 4, Python and Docker prerequisites as the main suite. PostgreSQL
runs in an isolated container and a temporary Docker volume owned by the runner. Only
resources created by this invocation are removed when it finishes.

```shell
python tools/build_persistence.py
python tools/compare_persistence.py --runs 3 --requests 30 --warmup 10
```

Run from the repository root. `--guicedee-version` and `--maven-repository` select explicit
framework artifacts during the build. Quarkus resolves normal upstream dependencies under
its own BOM; Micronaut uses its upstream platform. All runtime images use the same immutable JDK base. Source and packaged-JAR
hashes are embedded in each image and retained with results. `--tiered` applies C1 tuning
equally to all applications; keep that profile separate from default-JVM results.

GuicedEE defaults live in `guicedee/.env`, with environment overrides for `DB_HOST`,
`DB_PORT`, `DB_NAME`, `DB_USER` and `DB_PASSWORD`. Quarkus and Micronaut use those same variables.
The persistence unit resolves GuicedEE's environment placeholders; `Database` only selects
the PostgreSQL implementation and pool defaults. GuicedEE manages its lifecycle through
the module binding, without duplicate application startup/destroy service registrations.
The runner provides its isolated database settings. Each application has a five-connection
pool, disabled second-level/query caching, disabled statement batching and PostgreSQL's
READ COMMITTED isolation. The database retains `fsync`, synchronous commit and full-page
writes; its data directory uses a Docker volume rather than an in-memory filesystem.

## Timing and correctness

Each application runs at **0.25 CPU / 500 MiB**, with the same 128/384 MiB heap and two
active processors. PostgreSQL has a separate **2 CPU / 1 GiB** allocation and serves one
measured application at a time. Fresh JVMs and databases alternate between frameworks.
Schema creation, database startup, Docker pulls and image builds are outside timing.

The startup clock begins before launching the application container. Readiness requires
the completed persistence lifecycle, all 15 mapped entities and a successful database query.
The first business response inserts all 15 rows, executes the shared joined query, and
waits for the transaction to commit. A listening HTTP port is insufficient.

Fourteen checks gate each start. They verify the schema and transaction mode, complete
graph creation, independently visible committed rows and all 19 foreign-key values, joined reads, all 15 updates and
version increments, rollback after 15 successful inserts, absence from a new transaction,
duplicate-key handling, concurrent independent transactions, FK enforcement, dependency-order
deletion, absence of leaked rows after measurement and graceful lifecycle shutdown with
no remaining database connections. Shutdown verification is outside the timed samples. Independent checks use `psql` from
outside the application session. Any failed check prevents publication of the comparison.

Warm samples interleave a read of an unchanged graph with a complete CRUD cycle. Each cycle
makes four HTTP requests: create, read, update and delete. The three writes each have their
own transaction; the single-query read has no explicit transaction in any application.
It performs 15 inserts, 15 updates, 15 deletes and five joined queries. All response fields
are checked. Timings include HTTP transport, ORM work and transaction completion; they are
sequential request latencies, not saturation throughput or a bare-database microbenchmark.

Quarkus and Micronaut use managed entities and dirty checking; GuicedEE explicitly updates detached
entities in a stateless session. Those differences are part of the requested comparison.
All use the same graph plan and joined scalar projection for response data, including all
identifiers, labels, versions and foreign-key values. GuicedEE prepares detached rows from
the projection for explicit updates/deletes, following ActivityMaster's lean stateless
pattern. Quarkus and Micronaut load managed entities for dirty checking and removal. Their ORM/driver
stacks can perform different hydration work; runtime versions and dependencies are recorded.

GuicedEE uses `insertAll(0, ...)`, `updateAll(0, ...)` and `deleteAll(0, ...)` inside
`withStatelessSession` / `withTransaction`. Hibernate executes the supplied rows in order;
the explicit zero batch size preserves individual SQL statements. This avoids building a
separate application-level reactive operator chain for every entity. All writes and the
final commit are still awaited before responding.

Pattern references: ActivityMaster's
[SessionUtils](https://github.com/Activity-Master/Client/blob/master/src/main/java/com/guicedee/activitymaster/fsdm/client/services/SessionUtils.java)
and [GeographyService](https://github.com/Activity-Master/GeographyMaster/blob/master/src/main/java/com/guicedee/activitymaster/geography/GeographyService.java).
Each graph has one row per entity type, so writes remain ordered; the same-type bulk batching
used by Geography's import workload is not part of this CRUD workload.

Only these three full-JDK persistence modes are measured here. The existing SDK comparison's
SPI/scanner, jlink and native results remain a separate workload and cannot be used as
persistence results.

## Profile startup and CRUD

```shell
python tools/compare_persistence.py --diagnostics --runs 1 --requests 150 --warmup 20
python tools/profile_persistence.py target/persistence-runs/<batch>
```

Diagnostics capture JFR in all JVMs, GuicedEE's inclusive startup phases and PostgreSQL
`pg_stat_statements` execution/planning counters. The summary separates startup through
the first committed graph from the warmed measurement interval. SQL counters are
subtracted at the measurement boundaries. JFR allocation weights are estimates and
inclusive stack totals overlap; they must not be summed. Native wait samples are excluded
from execution-sample summaries. Diagnostic timings are affected by instrumentation and
the publication gate rejects them, even if marked eligible. Full recordings and derived
summaries stay in ignored `target/`; rerun without `--diagnostics` for comparison tables.
The GuicedEE log also separates persistence XML parsing, GuicedEE discovery scanning, Hibernate metadata bootstrap,
mapping-model construction and session-factory construction. Startup SQL counters subtract the prelaunch snapshot,
so schema preparation is excluded from the reported database execution time.

## Publish the latest complete comparison

Raw executions and logs stay in ignored `target/persistence-runs/<batch>/`. Publication
replaces the single current persistence dataset; it does not accumulate prior runs.

```shell
python tools/render_persistence.py --publish target/persistence-runs/<batch>/summary.json
python tools/render_charts.py
python tools/verify_latest.py
python tools/render_performance.py --check
python tools/render_persistence.py --check
```

The [Quarkus transaction guide](https://quarkus.io/guides/transaction/) describes Narayana
and `@Transactional` boundaries. The [Hibernate Reactive reference](https://docs.hibernate.org/stable/reactive/reference/html_single/)
describes stateless-session semantics and the absence of an automatic persistence context.
