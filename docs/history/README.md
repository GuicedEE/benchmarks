# Supporting investigations and archived measurements

Use [the current performance report](../../RESULTS.md) for the complete mode grids,
measurement definitions, conclusions and missing coverage. These documents retain detailed
experiments and their exact input revisions; they are not additional current-state rankings.

| Document | Scope |
|---|---|
| [Normal-dependency Quarkus native](../../STANDARD_QUARKUS_COMPARISON.md) | Detailed primary native experiment, configuration and validation |
| [Full measurement ledger](MEASUREMENT_LEDGER.md) | Archived successive local/JVM/jlink/native experiments and superseded baselines |
| [Linked module audit](../../JLINK_AUDIT.md) | Module closure and byte attribution for the complete JVM matrix images |
| [Startup and SDK diagnostics](../../PHASE_ANALYSIS.md) | Instrumented scanning, injector and SDK investigation |
| [OpenAPI investigation](../../OPENAPI_OPTIMIZATION.md) | Controlled original/final linked-image experiment and compatibility details |
| [Native integration](../../GUICEDEE_NATIVE.md) | Initial native support and its measured artifact revisions |
| [Native footprint audit](../../NATIVE_OPTIMIZATION.md) | Reachability, startup and footprint experiments with wrapped SDKs |
| [Modular validation](../../MODULAR-VALIDATION.md) | Packaging and functional checks, separate from performance evidence |
| [Original external comparison](../PERFORMANCE_ANALYSIS.MD) | Historical source report; the original application template was unavailable |
| [Raw result index](../../results/README.md) | All retained measured, failed and diagnostic batches |

Raw samples and their immutable checksums remain in `results/`. The current report is a
generated view over selected complete experiment groups, not an edit of the historical evidence.
