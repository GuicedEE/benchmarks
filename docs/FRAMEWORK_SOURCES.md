# Companion framework sources

This repository owns the benchmark applications, fixtures, harness, build recipes, native
metadata and retained evidence. Framework implementations remain in their own repositories.

## Workspace layout

The complete matrix is developed with this repository at `DevSuite/benchmarks` and framework
checkouts at `DevSuite/GuicedEE`. The existing commands prefixed with `benchmarks/` run from
that DevSuite root. `build.ps1 -InstallGuicedEE`, the GuicedEE native build and repository-staging
tools deliberately use that layout.

The recorded images used locally built GuicedEE 2.5.1 artifacts containing changes under
development. Their identities and available source snapshots are in each retained batch's
`environment.json`. A released artifact with the same Maven version is not automatically
the same input. The recorded Docker images and staged Maven cache are local build artifacts;
they are not distributed by this Git repository. Rebuilds with changed framework inputs
require new measurements and, where applicable, refreshed native metadata.

The independent `quarkus-standard` project can be built without DevSuite or GuicedEE artifacts.
See the standalone instructions in [the running guide](../RUNNING.md#run).

## Native support

The GuicedEE native adapter uses `com.guicedee:native-image`, built from
`DevSuite/GuicedEE/native-image`, alongside the modified Guice integration in
`DevSuite/GuicedEE/services/Google/guice-core`. The native support module was a local source
directory when this repository was populated; its publication is outside this benchmark
repository. A matching companion checkout/artifact is required to rebuild that variant.
The [native benchmark documentation](../guicedee-native/README.md) describes the SPI contract
and validates the recorded SDK hashes before packaging.

## OpenAPI

The provider changes belong in `DevSuite/GuicedEE/openapi` (the
[GuicedEE OpenAPI repository](https://github.com/GuicedEE/OpenAPI)). The benchmark's
[OpenAPI report](../OPENAPI_OPTIMIZATION.md) records the configuration used, comparisons,
and compatibility implications. It does not package a separate framework implementation.

## Version boundary

DevSuite's GuicedEE 2.6.0 preparation includes further SDK extraction and module-graph work.
The retained measurements identify their actual inputs, predominantly locally built 2.5.1
artifacts. They must not be relabeled as a measurement of a later release. Release notes
remain owned by the companion framework workspace.

## Microbenchmarks

This repository contains the service-level comparison, not an invented reconstruction of
earlier core JMH runs. The earlier `GuicedEE/inject/benchmarks/README.md` reference was absent
from the checkout when this repository was populated. Component benchmarks need their own
sources and results before being presented as reproducible evidence here.
