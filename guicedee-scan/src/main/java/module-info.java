module bench.guicedee.scan {
    requires comparison.common;
    requires com.guicedee.rest;
    requires com.guicedee.faulttolerance;
    requires com.guicedee.openapi;
    requires com.guicedee.swaggerui;
    requires transitive com.guicedee.metrics;
    requires transitive com.guicedee.telemetry;

    opens bench.guicedee to com.google.guice, com.guicedee.rest, tools.jackson.databind;
    opens bench.guicedee.rest to com.google.guice, com.guicedee.rest, com.guicedee.vertx, tools.jackson.databind;
    opens bench.guicedee.service to com.google.guice, com.guicedee.vertx;
}
