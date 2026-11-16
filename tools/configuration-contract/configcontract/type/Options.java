package configcontract.type;
@com.guicedee.vertx.spi.VertX(useDaemonThreads = true, haGroup = "CONTRACT_HA_GROUP")
@com.guicedee.vertx.spi.FileSystemOptions(fileCachingEnabled = false, fileCacheDir = "CONTRACT_CACHE_PATH")
@com.guicedee.vertx.spi.AddressResolverOptions(hostsRefreshPeriod = 30000, servers = {"CONTRACT_DNS", "1.1.1.1"}, searchDomains = "contract.search-domains")
@com.guicedee.vertx.spi.EventBusOptions(port = 19000)
@com.guicedee.vertx.spi.Verticle(value = "CONTRACT_WORKER", threadingModel = io.vertx.core.ThreadingModel.WORKER,
        maxWorkerExecuteTime = 3, maxWorkerExecuteTimeUnit = java.util.concurrent.TimeUnit.MINUTES,
        capabilities = com.guicedee.vertx.spi.Verticle.Capabilities.Rest)
@com.guicedee.vertx.auth.oauth2.OAuth2Options(clientId = "contract-client")
@com.guicedee.metrics.MetricsOptions(jmxEnabled = false, registryName = "CONTRACT_REGISTRY")
@com.guicedee.telemetry.TelemetryOptions(enabled = false, serviceName = "CONTRACT_SERVICE")
public final class Options {}
