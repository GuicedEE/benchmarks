@MetricsOptions(jmxEnabled=false, prometheus=@MetricsOptions.PrometheusOptions(enabled=true, endpoint="/metrics"))
@com.guicedee.vertx.spi.VertX(eventLoopPoolSize=2, workerPoolSize=20)
@com.guicedee.telemetry.TelemetryOptions(enabled=false)
package bench.guicedee;
import com.guicedee.metrics.MetricsOptions;
