import com.guicedee.client.Environment;
import com.guicedee.client.utils.Discovery;
import com.guicedee.guicedinjection.GuiceApplication;
import java.lang.annotation.Annotation;

class AnnotationRuntimeProbe {
    static void expect(String name, String value) {
        String actual = Environment.getSystemPropertyOrEnvironment(name, null);
        if (!value.equals(actual)) throw new AssertionError(name + " expected " + value + " got " + actual);
    }
    @SuppressWarnings({"unchecked", "rawtypes"})
    static Annotation annotation(String name) throws Exception {
        var values = Discovery.annotations((Class) Class.forName(name));
        if (values.size() != 1) throw new AssertionError(name + " count=" + values.size());
        return (Annotation) values.getFirst();
    }
    public static void main(String[] args) throws Exception {
        boolean persistence = args[0].equals("persistence");
        Class<?> app = Class.forName(persistence ? "bench.persistence.guicedee.Main" : "bench.guicedee.Main");
        if (persistence) {
            Environment.configureApplication(app);
            for (String[] setting : new String[][]{{"DB_HOST", "localhost"}, {"DB_PORT", "5432"},
                    {"DB_NAME", "bench"}, {"DB_USER", "bench"}, {"DB_PASSWORD", "bench"}}) expect(setting[0], setting[1]);
            if (!Environment.resolvePlaceholders("jdbc:postgresql://${DB_HOST}:${DB_PORT}/${DB_NAME}")
                    .equals("jdbc:postgresql://localhost:5432/bench")) throw new AssertionError("database placeholders");
        } else {
            GuiceApplication.run(app);
            var metrics = com.guicedee.metrics.implementations.MetricsPreStartup.getOptions();
            if (!metrics.enabled() || metrics.jmxEnabled() || !metrics.prometheus().enabled()) throw new AssertionError("metrics annotation not applied");
            if (com.guicedee.telemetry.implementations.TelemetryPreStartup.getOptions().enabled()) throw new AssertionError("telemetry annotation not applied");
            var ports = com.guicedee.client.IGuiceContext.get(com.guicedee.vertx.web.spi.ManagedHttpListenerGroup.class)
                    .start(java.util.List.of()).toCompletionStage().toCompletableFuture().get();
            if (ports.containsKey("prometheus")) System.out.println("METRICS_PORT=" + ports.get("prometheus"));
            annotation("com.guicedee.metrics.MetricsOptions");
        }
        if (!Discovery.mode().equals(args[1])) throw new AssertionError("discovery mode");
        annotation("com.guicedee.vertx.web.spi.HttpServerOptions");
        annotation("com.guicedee.vertx.spi.VertX");
        annotation("com.guicedee.telemetry.TelemetryOptions");
        System.out.println("ANNOTATION_PROBE_OK");
        if (!persistence) {
            System.in.read();
            com.guicedee.client.IGuiceContext.instance().destroy();
            System.out.println("ANNOTATION_SHUTDOWN_OK");
        }
    }
}
