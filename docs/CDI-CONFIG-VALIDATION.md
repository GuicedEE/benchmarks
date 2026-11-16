# CDI/config runtime validation

Validated on 2026-11-15 against GuicedEE 2.6.0. These are capability smoke runs,
not performance rankings: one start per variant, three measured requests, one warmup.
Other workspace jobs were active during validation. Linux runs enforce 0.25 CPU / 500 MiB.

| Runtime | Variant | Capability checks | Result |
|---|---|---|---|
| Windows application jlink | `guicedee-jlink` | 15/15 | Pass |
| Windows application jlink | `guicedee-scan-jlink` | 15/15 | Pass |
| Windows application jlink | `guicedee-cdi-jlink` | 16/16 | Pass |
| Windows application jlink | `guicedee-cdi-spi-jlink` | 16/16 | Pass |
| Linux application jlink | `guicedee-jlink` | 15/15 | Pass |
| Linux application jlink | `guicedee-scan-jlink` | 15/15 | Pass |
| Linux application jlink | `guicedee-cdi-jlink` | 16/16 | Pass |
| Linux application jlink | `guicedee-cdi-spi-jlink` | 16/16 | Pass |
| Linux native | `guicedee-cdi-native` | 16/16 | Pass |
| Linux native | `guicedee-native` | 15/15 | Pass |

The CDI checks verify Jakarta injection/initialization, the packaged properties marker,
and the environment override. Shared checks cover real vendor SDK requests, Firestore,
retry/timeout behavior, metrics, OpenAPI and Swagger UI.

All 34 Python harness tests and six targeted Config regression checks passed.
Linked images retain the application modules and complete dependency graph and use the
generated module launcher. Native images are Linux ELF executables without a bundled JVM.

Two compatibility repairs were required:

- The config loader now handles `jrt:` and native resource URLs in SPI mode, preserving profile pairing.
- GuicedEE 2.6.0 native recipes exclude obsolete relocated Commercetools Netty adapters; the optional OpenSSL substitution checks that its target exists.

Runtime scanner discovery is unsupported in native mode. Launching the native CDI image
with `GUICEDEE_DISCOVERY_MODE=scan` was verified to reject startup explicitly. Native
coverage uses SPI discovery; it must not be labelled as a native scanner benchmark.

Evidence is retained locally (ignored measurement output):

- Windows application jlink: `target/runs/20261115-194117/summary.json` and `environment.json`.
- Linux application jlink: `target/runs/20261115-202017/summary.json` and `environment.json`.
- Linux native: `target/runs/20261115-202209/summary.json` and `environment.json`.
- Native scanner rejection: `target/cdi-native-scan-rejection.log`.
- Framework config tests: `target/cdi-config-regression.log`.
- Harness tests: `target/cdi-final-harness.log`.

Linux images use the `cdi-matrix` tag; the run manifests record their immutable IDs.
The native support artifact was built locally as 2.6.0; this validation does not publish it.

See [RUNNING.md](../RUNNING.md#jakarta-cdi-and-applicationproperties-comparison) for
reproducible build, trace and measurement commands.
