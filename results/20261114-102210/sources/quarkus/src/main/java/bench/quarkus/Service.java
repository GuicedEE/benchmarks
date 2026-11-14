package bench.quarkus;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import bench.workload.Workload;
import io.smallrye.mutiny.Uni;
import org.eclipse.microprofile.faulttolerance.*;
import java.util.Map;
@ApplicationScoped
public class Service {
    private final Workload workload = new Workload(org.eclipse.microprofile.config.ConfigProvider.getConfig().getValue("BENCH_UPSTREAM", String.class));
    @Inject io.micrometer.core.instrument.MeterRegistry metrics;
    
    public Uni<Map<String,Object>> quote(Workload.Order order) {
        metrics.counter("benchmark_quotes").increment();
        return Uni.createFrom().completionStage(() -> workload.quote(order));
    }
    @Retry(maxRetries=2, delay=20, jitter=0)
    public Uni<String> retry(String id) { return Uni.createFrom().completionStage(() -> workload.remote("/flaky/"+id)); }
    @Timeout(50)
    public Uni<String> timeout() { return Uni.createFrom().completionStage(() -> workload.remote("/slow")); }
    public Uni<Map<String,Object>> firebase(String id) { return Uni.createFrom().completionStage(() -> workload.firebase(id)); }
}
