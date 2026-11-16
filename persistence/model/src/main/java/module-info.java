module bench.persistence.model {
    requires transitive jakarta.persistence;
    requires static org.hibernate.orm.core;

    exports bench.persistence.model;

    opens bench.persistence.model to
            org.hibernate.orm.core;
}
