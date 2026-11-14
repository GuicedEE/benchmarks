#!/bin/sh
set -eu
cd "$(dirname "$0")"
native-image --version > target/native-build-info.txt
java NativeModuleAccess.java target/lib target/native-module-access.args native-resources.txt target/modular-resources
# Native Image loads Java modules from a directory but does not discover each JAR's embedded
# reachability metadata there. Enumerate the JARs so library-owned metadata is applied as well.
MODULE_PATH=$(find target/lib -maxdepth 1 -type f -name '*.jar' | sort | paste -sd ':' -)
set --
if [ "${NATIVE_DESKTOP:-false}" != true ]; then
    # This reference application is a headless HTTP service, like the Quarkus
    # native build. Keep ServiceLoader enabled for all application/library SPIs.
    set -- -J-Djava.awt.headless=true \
        -H:ServiceLoaderFeatureExcludeServices=javax.sound.midi.spi.MidiDeviceProvider,javax.sound.midi.spi.MidiFileReader,javax.sound.midi.spi.MidiFileWriter,javax.sound.midi.spi.SoundbankReader,javax.sound.sampled.spi.AudioFileReader,javax.sound.sampled.spi.AudioFileWriter,javax.sound.sampled.spi.FormatConversionProvider,javax.sound.sampled.spi.MixerProvider
fi
if [ "${NATIVE_AUDIT:-false}" = true ]; then
    set -- "$@" -H:+PrintAnalysisCallTree -H:PrintAnalysisCallTreeType=CSV -H:+PrintHeapHistogram
fi
native-image -J-Xmx8g --no-fallback -O2 -march=x86-64-v3 --gc=serial \
    -H:+UnlockExperimentalVMOptions -H:BuildOutputJSONFile=target/native-build-statistics.json "$@" \
    @target/native-module-access.args \
    -H:ConfigurationFileDirectories=target/modular-resources \
    --module-path "target/comparison-guicedee-native-1.0-SNAPSHOT.jar:$MODULE_PATH" \
    --add-modules=bench.guicedee.nativeimage,jdk.unsupported \
    --add-reads=firebase.admin=org.graalvm.nativeimage \
    --add-reads=commercetools.sdk.java.api=org.graalvm.nativeimage \
    --features=com.guicedee.nativeimage.GuiceNativeFeature \
    --initialize-at-run-time=io.netty \
    --exclude-config '.*firebase-admin.*' '/META-INF/native-image/.*' \
    --exclude-config '.*commercetools.*' '/META-INF/native-image/.*' \
    -m bench.guicedee/bench.guicedee.Main -o target/application
sha256sum target/application >> target/native-build-info.txt
