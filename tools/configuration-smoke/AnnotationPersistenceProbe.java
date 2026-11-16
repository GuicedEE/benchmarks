import com.guicedee.client.Environment;
import com.guicedee.client.utils.Discovery;
class AnnotationPersistenceProbe {
    @SuppressWarnings({"rawtypes", "unchecked"})
    public static void main(String[] args) throws Exception {
        Class<?> app = Class.forName("bench.persistence.guicedee.Main");
        Environment.configureApplication(app);
        String jdbc = Environment.resolvePlaceholders("jdbc:postgresql://${DB_HOST:localhost}:${DB_PORT:5432}/${DB_NAME:bench}");
        if (!jdbc.equals("jdbc:postgresql://localhost:5432/bench")) throw new AssertionError("persistence URL fallback");
        if (!Environment.resolvePlaceholders("${DB_USER:bench}").equals("bench")) throw new AssertionError("persistence user fallback");
        if (!Discovery.mode().equals("spi")) throw new AssertionError("discovery");
        for (String type : new String[]{"com.guicedee.vertx.spi.VertX", "com.guicedee.vertx.web.spi.HttpServerOptions", "com.guicedee.telemetry.TelemetryOptions"})
            if (Discovery.annotations((Class)Class.forName(type)).size()!=1) throw new AssertionError(type);
        System.out.println("ANNOTATION_PROBE_OK");
    }
}
