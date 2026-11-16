package bench.workload;

import java.util.Locale;
import java.util.concurrent.CompletionStage;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.function.Supplier;

/** First-use diagnostics only; all phase names are fixed literals, never request data. */
final class WorkloadTrace {
    private static final WorkloadTrace DISABLED = new WorkloadTrace("", false);
    private final boolean enabled;
    private final String operation;
    private final long origin;
    private final ConcurrentLinkedQueue<String> spans;

    WorkloadTrace(String operation, boolean enabled) {
        this.operation = operation;
        this.enabled = enabled;
        this.origin = enabled ? System.nanoTime() : 0;
        this.spans = enabled ? new ConcurrentLinkedQueue<>() : null;
    }

    static WorkloadTrace start(String operation, boolean enabled) {
        return enabled ? new WorkloadTrace(operation, true) : DISABLED;
    }

    <T> T sync(String name, Supplier<T> action) {
        if (!enabled) return action.get();
        long start = enabled ? System.nanoTime() : 0;
        boolean success = false;
        try {
            T result = action.get();
            success = true;
            return result;
        } finally {
            record(name, start, success);
        }
    }

    <T> CompletionStage<T> async(String name, Supplier<CompletionStage<T>> action) {
        if (!enabled) return action.get();
        long start = enabled ? System.nanoTime() : 0;
        try {
            return action.get().whenComplete((result, failure) -> record(name, start, failure == null));
        } catch (RuntimeException | Error failure) {
            record(name, start, false);
            throw failure;
        }
    }

    <T> CompletionStage<T> complete(CompletionStage<T> stage) {
        return enabled ? stage.whenComplete((result, failure) -> finish(failure == null)) : stage;
    }

    private void record(String name, long start, boolean success) {
        if (!enabled) return;
        long end = System.nanoTime();
        spans.add(String.format(
                Locale.ROOT,
                "{\"phase\":\"%s\",\"startNs\":%d,\"durationNs\":%d,\"success\":%s}",
                name,
                start - origin,
                end - start,
                success));
    }

    void finish(boolean success) {
        if (enabled)
            System.out.println("BENCH_PHASE "
                    + String.format(
                            Locale.ROOT,
                            "{\"operation\":\"%s\",\"durationNs\":%d,\"success\":%s,\"events\":[%s]}",
                            operation,
                            System.nanoTime() - origin,
                            success,
                            String.join(",", spans)));
    }
}
