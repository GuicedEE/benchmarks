package bench.guicedee.service;

import bench.workload.Workload;
import com.guicedee.vertx.spi.Verticle;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import java.util.Map;
import org.eclipse.microprofile.faulttolerance.*;
import org.eclipse.microprofile.metrics.annotation.Counted;

@ApplicationScoped
@Verticle("bench-guicedee-service")
public class Service {
    @jakarta.inject.Inject
    @org.eclipse.microprofile.config.inject.ConfigProperty(name = "bench.upstream")
    private String upstream;

    @jakarta.inject.Inject
    @org.eclipse.microprofile.config.inject.ConfigProperty(name = "bench.phase.diagnostics")
    private boolean diagnostics;

    @jakarta.inject.Inject
    @org.eclipse.microprofile.config.inject.ConfigProperty(name = "bench.config.marker")
    private String configMarker;

    private Workload workload;

    @jakarta.annotation.PostConstruct
    public void initialize() {
        if (!"application-properties".equals(configMarker))
            throw new IllegalStateException("application.properties was not injected");
        workload = new Workload(upstream, diagnostics);
    }

    public Map<String, Object> configuration() {
        return Map.of("marker", configMarker, "upstream", upstream, "initialized", workload != null);
    }

    @Counted(name = "benchmark_quotes", absolute = true)
    public Uni<Map<String, Object>> quote(Workload.Order order) {

        return Uni.createFrom().completionStage(() -> workload.quote(order));
    }

    @Retry(maxRetries = 2, delay = 20, jitter = 0)
    public Uni<String> retry(String id) {
        return Uni.createFrom().completionStage(() -> workload.remote("/flaky/" + id));
    }

    @Timeout(50)
    public Uni<String> timeout() {
        return Uni.createFrom().completionStage(() -> workload.remote("/slow"));
    }

    public Uni<Map<String, Object>> firebase(String id) {
        return Uni.createFrom().completionStage(() -> workload.firebase(id));
    }
}
