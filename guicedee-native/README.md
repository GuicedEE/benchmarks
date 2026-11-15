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

The DNS-based Firestore workload excludes the optional xDS, RLS, legacy grpclb and Google C2P control-plane
providers listed in `native-excluded-providers.txt`. Normal DNS, pick-first/round-robin,
transport and TLS providers remain. Pass `--include-cloud-control-plane` to `tools/build.py`
to restore the complete provider set (`NATIVE_CLOUD_CONTROL_PLANE=true` for the shell build).
This is an application choice, not a GuicedEE framework exclusion. Applications that use
those control-plane protocols must enable them and validate their own workload.

GuicedEE uses Native Image's ServiceLoader feature and does not inherit the wrapped Quarkus
control's blanket provider-constructor metadata. When excluding providers, the modular
metadata helper preserves constructors of the remaining providers using analysis-time
reachability conditions. A runtime `typeReached` guard is insufficient when ServiceLoader
queries a constructor before initializing the service class.

`BenchmarkNativeConfiguration` supplies runtime defaults of `allocator.type=pooled` and
`allocator.maxOrder=3` for Netty and its three relocated SDK copies, yielding 64 KiB chunks with the default
8 KiB page size. The chunk order matches [Quarkus's normal `maxOrder` default](https://github.com/quarkusio/quarkus/blob/main/extensions/netty/deployment/src/main/java/io/quarkus/netty/deployment/NettyProcessor.java).
It preserves pooling and allows larger payloads to use additional chunks. Override individual
defaults with `-D<prefix>.allocator.maxOrder=<value>` and `-D<prefix>.allocator.type=adaptive`
on the executable:

| Netty owner | Property prefix |
|---|---|
| Vert.x | `io.netty` |
| commercetools | `com.commercetools.internal.shaded.io.netty` |
| Firebase | `com.google.firebase.internal.shaded.io.netty` |
| Firebase gRPC transport | `com.google.firebase.internal.shaded.io.grpc.netty.shaded.io.netty` |

These defaults apply only to this native application; the JVM modes keep their existing
configuration. The normal Quarkus application and its dependency graph are unchanged.
