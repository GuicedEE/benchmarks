package configcontract;
import com.guicedee.client.Environment;
import com.guicedee.client.utils.Discovery;
import com.guicedee.vertx.spi.*;
import com.guicedee.vertx.auth.oauth2.*;
import java.util.concurrent.TimeUnit;

public final class Probe {
    static void expect(boolean condition, String description) { if (!condition) throw new AssertionError(description); }
    public static void main(String[] args) throws Exception {
        if (System.getProperty("config.contract.declaration").equals("duplicate")) {
            for (Class<? extends java.lang.annotation.Annotation> type : java.util.List.of(VertX.class, FileSystemOptions.class,
                    OAuth2Options.class, com.guicedee.metrics.MetricsOptions.class, com.guicedee.telemetry.TelemetryOptions.class)) {
                try { Discovery.singleAnnotation(type); throw new AssertionError("Duplicate accepted: " + type); }
                catch (IllegalStateException expected) { expect(expected.getMessage().contains("Only one"), "duplicate diagnostic"); }
            }
            System.out.println("CONFIGURATION_CONTRACT_OK");
            return;
        }
        var configure = VertXPreStartup.class.getDeclaredMethod("configureVertxOptions"); configure.setAccessible(true);
        var options = (io.vertx.core.VertxOptions) configure.invoke(new VertXPreStartup());
        expect(Boolean.TRUE.equals(options.getUseDaemonThread()), "daemon");
        expect(options.getEventLoopPoolSize() == new io.vertx.core.VertxOptions().getEventLoopPoolSize(), "inherit event loops");
        expect(options.getWarningExceptionTimeUnit().toMillis(options.getWarningExceptionTime()) == 5000, "warning pair");
        expect(options.getWorkerPoolSize() == 9, "OS before both dotenv files and annotation");
        System.setProperty("VERTX_WORKER_POOL_SIZE", "11");
        expect(((io.vertx.core.VertxOptions) configure.invoke(new VertXPreStartup())).getWorkerPoolSize() == 11, "JVM before OS");
        expect(!options.getFileSystemOptions().isFileCachingEnabled(), "filesystem declaration");
        expect(options.getFileSystemOptions().getFileCacheDir().equals("contract-cache"), "bare filesystem path");
        expect(options.getHAGroup().equals("os-group"), "bare reference OS before dotenv");
        System.setProperty("CONTRACT_HA_GROUP", "system-group");
        expect(((io.vertx.core.VertxOptions) configure.invoke(new VertXPreStartup())).getHAGroup().equals("system-group"), "bare reference JVM before OS");
        expect(options.getAddressResolverOptions().getServers().equals(java.util.List.of("8.8.8.8", "1.1.1.1")), "bare DNS array entry");
        expect(options.getAddressResolverOptions().getSearchDomains().equals(java.util.List.of("local.test", "example.test")), "normalized bare array key");
        expect(options.getEventBusOptions().getPort() == 19000, "eventbus declaration");
        expect(options.getAddressResolverOptions().getHostsRefreshPeriodUnit() == TimeUnit.MILLISECONDS, "DNS unit");
        expect(options.getAddressResolverOptions().getHostsRefreshPeriod() == 30000, "DNS period");
        var auth = OAuth2AuthenticationProvider.class.getDeclaredMethod("discoverOAuth2Options", io.github.classgraph.ScanResult.class); auth.setAccessible(true);
        expect(((OAuth2Options) auth.invoke(new OAuth2AuthenticationProvider(), new Object[]{null})).clientId().equals("contract-client"), "auth discovery");
        new com.guicedee.metrics.implementations.MetricsPreStartup().onStartup();
        expect(!com.guicedee.metrics.implementations.MetricsPreStartup.getOptions().jmxEnabled(), "metrics discovery");
        expect(com.guicedee.metrics.implementations.MetricsPreStartup.getOptions().registryName().equals("contract-registry"), "bare metrics registry");
        new com.guicedee.telemetry.implementations.TelemetryPreStartup().onStartup();
        expect(!com.guicedee.telemetry.implementations.TelemetryPreStartup.getOptions().enabled(), "telemetry discovery");
        expect(com.guicedee.telemetry.implementations.TelemetryPreStartup.getOptions().serviceName().equals("contract-service"), "bare telemetry service");
        var event = VertxEventRegistry.class.getDeclaredMethod("resolveOption", String.class, String.class, String.class); event.setAccessible(true);
        expect(event.invoke(null, "orders.created", "VERTX_EVENT_WORKER", "false").equals("true"), "per-address dotenv");
        expect(Environment.getSystemPropertyOrEnvironment("contract.independent", "one").equals("one"), "first default");
        expect(Environment.getSystemPropertyOrEnvironment("contract.independent", "two").equals("two"), "independent default");
        var verticle = Discovery.singleAnnotation(Verticle.class).orElseThrow();
        if (!Discovery.isSpiOnly() && System.getProperty("config.contract.declaration").equals("pkg")) {
            var metadata = Discovery.scanResult().getPackageInfo("configcontract.pkg").getDirectAnnotationInfo(Verticle.class.getName());
            var reconstruct = VerticleBuilder.class.getDeclaredMethod("reconstructVerticleAnnotation", io.github.classgraph.AnnotationInfo.class); reconstruct.setAccessible(true);
            verticle = (Verticle) reconstruct.invoke(new VerticleBuilder(), metadata);
        }
        expect(verticle.value().equals("CONTRACT_WORKER"), "package worker name");
        expect(verticle.threadingModel() == io.vertx.core.ThreadingModel.WORKER, "package enum");
        expect(verticle.capabilities()[0].getPackageName().equals("com.guicedee.rest"), "capability prefix");
        var deployment = VerticleBuilder.class.getDeclaredMethod("toDeploymentOptions", Verticle.class); deployment.setAccessible(true);
        var configured = (io.vertx.core.DeploymentOptions) deployment.invoke(new VerticleBuilder(), verticle);
        expect(configured.getWorkerPoolName().equals("contract-worker"), "bare deployment worker pool");
        AnnotationTextProbe.verify();
        expect(configured.getMaxWorkerExecuteTimeUnit() == TimeUnit.MINUTES && configured.getMaxWorkerExecuteTime() == 3, "worker pair");
        System.out.println("CONFIGURATION_CONTRACT_OK");
    }
}
