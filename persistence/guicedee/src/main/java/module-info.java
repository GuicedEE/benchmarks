module bench.persistence.guicedee {
    requires bench.persistence.model;
    requires com.guicedee.persistence;
    requires com.guicedee.rest;
    requires com.guicedee.telemetry;
    requires io.vertx.sql.client.pg;
    // Vert.x exposes SCRAM as optional; this PostgreSQL application requires it.
    requires com.ongres.scram.client;

    opens bench.persistence.guicedee to
            com.google.guice,
            com.guicedee.vertx,
            com.guicedee.rest,
            tools.jackson.databind;

    provides com.guicedee.client.services.IGuiceDiscovery with
            bench.persistence.guicedee.Discovery;
    provides com.guicedee.client.services.lifecycle.IGuiceModule with
            bench.persistence.guicedee.Database;
}
