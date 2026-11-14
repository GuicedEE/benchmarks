package bench.guicedee.service;

import com.google.inject.Singleton;
import bench.workload.Workload;
import com.guicedee.vertx.spi.Verticle;
import io.smallrye.mutiny.Uni;
import org.eclipse.microprofile.faulttolerance.*;
import org.eclipse.microprofile.metrics.annotation.Counted;

import java.util.Map;

@Singleton
@Verticle("bench-guicedee-service")
public class Service {
    private final Workload workload = new Workload(com.guicedee.client.Environment.getSystemPropertyOrEnvironment(
            "BENCH_UPSTREAM",
            "http://127.0.0.1:18089"), Boolean.parseBoolean(com.guicedee.client.Environment.getSystemPropertyOrEnvironment(
                    "BENCH_PHASE_DIAGNOSTICS", "false")));

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
