package bench.persistence.micronaut;

import bench.persistence.model.*;
import io.micronaut.transaction.annotation.Transactional;
import jakarta.inject.Singleton;
import jakarta.persistence.EntityManager;
import java.util.*;
import org.hibernate.SessionFactory;

@Singleton
public class Store {
    private final EntityManager em;
    private final SessionFactory factory;

    public Store(EntityManager em, SessionFactory factory) {
        this.em = em;
        this.factory = factory;
    }

    private void active() {
        if (!em.getTransaction().isActive())
            throw new IllegalStateException("No active Micronaut Hibernate transaction");
    }

    private List<Row> rows(long id) {
        return Graph.rows(em.createQuery(Graph.QUERY, Object[].class)
                .setParameter("id", id)
                .getResultList());
    }

    private Map<String, Object> project(long id) {
        return Graph.project(em.createQuery(Graph.PROJECTED_QUERY, Object[].class)
                .setParameter("id", id)
                .getResultList());
    }

    @Transactional
    public Map<String, Object> ready() {
        active();
        Number value = (Number) em.createNativeQuery("select 1").getSingleResult();
        return Map.of(
                "ready",
                value.intValue() == 1,
                "entities",
                em.getMetamodel().getEntities().size(),
                "transactionMode",
                "micronaut-hibernate",
                "ormVersion",
                org.hibernate.Version.getVersionString());
    }

    @Transactional
    public Map<String, Object> create(long id, boolean rollback) {
        active();
        Graph.create(id).forEach(em::persist);
        em.flush();
        if (rollback) throw new Graph.RollbackProbe();
        return project(id);
    }

    public Map<String, Object> read(long id) {
        try (var session = factory.openSession()) {
            return Graph.project(session.createQuery(Graph.PROJECTED_QUERY, Object[].class)
                    .setParameter("id", id)
                    .getResultList());
        }
    }

    @Transactional
    public Map<String, Object> update(long id) {
        active();
        Graph.update(rows(id));
        em.flush();
        return project(id);
    }

    @Transactional
    public Map<String, Object> delete(long id) {
        active();
        Graph.reverse(rows(id)).forEach(em::remove);
        em.flush();
        return Map.of("deleted", 15, "id", id);
    }
}
