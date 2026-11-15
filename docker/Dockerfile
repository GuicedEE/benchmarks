FROM oraclelinux:9-slim AS stock-runtime
RUN microdnf install -y tar gzip curl ca-certificates && microdnf clean all
RUN curl -fL https://download.oracle.com/java/25/latest/jdk-25_linux-x64_bin.tar.gz -o /tmp/jdk.tar.gz \
    && mkdir -p /opt/java/openjdk && tar -xzf /tmp/jdk.tar.gz -C /opt/java/openjdk --strip-components=1 \
    && sha256sum /tmp/jdk.tar.gz > /oracle-jdk-sha256.txt && rm /tmp/jdk.tar.gz
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH=/opt/java/openjdk/bin:$PATH
FROM stock-runtime AS os-source
RUN rm -rf /opt/java/openjdk
FROM scratch AS common-os
COPY --from=os-source / /
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH=/opt/java/openjdk/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8
WORKDIR /app
COPY docker/build-provenance.json build-provenance.json
ENTRYPOINT ["/opt/java/openjdk/bin/java"]

FROM common-os AS base
COPY --from=stock-runtime /opt/java/openjdk /opt/java/openjdk

FROM base AS guicedee
COPY guicedee/.env .env
COPY guicedee/target/comparison-guicedee-1.0-SNAPSHOT.jar app.jar
COPY guicedee/target/lib/ lib/
CMD ["--module-path", "/app/app.jar:/app/lib", "-m", "bench.guicedee/bench.guicedee.Main"]

FROM base AS quarkus
COPY quarkus/target/quarkus-app/ ./
CMD ["-jar", "/app/quarkus-run.jar"]

FROM base AS guicedee-scan
COPY guicedee-scan/.env .env
COPY guicedee-scan/target/comparison-guicedee-scan-1.0-SNAPSHOT.jar app.jar
COPY guicedee-scan/target/lib/ lib/
ENV GUICEDEE_DISCOVERY_MODE=scan
CMD ["--module-path", "/app/app.jar:/app/lib", "-m", "bench.guicedee.scan/bench.guicedee.Main"]

FROM stock-runtime AS maven-build-base
ARG GUICEDEE_VERSION=2.6.0
RUN microdnf install -y binutils && microdnf clean all
ARG MAVEN_VERSION=4.0.0-rc-7
ADD https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/${MAVEN_VERSION}/apache-maven-${MAVEN_VERSION}-bin.zip /tmp/maven.zip
RUN cd /opt && jar xf /tmp/maven.zip && chmod +x /opt/apache-maven-${MAVEN_VERSION}/bin/mvn && rm /tmp/maven.zip
ENV PATH=/opt/apache-maven-4.0.0-rc-7/bin:$PATH
COPY docker/repository/ /root/.m2/repository/
WORKDIR /src
COPY pom.xml pom.xml
COPY common/ common/
COPY guicedee/pom.xml guicedee/pom.xml
COPY guicedee/src/ guicedee/src/
COPY guicedee-scan/pom.xml guicedee-scan/pom.xml
COPY guicedee-scan/src/ guicedee-scan/src/
COPY quarkus/pom.xml quarkus/pom.xml
COPY quarkus/src/ quarkus/src/
COPY quarkus-native/pom.xml quarkus-native/pom.xml
COPY quarkus-standard/pom.xml quarkus-standard/pom.xml
COPY guicedee-native/pom.xml guicedee-native/pom.xml
COPY guicedee-jlink/ guicedee-jlink/
COPY guicedee-scan-jlink/ guicedee-scan-jlink/

FROM maven-build-base AS application-build
RUN mvn -B -ntp -pl guicedee-jlink,guicedee-scan-jlink -am package -Pjlink -Dguicedee.version=$GUICEDEE_VERSION -DskipTests

FROM common-os AS guicedee-jlink
COPY --from=application-build /src/guicedee-jlink/target/maven-jlink/default /opt/java/openjdk
COPY guicedee/.env .env
ENTRYPOINT ["/opt/java/openjdk/bin/benchmark"]

