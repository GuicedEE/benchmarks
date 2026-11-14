# Linked application size and dependency audit

Measured on 14 November 2026 against the **same immutable Linux images** used in the current [six-variant comparison](RESULTS.md#current-linux-native-comparison). Both GuicedEE images are valid named-module application images, but their packaged dependency graphs are **not minimal**. Linking succeeds; it does not establish that every packaged module, class or resource is needed by this workload.

## What the reported size means

| Measurement | SPI | Scanner |
|---|---:|---:|
| Docker local image-store disk usage | 473.2 MiB | 473.4 MiB |
| Sum of unpacked Docker layer sizes | 286.2 MiB | 286.2 MiB |
| Linked runtime directory, including application | 168.8 MiB | 168.9 MiB |
| `lib/modules` within that runtime | 135.2 MiB | 135.2 MiB |

The daemon uses `io.containerd.snapshotter.v1`. Its image-store accounting retains compressed content and unpacked snapshots. The 473 MiB figure is neither the linked runtime size nor the registry download size. Shared layers also mean it is not exclusive incremental disk consumption per image. See [Docker's storage explanation](https://docs.docker.com/engine/storage/containerd/#disk-space-usage).

The SPI image's OS layer is 115.5 MiB; the linked-runtime layer is 169.0 MiB including layer overhead. The runtime's `lib/server/libjvm.so` is 26.3 MiB. Maven, its repository and the full builder JDK are not copied into the linked final stage. Exact byte counts, layer sizes, image IDs and `lib/modules` hashes are in [the verification record](results/jlink-audit-verification.json).

## Module reachability

Both SPI and scanner have the following counts:

| Resolution policy | Modules |
|---|---:|
| Installed in the linked image | 107 (18 JDK, 89 application/library) |
| Application root plus mandatory `requires` closure | 96 |
| Application root plus service binding within the installed image | 101 |

The audit uses `ModuleFinder.ofSystem()` and `Configuration.empty().resolve()` / `resolveAndBind()` inside each actual image, without starting the application. It retains `requires static`, `uses` and `provides` in its evidence. The 101-module result considers **only providers already shipped in the image**. It is not a prediction for enabling `--bind-services` against the entire builder JDK, which can expose additional providers and dependencies. Installed modules are not necessarily initialized or scanned at startup.

`maven-jlink-plugin` **3.1.0** adds every resolved dependency-module name to `--add-modules`. This was checked in the installed plugin's `JLinkMojo.execute()` bytecode: it collects configured roots, then appends every key from `getModulePathElements()`. Therefore adding just `<addModules>bench.guicedee</addModules>` to the existing configuration would **not** narrow the graph. The current POMs neither supply a narrower root policy nor enable service binding.

These 11 installed modules are outside the mandatory application closure:

| Module | Added by service binding within this image? |
|---|---|
| `com.google.j2objc.annotations` | No |
| `com.guicedee.xmlrepresentation` | No |
| `com.sun.istack.runtime` | Yes, provider dependency |
| `com.sun.xml.txw2` | Yes, provider dependency |
| `io.netty.tcnative.classes.openssl` | No |
| `jakarta.el` | No |
| `jakarta.validation` | No |
| `org.apache.commons.io` | No |
| `org.eclipse.angus.activation` | Yes, provider |
| `org.glassfish.jaxb.core` | Yes, provider dependency |
| `org.glassfish.jaxb.runtime` | Yes, provider |

Together these 11 contain **1.47 MiB of stored resources** in the SPI module image. The six outside the service-bound closure contain **0.62 MiB**. These are measured payloads, not measured savings from a rebuilt image. Static/reflection-driven optional features still need capability checks before removal; the graph alone is not a safe deletion list.

## Where the bytes are

These are stored resource bytes from `jimage list --verbose`, using compressed size when present. They exclude the shared image index and metadata; uncompressed module totals would overstate disk usage.

| Module | Stored resources |
|---|---:|
| `firebase.admin` | 53.91 MiB |
| `commercetools.sdk.java.api` | 28.10 MiB |
| `java.base` | 10.79 MiB |
| `java.desktop` | 8.18 MiB |
| `java.xml` | 3.43 MiB |
| `com.guicedee.swaggerui` | 2.88 MiB |

The two SDK wrappers account for **82.01 MiB**, about 63% of stored module resources. They bundle and relocate their dependency trees into large named modules. Both are genuinely referenced by the shared workload, but jlink includes their full module contents, including SDK products, models, transports and resources beyond the exercised calls. [jlink resolves modules and their dependencies](https://docs.oracle.com/en/java/javase/25/docs/specs/man/jlink.html); it does not infer class/method reachability from the benchmark requests.

There is concrete platform-specific excess inside those bundles: the Linux amd64 image retains **9.52 MiB of compressed native resources for Windows, macOS or AArch64**. The verification record lists all ten files, mostly Firebase's Conscrypt and gRPC libraries. Platform-specific filtering belongs in the target image build; the portable SDK wrapper must retain support for other application targets.

## Dependency origins and cleanup priorities

The Maven dependency tree and installed JPMS descriptors establish these paths:

| Inclusion | Origin and implication |
|---|---|
| XML/JAXB | REST's Maven dependency on `xml-representation` brings in JAXB although REST's JPMS descriptor does not require XML representation. An opt-in XML adapter would avoid this default packaging. |
| CDI API / EL | Vert.x declares mandatory transitive `jakarta.cdi`; Maven's CDI API dependency brings EL. A source search found no direct CDI package references in Vert.x. This is a candidate for removal from the base Vert.x module, subject to consumer validation. |
| ClassGraph in SPI image | `com.guicedee.client` requires ClassGraph. Disabling scanning does not remove this module dependency; excluding it requires an optional scanner adapter and API review. |
| Telemetry | REST references `GuicedTelemetry`, and the benchmark explicitly includes the telemetry module, although `.env` sets `TELEMETRY_ENABLED=false`. Disabling the feature does not remove its module dependency; making it optional requires an adapter change. |
| HTTP/3 and QUIC | The linked `io.vertx.core` descriptor requires Netty HTTP/3. An HTTP-only fixture still receives that mandatory dependency. |
| `java.desktop` | Mandatory incoming edges include Commons Lang, Javassist and Log4j; JAXB runtime also requires it. It cannot simply be excluded while those descriptors remain unchanged. |

The largest packaging opportunities are target-specific SDK resources and better SDK module granularity. Correcting unnecessary mandatory dependencies and making XML/CDI/scanning boundaries explicit is valuable architecturally, but dropping the currently unreachable modules alone will not remove hundreds of megabytes. A narrower linker policy must preserve SPI providers and explicit application overrides. After any such change, rebuild both SPI/scanner images and rerun the full fixture capability gate before comparing timings.

This audit changes no application dependencies, module descriptors or measured images. It does not claim a startup improvement. Existing timings remain attached to their original image IDs.

## Evidence and reproduction

- [SPI descriptor and resource inventory](results/jlink-module-audit.json)
- [Scanner descriptor and resource inventory](results/jlink-scan-module-audit.json)
- [Size, image identity, native resources and verification](results/jlink-audit-verification.json)
- [Audit source](tools/LinkGraphAudit.java)

From the DevSuite root with JDK 25 and Docker, use a fresh output filename to retain earlier evidence:

```powershell
New-Item -ItemType Directory -Force benchmarks/docker/analysis/link-audit | Out-Null
javac -d benchmarks/docker/analysis/link-audit benchmarks/tools/LinkGraphAudit.java
$auditDirectory = (Resolve-Path benchmarks/docker/analysis/link-audit).Path
docker run --rm --mount "type=bind,source=$auditDirectory,target=/audit,readonly" --entrypoint java devsuite-bench-guicedee-jlink:local -cp /audit LinkGraphAudit bench.guicedee > benchmarks/results/jlink-module-audit-new.json
# For scanner: use devsuite-bench-guicedee-scan-jlink:local and root bench.guicedee.scan.
docker image inspect devsuite-bench-guicedee-jlink:local
docker history --no-trunc --human=false devsuite-bench-guicedee-jlink:local
docker run --rm --entrypoint du devsuite-bench-guicedee-jlink:local -sb /opt/java/openjdk
```

For stored-byte attribution, copy `/opt/java/openjdk/lib/modules` from the image with `docker cp`, then run host `jimage list --verbose` on the copy. Group entries by `Module:` and sum `Compressed` when nonzero, otherwise `Size`. The audit verified every SPI module's resource count and uncompressed-byte total against `ModuleReader`, and verified the copied image's SHA-256 against the container. Compare image IDs with the recorded verification before applying this report to newly built tags.
