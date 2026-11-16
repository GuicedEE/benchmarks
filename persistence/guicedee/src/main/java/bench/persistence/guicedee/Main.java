package bench.persistence.guicedee;

import com.guicedee.client.annotations.GuiceOptions;
import com.guicedee.guicedinjection.GuiceApplication;
import com.guicedee.telemetry.TelemetryOptions;
import com.guicedee.vertx.spi.VertX;
import com.guicedee.vertx.web.spi.HttpServerOptions;
import java.util.concurrent.TimeUnit;

// Mirror the .env defaults while retaining the previous Vert.x runtime defaults.
@GuiceOptions(discoveryMode = GuiceOptions.DiscoveryMode.SPI, logLevel = "INFO")
@HttpServerOptions(host = "0.0.0.0", port = 8080, httpsEnabled = false)
@VertX(
        eventLoopPoolSize = 2,
        workerPoolSize = 20,
        maxEventLoopExecuteTime = 2_000_000_000L,
        maxEventLoopExecuteTimeUnit = TimeUnit.NANOSECONDS,
        maxWorkerExecuteTime = 60_000_000_000L,
        maxWorkerExecuteTimeUnit = TimeUnit.NANOSECONDS,
        warningExceptionTime = 5_000_000_000L,
        warningExceptionTimeUnit = TimeUnit.NANOSECONDS,
        quorumSize = 1,
        preferNativeTransport = false,
        useDaemonThreads = false,
        disableTCCL = false)
@TelemetryOptions(enabled = false)
public class Main {
    public static void main(String[] args) {
        GuiceApplication.run(Main.class);
    }
}
