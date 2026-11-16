package bench.guicedee;

import com.guicedee.client.annotations.EnvironmentProperty;
import com.guicedee.client.annotations.GuiceOptions;
import com.guicedee.guicedinjection.GuiceApplication;
import com.guicedee.metrics.MetricsOptions;
import com.guicedee.telemetry.TelemetryOptions;
import com.guicedee.vertx.spi.VertX;
import com.guicedee.vertx.web.spi.HttpServerOptions;

// Mirror the .env defaults while retaining the previous Vert.x runtime defaults.
@GuiceOptions(discoveryMode = GuiceOptions.DiscoveryMode.SPI, logLevel = "INFO")
@HttpServerOptions(host = "127.0.0.1", port = 18080, httpsEnabled = false)
@EnvironmentProperty(name = "BENCH_UPSTREAM", value = "http://127.0.0.1:18089")
@VertX(
        eventLoopPoolSize = 2,
        workerPoolSize = 20,
        quorumSize = 1,
        preferNativeTransport = false,
        useDaemonThreads = false,
        disableTCCL = false)
@MetricsOptions(
        enabled = true,
        jmxEnabled = false,
        prometheus = @MetricsOptions.PrometheusOptions(enabled = true, endpoint = "/metrics"))
@TelemetryOptions(enabled = false)
public class Main {
    public static void main(String[] args) {
        GuiceApplication.run(Main.class);
    }
}
