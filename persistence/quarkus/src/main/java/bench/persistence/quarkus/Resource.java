package bench.persistence.quarkus;

import bench.persistence.model.Graph;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;
import java.util.Map;
import java.util.function.Supplier;

@Path("/") @Produces(MediaType.APPLICATION_JSON)
public class Resource {
    @Inject Store store;
    @GET @Path("ready") public Response ready() { return response(store::ready); }
    @POST @Path("graphs/{id}") public Response create(@PathParam("id") long id) { return response(() -> store.create(id,false)); }
    @POST @Path("graphs/{id}/rollback") public Response rollback(@PathParam("id") long id) { return response(() -> store.create(id,true)); }
    @GET @Path("graphs/{id}") public Response read(@PathParam("id") long id) { return response(() -> store.read(id)); }
    @POST @Path("graphs/{id}/update") public Response update(@PathParam("id") long id) { return response(() -> store.update(id)); }
    @DELETE @Path("graphs/{id}") public Response delete(@PathParam("id") long id) { return response(() -> store.delete(id)); }
    private Response response(Supplier<Map<String,Object>> action) {
        try { return Response.ok(action.get()).build(); }
        catch (Graph.MissingGraph e) { return Response.status(404).entity(Map.of("error","NOT_FOUND")).build(); }
        catch (Graph.RollbackProbe e) { return Response.status(409).entity(Map.of("error","ROLLBACK_PROBE")).build(); }
        catch (Exception e) { return Response.serverError().entity(Map.of("error","DATABASE_FAILURE")).build(); }
    }
}