FROM quay.io/quarkus/ubi9-quarkus-mandrel-builder-image:jdk-25@sha256:c0ff31764f70469795db5513d674e4721fd8e7e761beddbff741ef5d84e79ed3 AS native-build
ARG GUICEDEE_VERSION=2.6.0
USER root
COPY --from=maven-build-base /opt/apache-maven-4.0.0-rc-7 /opt/maven
COPY --from=maven-build-base /root/.m2/repository /root/.m2/repository
COPY --from=maven-build-base /src /src
WORKDIR /src
COPY quarkus-native/src/ quarkus-native/src/
COPY quarkus-native/native-metadata-inputs.json quarkus-native/native-metadata-inputs.json
RUN native-image --version > /native-build-info.txt && \
    /opt/maven/bin/mvn -B -ntp -pl quarkus-native -am package -Pnative,wrapped-control -Dguicedee.version=$GUICEDEE_VERSION -DskipTests && \
    sha256sum /src/quarkus-native/target/*-runner >> /native-build-info.txt

FROM common-os AS quarkus-native
COPY --from=native-build /src/quarkus-native/target/*-runner /app/application
COPY --from=native-build /native-build-info.txt /app/native-build-info.txt
ENTRYPOINT ["/app/application"]

FROM quay.io/quarkus/ubi9-quarkus-mandrel-builder-image:jdk-25@sha256:c0ff31764f70469795db5513d674e4721fd8e7e761beddbff741ef5d84e79ed3 AS guicedee-native-build
ARG GUICEDEE_VERSION=2.6.0
USER root
COPY --from=maven-build-base /opt/apache-maven-4.0.0-rc-7 /opt/maven
COPY --from=maven-build-base /root/.m2/repository /root/.m2/repository
COPY --from=maven-build-base /src /src
WORKDIR /src
COPY quarkus-native/src/ quarkus-native/src/
COPY guicedee-native/src/ guicedee-native/src/
COPY guicedee-native/build-native.sh guicedee-native/build-native.sh
COPY guicedee-native/NativeModuleAccess.java guicedee-native/NativeModuleAccess.java
COPY guicedee-native/native-resources.txt guicedee-native/native-resources.txt
COPY guicedee-native/native-excluded-providers.txt guicedee-native/native-excluded-providers.txt
ARG NATIVE_AUDIT=false
ARG NATIVE_DESKTOP=false
ARG NATIVE_CLOUD_CONTROL_PLANE=false
ARG NATIVE_FULL_REFLECTION=false
RUN NATIVE_AUDIT=$NATIVE_AUDIT NATIVE_DESKTOP=$NATIVE_DESKTOP NATIVE_CLOUD_CONTROL_PLANE=$NATIVE_CLOUD_CONTROL_PLANE NATIVE_FULL_REFLECTION=$NATIVE_FULL_REFLECTION /opt/maven/bin/mvn -B -ntp -pl guicedee-native -am package -Pnative,native-app -Dguicedee.version=$GUICEDEE_VERSION -DskipTests

FROM common-os AS guicedee-native
COPY --from=guicedee-native-build /src/guicedee-native/target/application /app/application
COPY --from=guicedee-native-build /src/guicedee-native/target/*.so /app/
COPY --from=guicedee-native-build /src/guicedee-native/target/native-build-info.txt /app/native-build-info.txt
COPY --from=guicedee-native-build /src/guicedee-native/target/native-build-statistics.json /app/native-build-statistics.json
COPY guicedee/.env .env
ENTRYPOINT ["/app/application"]

FROM common-os AS guicedee-scan-jlink
COPY --from=application-build /src/guicedee-scan-jlink/target/maven-jlink/default /opt/java/openjdk
COPY guicedee-scan/.env .env
ENV GUICEDEE_DISCOVERY_MODE=scan
ENTRYPOINT ["/opt/java/openjdk/bin/benchmark"]

# Independent Quarkus build: only the upstream BOM and published SDK/extension dependencies.
# Its Maven cache contains no staged GuicedEE artifacts or inherited workspace configuration.
FROM quay.io/quarkus/ubi9-quarkus-mandrel-builder-image:jdk-25@sha256:c0ff31764f70469795db5513d674e4721fd8e7e761beddbff741ef5d84e79ed3 AS quarkus-standard-source
USER root
ADD https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/4.0.0-rc-7/apache-maven-4.0.0-rc-7-bin.zip /tmp/maven.zip
RUN cd /opt && jar xf /tmp/maven.zip && chmod +x /opt/apache-maven-4.0.0-rc-7/bin/mvn && rm /tmp/maven.zip
ENV PATH=/opt/apache-maven-4.0.0-rc-7/bin:$PATH
WORKDIR /src/quarkus-standard
COPY common/src/main/java/bench/ /src/common/src/main/java/bench/
COPY quarkus/src/main/java/ /src/quarkus/src/main/java/
COPY quarkus-standard/pom.xml quarkus-standard/BuildProvenance.java /src/quarkus-standard/
COPY quarkus-standard/src/ /src/quarkus-standard/src/

FROM quarkus-standard-source AS quarkus-standard-jvm-build
RUN --mount=type=cache,id=quarkus-standard-m2,target=/root/.m2 \
    mvn -B -ntp package dependency:build-classpath -Dmdep.outputFile=target/classpath.txt -DskipTests && \
    java BuildProvenance.java

FROM base AS quarkus-standard
COPY --from=quarkus-standard-jvm-build /src/quarkus-standard/target/quarkus-app/ /app/
COPY --from=quarkus-standard-jvm-build /src/quarkus-standard/target/build-provenance.json /app/build-provenance.json
CMD ["-jar", "/app/quarkus-run.jar"]

FROM quarkus-standard-source AS quarkus-standard-native-build
RUN --mount=type=cache,id=quarkus-standard-m2,target=/root/.m2 \
    native-image --version > /native-build-info.txt && \
    mvn -B -ntp package dependency:build-classpath -Pnative -Dmdep.outputFile=target/classpath.txt -DskipTests && \
    java BuildProvenance.java && sha256sum target/*-runner >> /native-build-info.txt

FROM common-os AS quarkus-standard-native
COPY --from=quarkus-standard-native-build /src/quarkus-standard/target/*-runner /app/application
COPY --from=quarkus-standard-native-build /native-build-info.txt /app/native-build-info.txt
COPY --from=quarkus-standard-native-build /src/quarkus-standard/target/build-provenance.json /app/build-provenance.json
ENTRYPOINT ["/app/application"]

# Same compiler, Maven, machine and cache policy for all measured build modes.
# No build output is reused: compare_builds.py runs clean and offline for every sample.
FROM quay.io/quarkus/ubi9-quarkus-mandrel-builder-image:jdk-25@sha256:c0ff31764f70469795db5513d674e4721fd8e7e761beddbff741ef5d84e79ed3 AS build-benchmark
USER root
COPY --from=maven-build-base /opt/apache-maven-4.0.0-rc-7 /opt/maven
COPY --from=maven-build-base /root/.m2/repository /root/.m2/repository
COPY --from=maven-build-base /src /src
ENV PATH=/opt/maven/bin:$PATH
WORKDIR /src
COPY quarkus-standard/src/ quarkus-standard/src/
COPY quarkus-native/src/ quarkus-native/src/
COPY guicedee-native/src/ guicedee-native/src/
COPY guicedee-native/build-native.sh guicedee-native/NativeModuleAccess.java guicedee-native/native-resources.txt guicedee-native/native-excluded-providers.txt guicedee-native/
COPY guicedee-native/native-trace-inputs.json guicedee-native/native-trace-inputs.json
COPY tools/compare_builds.py tools/compare_builds.py
