package bench.guicedee.nativeconfig;

import com.guicedee.nativeimage.GuiceNativeConfiguration;
import com.guicedee.nativeimage.GuiceNativeRegistration;
import java.util.Arrays;
import java.util.Set;

/** Metadata for the unchanged SPI application. No application instances are created during the build. */
public final class BenchmarkNativeConfiguration implements GuiceNativeConfiguration {
    @Override public void configure(GuiceNativeRegistration registration) {
        try {
            var loader = getClass().getClassLoader();
            for (String name : new String[]{"tools.jackson.databind.json.JsonMapper",
                    "io.vertx.core.impl.VertxImpl", "com.codahale.metrics.MetricRegistry"}) {
                registration.inspectMemberInjection(Class.forName(name, false, loader));
            }
            for (String name : new String[]{"bench.guicedee.Main", "bench.guicedee.BenchmarkDiscovery",
                    "bench.guicedee.rest.Resource", "bench.workload.Workload$Order"}) {
                registration.reflect(Class.forName(name, false, loader));
            }
            var annotations = Set.of("org.eclipse.microprofile.metrics.annotation.Counted",
                    "org.eclipse.microprofile.faulttolerance.Retry", "org.eclipse.microprofile.faulttolerance.Timeout");
            registration.intercept(Class.forName("bench.guicedee.service.Service", false, loader),
                    method -> Arrays.stream(method.getDeclaredAnnotations())
                            .anyMatch(annotation -> annotations.contains(annotation.annotationType().getName())));
        } catch (ClassNotFoundException failure) {
            throw new IllegalStateException("The SPI benchmark application must be on the native module path", failure);
        }
    }
}
