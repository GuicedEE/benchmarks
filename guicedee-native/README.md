# GuicedEE native benchmark

This module compiles the SPI application into a Linux executable using the optional
`com.guicedee:native-image` SPI. It keeps the application's module descriptor and real
Guice DI, lifecycle, interception and reactive framework integrations.

From the repository root:

```shell
python tools/build.py --docker --framework guicedee --runtime native
python tools/compare.py --docker --firebase --runtime native --runs 7 --requests 30 --warmup 10
```

The comparison also requires the Quarkus native image; build both by omitting `--framework`.
The build reads dependencies from the selected Maven repository. It never compiles a sibling
framework checkout. `--guicedee-version` and `--maven-repository` select explicit test inputs.

The native adapter shares wrapped-SDK compatibility sources/metadata with `quarkus-native`.
`NativeModuleAccess.java` opens dependency-owned substitutions to the image builder and maps
traced resources to their JPMS modules. Application descriptors are never removed. Netty
initializes at runtime. Traced SDK hashes are checked before accepting native metadata.

To refresh metadata, build the GuicedEE JVM image, extract `libnative-image-agent.so` from the
pinned Mandrel builder, then run:

```shell
python tools/trace_native.py /path/to/libnative-image-agent.so target/native-trace --framework guicedee
python tools/build.py --docker --framework guicedee --runtime native --trace-directory target/native-trace
```

The trace must pass all 15 capabilities. It is diagnostic and excluded from timings. The
metadata covers this workload's SDK operations, including Firestore; additional application
features require their own trace and capability checks.

`--audit-native` retains compiler call-tree/used-class reports in the builder.
`--include-desktop` retains Java Sound audio/MIDI providers, excluded by this headless fixture.
Application/library service loading remains enabled. The final image includes emitted native
sidecar libraries and `/app/native-build-statistics.json`, and launches `/app/application`.
Compiler work is outside the measured application's CPU/memory quota.
