package bench.persistence.guicedee;

import bench.persistence.model.*;
import com.google.inject.Inject;
import com.google.inject.Singleton;
import io.smallrye.mutiny.Uni;
import java.util.*;
import java.util.function.Function;
import org.hibernate.reactive.mutiny.Mutiny;

@Singleton
public class Store {
    @Inject
    private Mutiny.SessionFactory factory;

    public Uni<Map<String, Object>> ready() {
        return factory.withStatelessSession(session ->
                        session.createNativeQuery("select 1", Integer.class).getSingleResult())
                .map(value -> Map.of(
                        "ready",
                        value == 1,
                        "entities",
                        factory.getMetamodel().getEntities().size(),
                        "transactionMode",
                        "hibernate-reactive-stateless",
                        "ormVersion",
                        org.hibernate.Version.getVersionString()));
    }

    private Uni<List<Object[]>> select(Mutiny.StatelessSession session, long id) {
        return session.createQuery(Graph.PROJECTED_QUERY, Object[].class)
                .setParameter("id", id)
                .getResultList();
    }

    // Hibernate manages the session lifecycle; each write awaits its transaction before returning.
    private <T> Uni<T> transaction(Function<Mutiny.StatelessSession, Uni<T>> work) {
        return factory.withStatelessSession(session -> session.withTransaction(tx -> work.apply(session)));
    }

    public Uni<Map<String, Object>> create(long id, boolean rollback) {
        // Hibernate's ordered loop avoids a scoped Uni per entity. Explicit zero
        // batch size preserves one SQL statement per row and the shared contract.
        return transaction(session -> session.insertAll(0, Graph.create(id).toArray())
                .chain(() -> rollback
                        ? Uni.createFrom().failure(new Graph.RollbackProbe())
                        : select(session, id).map(Graph::project)));
    }

    public Uni<Map<String, Object>> read(long id) {
        return factory.withStatelessSession(session -> select(session, id).map(Graph::project));
    }

    public Uni<Map<String, Object>> update(long id) {
        return transaction(session -> select(session, id).map(Graph::detached).chain(values -> {
            Graph.update(values);
            return session.updateAll(0, values.toArray())
                    .chain(() -> select(session, id))
                    .map(Graph::project);
        }));
    }

    public Uni<Map<String, Object>> delete(long id) {
        return transaction(session -> select(session, id)
                .map(Graph::detached)
                .chain(values -> session.deleteAll(0, Graph.reverse(values).toArray()))
                .replaceWith(Map.<String, Object>of("deleted", 15, "id", id)));
    }
}
