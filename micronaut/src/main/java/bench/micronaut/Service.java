package bench.micronaut;

import bench.workload.Workload;
import io.micrometer.core.instrument.MeterRegistry;
import io.micronaut.context.annotation.Value;
import io.micronaut.retry.annotation.Retryable;
import jakarta.annotation.PreDestroy;
import jakarta.inject.Singleton;
import java.time.Duration;
import java.util.Map;
import reactor.core.publisher.Mono;

@Singleton
public class Service {
    private final Workload workload;
    private final MeterRegistry metrics;

    public Service(
            @Value("${BENCH_UPSTREAM}") String upstream,
            @Value("${BENCH_PHASE_DIAGNOSTICS:false}") boolean diagnostics,
            MeterRegistry metrics) {
        workload = new Workload(upstream, diagnostics);
        this.metrics = metrics;
    }

    public Mono<Map<String, Object>> quote(Workload.Order order) {
        metrics.counter("benchmark_quotes").increment();
        return Mono.fromCompletionStage(() -> workload.quote(order));
    }

    @Retryable(attempts = "2", delay = "20ms")
    public Mono<String> retry(String id) {
        return Mono.fromCompletionStage(() -> workload.remote("/flaky/" + id));
    }

    public Mono<String> timeout() {
        return Mono.fromCompletionStage(() -> workload.remote("/slow")).timeout(Duration.ofMillis(50));
    }

    public Mono<Map<String, Object>> firebase(String id) {
        return Mono.fromCompletionStage(() -> workload.firebase(id));
    }

    @PreDestroy
    void close() throws Exception {
        workload.close();
    }
}
