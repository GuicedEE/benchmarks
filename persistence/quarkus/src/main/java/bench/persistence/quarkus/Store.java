package bench.persistence.quarkus;

import bench.persistence.model.*;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.persistence.EntityManager;
import jakarta.transaction.*;
import java.util.*;

@ApplicationScoped
public class Store {
    @Inject
    EntityManager em;

    @Inject
    TransactionManager transactionManager;

    private void active() {
        try {
            if (transactionManager.getStatus() != Status.STATUS_ACTIVE)
                throw new IllegalStateException("No active Narayana transaction");
        } catch (SystemException e) {
            throw new IllegalStateException(e);
        }
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
                "narayana-jta",
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
        return project(id);
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
