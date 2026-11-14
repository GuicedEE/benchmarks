# Quarkus wrapped-SDK control

This optional control compiles the Quarkus adapter with the same wrapped Firebase and
commercetools SDK artifacts used by GuicedEE. The default public comparison uses the
independent [quarkus-standard](../quarkus-standard/README.md) application.

From the repository root:

```shell
python tools/build.py --docker --runtime native --quarkus-dependencies wrapped
python tools/compare.py --docker --firebase --runtime native --quarkus-dependencies wrapped
```

The compatibility sources and relocated SDK metadata also support GuicedEE native. They
are functional build inputs, not retained experimental outputs. Native metadata is tied
to exact SDK hashes; changed SDKs require a fresh passing trace. The importer and relocation
tools preserve upstream conditions and read each wrapper's embedded shade recipe.

The native compiler uses the same pinned Mandrel builder as the other native variants.
Application descriptors are preserved. Never relabel wrapped-SDK results as normal-dependency
Quarkus results; packaging and dependency resolution are deliberately different.
