package bench.persistence.guicedee;

import bench.persistence.model.Graph;
import com.google.inject.Inject;
import com.google.inject.Provider;
import com.google.inject.Singleton;
import com.guicedee.client.IGuiceContext;
import com.guicedee.vertx.spi.Verticle;
import io.smallrye.mutiny.Uni;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;
import java.util.Map;
import java.util.function.Supplier;

@Path("/") @Produces(MediaType.APPLICATION_JSON) @Singleton @Verticle("persistence-rest")
public class Resource {
    @Inject private Provider<Store> store;
    @GET @Path("ready") public Uni<Response> ready() { return response(() -> store.get().ready()); }
    @POST @Path("graphs/{id}") public Uni<Response> create(@PathParam("id") long id) { return response(() -> store.get().create(id, false)); }
    @POST @Path("graphs/{id}/rollback") public Uni<Response> rollback(@PathParam("id") long id) { return response(() -> store.get().create(id, true)); }
    @GET @Path("graphs/{id}") public Uni<Response> read(@PathParam("id") long id) { return response(() -> store.get().read(id)); }
    @POST @Path("graphs/{id}/update") public Uni<Response> update(@PathParam("id") long id) { return response(() -> store.get().update(id)); }
    @DELETE @Path("graphs/{id}") public Uni<Response> delete(@PathParam("id") long id) { return response(() -> store.get().delete(id)); }
    private Uni<Response> response(Supplier<Uni<Map<String,Object>>> action) {
        // The HTTP listener can precede database post-startup. Never lazily initialize
        // an unfinished SessionFactory from a request's event-loop thread.
        if (!IGuiceContext.instance().getLoadingFinished().succeeded()) {
            return Uni.createFrom().item(Response.status(503).entity(Map.of("error","STARTING")).build());
        }
        return action.get().map(value -> Response.ok(value).build()).onFailure().recoverWithItem(error -> {
            int status = error instanceof Graph.MissingGraph ? 404 : error instanceof Graph.RollbackProbe ? 409 : 500;
            return Response.status(status).entity(Map.of("error", status == 409 ? "ROLLBACK_PROBE" : status == 404 ? "NOT_FOUND" : "DATABASE_FAILURE")).build();
        });
    }
}
