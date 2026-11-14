# Result index

Read [../RESULTS.md](../RESULTS.md) for interpretation. JSON rows are evidence even when they fail. Do not select only successful requests from a failed startup or substitute newer sources for older image IDs.

| Directory | Purpose |
|---|---|
| `20261114-101345`, `20261114-101513` | Dependency integration failures; not performance baselines |
| `20261114-101729` | Local Windows smoke test, unrestricted host CPU |
| `20261114-102011` | Initial 250m/500Mi Docker smoke test |
| `20261114-102210` | Initial three-run capped baseline, 30 measured warm requests per run |
| `20261114-102719` | Refined capability checks against the initial immutable images |
| `20261114-103457` | Package-option discovery failure during integration; no valid GuicedEE startup timings |
| `20261114-104030` | SPI integration smoke test exposed the remaining raw fault-tolerance scan; overlapped image packaging, not a timing baseline |
| `20261114-104245` | Integrated SPI-only three-run capped batch, 30 measured warm requests per run |
| `20261114-104548` | Same SPI images, C1 JIT setting applied to both frameworks; three capped runs each |
| `20261114-105153` | Final rebuilt images with explicit shared-workload JPMS descriptor; one capped C1 capability smoke run |
| `20261114-110626` | `.env` configuration with no package/class options annotations; capped C1 capability smoke run |
| `20261114-110753` | Local `.env` configuration smoke run, verifying the application's working directory |
| `20261114-111122` | GuicedEE-only local smoke run with configuration annotations on Main and `.env` overrides |
| `20261114-112645` | Six-image smoke: separate verticle packages, provider-free scanner artifact, standard JRE and jlink runtimes |
| `20261114-112932` | Default-JVM six-variant matrix: three capped starts and 90 warm requests per variant; discovery/deployment evidence recorded |
| `20261114-113839` | Identical six images with C1 applied equally: three capped starts and 90 warm requests per variant |
| `20261114-121520` | Separate modular scanner project and framework fixes; failed fixture injection after Jakarta annotation edits without CDI; preserved diagnostic only |
| `20261114-122316` | Corrected Guice annotations and modular scanner project; framework fixes; six-variant C1 matrix with three starts per variant |
| `20261114-124721` | Full application-linked and module-path GuicedEE local Windows validation; unrestricted host, no Quarkus comparison |
| `20261114-134115` | Five-variant Linux application-jlink/default-JVM comparison after Docker reset; 15 eligible starts, 450 successful warm requests |
| `20261114-134836` | Same five immutable Linux images with equal C1 tuning; 15 eligible starts, 450 successful warm requests |
| `20261114-150143` | Initial native executable started but failed SDK capability checks; excluded from performance ranking |
| `20261114-151247`, `20261114-151503`, `20261114-152554` | Instrumented JVM native-image-agent diagnostics at 2 CPU / 2 GiB; all 15 capability checks passed; not performance comparisons |
| `native-agent-trace`, `native-agent-trace-2`, `native-agent-trace-3` | Raw reachability metadata from those diagnostics; trace 3 uses the corrected SDK wrappers |
| `20261114-153428` | Quarkus JVM/native capped capability smoke: both passed all 15 checks; single starts are not the repeated timing baseline |
| `20261114-154043` | Six-variant default-JVM/native comparison with corrected SDKs: 18 eligible starts and 540 successful measured requests |
| `20261114-154849` | Same six immutable images with C1 applied only to JVMs: 18 eligible starts and 540 successful measured requests |
| `20261114-155900`, `native-agent-final-validation` | Refined tracing-tool validation: all 15 capabilities and traced-image SDK hash checks passed; explicitly excluded from performance comparisons |
| `20261114-192338` | Startup/SDK phases and live scan/Guice inventories: three SPI jlink and three scanner jlink starts; all capabilities/captures passed; diagnostic only |
| `20261114-192632` | Quarkus JVM phases exposed duplicate workload construction through CDI proxies; capabilities passed but capture validation rejected the extra construction; retained diagnostic only |
| `20261114-192928` | Quarkus JVM phases with corrected capture validation: three starts passed all capabilities/captures; diagnostic only |
| `20261114-193232` | Both linked GuicedEE variants with diagnostics disabled: two starts passed 30 capabilities, retained ten Guice modules and emitted no phase output; functional smoke only |
| `20261114-194654` | Fresh original-image baseline for OpenAPI work: three capped starts per linked discovery variant |
| `20261114-195349` | Intermediate OpenAPI direct-generation/configuration-wiring candidate; all capabilities passed; retained exploratory batch |
| `20261114-200110` | Separate final OpenAPI candidate batch; noisy/worse end-to-end medians prompted the alternating control; retained in full |
| `20261114-200341` | Final OpenAPI candidate phases: six starts, 90 capabilities and 18 measured requests passed; instrumented, not a performance comparison |
| `20261114-200551` | Alternating original/final OpenAPI images: 12 starts, 180 capabilities and 60 measured requests passed; primary OpenAPI before/after comparison |
| `20261114-211508` | Failed initial GuicedEE native comparison; retained diagnostic only |
| `20261114-212404`, `20261114-212840` | Validated GuicedEE/Quarkus native comparisons using identical SDK wrappers |
| `20261114-221748`, `20261114-222751` | Paired native startup/footprint comparisons; the latter is the final shared-wrapper result |
| `20261114-221910` | Instrumented native startup/Guice phases; excluded from rankings |
| `20261114-222037` | Smaller initial-heap experiment; no material memory benefit |
| `20261114-225526`, `20261114-225644`, `20261114-230206`, `20261114-231028` | Standard-dependency Quarkus integration failures; excluded from rankings |
| `20261114-225944`, `quarkus-standard-native-trace` | Passing upstream-dependency JVM trace used for native metadata; instrumented, not a timing baseline |
| `20261114-231325`, `20261114-231541` | Passing standard Quarkus native/JVM capability diagnostics; not timing baselines |
| `20261114-231729`, `20261114-231959` | Standard-dependency Quarkus versus GuicedEE native; reversed initial orders; 28 starts, 420 checks and 840 requests pass |

Each run records environment/input provenance, per-application JSON and a summary. Local `.log`/`.args` files are retained on disk but ignored by Git. Original failed samples remain in place. Test/build logs at this directory's root are also local, ignored output.

The [retained-evidence manifest](retained-evidence.json) identifies the files published in
this repository and their exact byte hashes. New runs and unreferenced exploratory output
remain ignored until explicitly reviewed for inclusion; see [the policy](../docs/RETENTION.md).

The later read-only [jlink audit](../JLINK_AUDIT.md) uses the same six-variant batch's GuicedEE image IDs. `jlink-module-audit.json` and `jlink-scan-module-audit.json` contain the installed descriptors and application/service reachability; the SPI inventory additionally contains compressed resource sizes. `jlink-audit-verification.json` records byte counts, layer sizes, platform-specific native resources and image hashes. These are packaging diagnostics, not new performance samples.
