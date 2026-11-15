module bench.persistence.model {
    requires transitive jakarta.persistence;
    exports bench.persistence.model;
    opens bench.persistence.model to org.hibernate.orm.core;
}
