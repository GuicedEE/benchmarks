package bench.persistence.guicedee;

import bench.persistence.model.*;
import com.google.inject.Inject;
import com.google.inject.Singleton;
import io.smallrye.mutiny.Uni;
import org.hibernate.reactive.mutiny.Mutiny;
import java.util.*;
import java.util.function.Function;

@Singleton
public class Store {
    @Inject private Mutiny.SessionFactory factory;

    public Uni<Map<String,Object>> ready() {
        return factory.withStatelessSession(session -> session.createNativeQuery("select 1", Integer.class)
            .getSingleResult()).map(value -> Map.of("ready", value == 1,
                "entities", factory.getMetamodel().getEntities().size(),
                "transactionMode", "hibernate-reactive-stateless", "ormVersion", org.hibernate.Version.getVersionString()));
    }

    private Uni<List<Object[]>> select(Mutiny.StatelessSession session, long id) {
        return session.createQuery(Graph.PROJECTED_QUERY, Object[].class).setParameter("id", id).getResultList();
    }

    // ActivityMaster's ownership pattern: one explicit session per write, closed on success or failure.
    private <T> Uni<T> transaction(Function<Mutiny.StatelessSession,Uni<T>> work) {
        return factory.openStatelessSession().chain(session -> session.withTransaction(tx -> work.apply(session))
            .eventually(session::close));
    }

    // A session belongs to one composed stream. Every SQL operation and the final commit is awaited.
    private Uni<Void> each(List<Row> rows, Function<Row,Uni<Void>> action) {
        Uni<Void> result = Uni.createFrom().voidItem();
        for (Row row : rows) result = result.chain(() -> action.apply(row));
        return result;
    }

    public Uni<Map<String,Object>> create(long id, boolean rollback) {
        return transaction(session -> each(Graph.create(id), session::insert)
            .chain(() -> rollback ? Uni.createFrom().failure(new Graph.RollbackProbe())
                                 : select(session, id).map(Graph::project)));
    }

    public Uni<Map<String,Object>> read(long id) {
        return factory.withStatelessSession(session -> select(session, id).map(Graph::project));
    }

    public Uni<Map<String,Object>> update(long id) {
        return transaction(session -> select(session, id).map(Graph::detached).chain(values -> {
            Graph.update(values);
            return each(values, session::update).chain(() -> select(session, id)).map(Graph::project);
        }));
    }

    public Uni<Map<String,Object>> delete(long id) {
        return transaction(session -> select(session, id).map(Graph::detached)
            .chain(values -> each(Graph.reverse(values), session::delete))
            .replaceWith(Map.<String,Object>of("deleted", 15, "id", id)));
    }
}
