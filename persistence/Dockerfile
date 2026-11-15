ARG JAVA_IMAGE=eclipse-temurin:25-jdk
FROM ${JAVA_IMAGE} AS runtime
WORKDIR /app
EXPOSE 8080

FROM runtime AS guicedee
COPY guicedee/target/persistence-guicedee-1.0-SNAPSHOT.jar app.jar
COPY guicedee/target/lib/ lib/
COPY guicedee/.env .env
COPY target/guicedee-inputs.json benchmark-inputs.json
ENTRYPOINT ["java", "--add-reads=org.hibernate.orm.core=bench.persistence.model", "--add-reads=bench.persistence.model=org.hibernate.orm.core", "--module-path", "/app/app.jar:/app/lib", "-m", "bench.persistence.guicedee/bench.persistence.guicedee.Main"]

FROM runtime AS quarkus
COPY quarkus/target/quarkus-app/ ./
COPY target/quarkus-inputs.json benchmark-inputs.json
ENTRYPOINT ["java", "-jar", "/app/quarkus-run.jar"]
