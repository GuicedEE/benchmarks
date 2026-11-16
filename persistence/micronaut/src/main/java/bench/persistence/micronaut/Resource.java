package bench.persistence.micronaut;

import bench.persistence.model.Graph;
import io.micronaut.http.*;
import io.micronaut.http.annotation.*;
import io.micronaut.scheduling.TaskExecutors;
import io.micronaut.scheduling.annotation.ExecuteOn;
import java.util.Map;
import java.util.function.Supplier;

@Controller("/")
@Consumes(MediaType.ALL)
@ExecuteOn(TaskExecutors.BLOCKING)
public class Resource {
    private final Store store;

    public Resource(Store store) {
        this.store = store;
    }

    @Get("/ready")
    public HttpResponse<?> ready() {
        return response(store::ready);
    }

    @Post("/graphs/{id}")
    public HttpResponse<?> create(long id) {
        return response(() -> store.create(id, false));
    }

    @Post("/graphs/{id}/rollback")
    public HttpResponse<?> rollback(long id) {
        return response(() -> store.create(id, true));
    }

    @Get("/graphs/{id}")
    public HttpResponse<?> read(long id) {
        return response(() -> store.read(id));
    }

    @Post("/graphs/{id}/update")
    public HttpResponse<?> update(long id) {
        return response(() -> store.update(id));
    }

    @Delete("/graphs/{id}")
    public HttpResponse<?> delete(long id) {
        return response(() -> store.delete(id));
    }

    private HttpResponse<?> response(Supplier<Map<String, Object>> action) {
        try {
            return HttpResponse.ok(action.get());
        } catch (Graph.MissingGraph e) {
            return HttpResponse.notFound(Map.of("error", "NOT_FOUND"));
        } catch (Graph.RollbackProbe e) {
            return HttpResponse.status(HttpStatus.CONFLICT).body(Map.of("error", "ROLLBACK_PROBE"));
        } catch (Exception e) {
            return HttpResponse.serverError(Map.of("error", "DATABASE_FAILURE"));
        }
    }
}
