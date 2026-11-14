# Oracle JDK modular benchmark validation

The [linked-image audit](JLINK_AUDIT.md) separates valid JPMS packaging from minimal dependencies. Both current images contain 107 modules; 96 are in the mandatory application closure and 101 are reachable with installed SPI providers. The SPI linked runtime is 168.8 MiB; Docker's 473.2 MiB figure includes compressed and unpacked image-store accounting.

The separate [Quarkus native project](quarkus-native/README.md) compiles a Linux ELF executable and runs it without a JVM. This is distinct from application jlink. Its first [passing capped smoke comparison](results/20261114-153428/summary.json) passed all 15 capabilities for both Quarkus JVM and native. Repeated six-variant results are recorded in [RESULTS.md](RESULTS.md).

Preparing native exposed SDK wrapper relocation defects: both wrappers now preserve the platform `org.ietf` and compiler-provided `org.graalvm` APIs, and Firebase preserves Conscrypt's JNI package names. The benchmark supplies relocated native metadata and dependency-guarded compatibility substitutions. No application module descriptor is removed. Normal Maven builds still work without a native compiler.

The implementation follows `.agents/skills/guicedee-cloud-app/references/dockerfile-jlink.md`: dedicated `packaging: jlink` modules, a single application dependency, `maven-jlink-plugin` 3.1.0 with ASM 9.11.1, and generated launchers. Oracle JDK 25 was used locally. Application modules and their dependencies reside in `lib/modules`; `jdk.jlink` is absent.

Commercetools 20.4.0 is grouped as `commercetools.sdk.java.api`, including its GraphQL client models and HTTP implementation. Javassist is excluded from that bundle and resolved through the existing modular wrapper. Firebase Admin 9.12.0 remains `firebase.admin`. Both upstream versions are managed by Versioner/StandaloneBOM.

## Verified locally

- Both application-linked images built successfully.
- Both generated launchers passed the full fixture/emulator capability checks.
- Three runs each of module-path SPI/scanner and linked SPI/scanner passed: **12/12 eligible runs**, 100 measured requests and 20 warmups per run.
- Seven harness tests passed.
- Results: [summary](results/20261114-124721/summary.json), [linked image hashes and module lists](results/20261114-124721/linked-image-verification.json).

These are unrestricted Windows host measurements, not Linux/container resource-limit results. Docker was unavailable during that local batch. Historical JDK-only jlink measurements are invalid for application-module comparisons and are not reused.

## Verified on Linux after the Docker reset

The Oracle Linux builder now makes Maven's extracted launcher executable and installs `binutils` in the build stage for jlink's debug stripping. Both application images build successfully through their Maven jlink modules. Each linked runtime contains 107 modules (18 JDK modules plus the application and dependencies), including the correct application module, and runs its generated `bin/benchmark` launcher.

The [default-JVM container matrix](results/20261114-134115/summary.json) passed all 15 capability checks on all 15 fresh starts, with 450 successful measured warm requests. It compares module-path SPI/scanner, their application-linked images, and Quarkus fast-JAR at 250m CPU / 500 MiB RAM. All images use Oracle JDK 25.0.5.0.3+1-LTS-2; image IDs, module-image hashes, launchers and source provenance are in the [environment record](results/20261114-134115/environment.json). See [RESULTS.md](RESULTS.md) for the complete comparison and tuning profiles.

The [C1 matrix](results/20261114-134836/summary.json) repeats the same 15 starts and 450 measured requests with `TieredStopAtLevel=1` applied equally. It also passes all capability gates, uses the same image IDs, and has no measured request failures or OOM kills.
