package bench.quarkus;

import bench.workload.Workload;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.util.Map;

@Path("/")
@Produces(MediaType.APPLICATION_JSON)
@ApplicationScoped
public class Resource {
    @Inject
    Service service;

    @GET
    @Path("ready")
    public Map<String, Object> ready() {
        return Map.of("ready", true);
    }

    @POST
    @Path("quote")
    @Consumes(MediaType.APPLICATION_JSON)
    @org.eclipse.microprofile.openapi.annotations.Operation(summary = "Vendor SDK REST and GraphQL shipping quote")
    public Uni<Response> quote(Workload.Order order, @QueryParam("persist") boolean persist) {
        if (order == null || order.sku() == null || order.sku().isBlank() || order.quantity() < 1) {
            return Uni.createFrom().item(error(400, "INVALID_ORDER"));
        }
        return service.quote(order)
                .flatMap(body -> persist
                        ? service.firebase(order.sku())
                                .map(saved -> Response.ok(body).build())
                        : Uni.createFrom().item(Response.ok(body).build()))
                .onFailure()
                .invoke(Throwable::printStackTrace)
                .onFailure()
                .recoverWithItem(f -> error(502, "UPSTREAM_FAILURE"));
    }

    @GET
    @Path("retry/{id}")
    public Uni<Response> retry(@PathParam("id") String id) {
        return service.retry(id)
                .map(v -> Response.ok(Map.of("result", v)).build())
                .onFailure()
                .recoverWithItem(f -> error(502, "UPSTREAM_FAILURE"));
    }

    @GET
    @Path("timeout")
    public Uni<Response> timeout() {
        return service.timeout()
                .map(v -> Response.ok(Map.of("result", v)).build())
                .onFailure()
                .recoverWithItem(f -> error(504, "UPSTREAM_TIMEOUT"));
    }

    @GET
    @Path("firebase/{id}")
    public Uni<Response> firebase(@PathParam("id") String id) {
        return service.firebase(id)
                .map(body -> Response.ok(body).build())
                .onFailure()
                .recoverWithItem(f -> error(502, "FIREBASE_FAILURE"));
    }

    private Response error(int status, String code) {
        return Response.status(status)
                .entity(Map.of("error", Map.of("code", code, "status", status)))
                .build();
    }
}
