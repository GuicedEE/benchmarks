package bench.micronaut;

import bench.workload.Workload;
import io.micronaut.http.*;
import io.micronaut.http.annotation.*;
import io.swagger.v3.oas.annotations.Operation;
import java.util.Map;
import reactor.core.publisher.Mono;

@Controller("/")
public class Resource {
    private final Service service;

    public Resource(Service service) {
        this.service = service;
    }

    @Get("/ready")
    public Map<String, Object> ready() {
        return Map.of("ready", true);
    }

    @Post("/quote{?persist}")
    @Operation(summary = "Vendor SDK REST and GraphQL shipping quote")
    public Mono<HttpResponse<?>> quote(
            @Body Workload.Order order, @QueryValue(defaultValue = "false") boolean persist) {
        if (order == null || order.sku() == null || order.sku().isBlank() || order.quantity() < 1)
            return Mono.just(error(400, "INVALID_ORDER"));
        return service.quote(order)
                .flatMap(body -> persist ? service.firebase(order.sku()).thenReturn(body) : Mono.just(body))
                .<HttpResponse<?>>map(HttpResponse::ok)
                .onErrorReturn(error(502, "UPSTREAM_FAILURE"));
    }

    @Get("/retry/{id}")
    public Mono<HttpResponse<?>> retry(String id) {
        return service.retry(id)
                .<HttpResponse<?>>map(v -> HttpResponse.ok(Map.of("result", v)))
                .onErrorReturn(error(502, "UPSTREAM_FAILURE"));
    }

    @Get("/timeout")
    public Mono<HttpResponse<?>> timeout() {
        return service.timeout()
                .<HttpResponse<?>>map(v -> HttpResponse.ok(Map.of("result", v)))
                .onErrorReturn(error(504, "UPSTREAM_TIMEOUT"));
    }

    @Get("/firebase/{id}")
    public Mono<HttpResponse<?>> firebase(String id) {
        return service.firebase(id)
                .<HttpResponse<?>>map(HttpResponse::ok)
                .onErrorReturn(error(502, "FIREBASE_FAILURE"));
    }

    private HttpResponse<?> error(int status, String code) {
        return HttpResponse.status(HttpStatus.valueOf(status))
                .body(Map.of("error", Map.of("code", code, "status", status)));
    }
}
