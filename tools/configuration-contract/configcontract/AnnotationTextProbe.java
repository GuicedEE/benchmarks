package configcontract;

import com.guicedee.metrics.*;
import com.guicedee.metrics.implementations.*;
import com.guicedee.metrics.implementations.mp.MPMetricRegistry;
import com.guicedee.telemetry.annotations.*;
import com.guicedee.telemetry.interceptors.TraceMethodInterceptor;
import java.lang.reflect.*;
import java.util.*;

/** Checks resolved names at the metrics and tracing API boundaries without starting a context. */
final class AnnotationTextProbe {
    @MetricMethod(name = "CONTRACT_METRIC", tags = {"CONTRACT_TAG", "literal=value"})
    @Trace("CONTRACT_TRACE")
    @SpanAttribute("CONTRACT_RESULT")
    public long measured(@SpanAttribute("CONTRACT_ARGUMENT") String value) { return 0; }

    static void verify() throws Exception {
        System.setProperty("CONTRACT_METRIC", "contract.counter");
        System.setProperty("CONTRACT_TAG", "region=test");
        System.setProperty("CONTRACT_TRACE", "contract.span");
        System.setProperty("CONTRACT_ARGUMENT", "argument.name");
        System.setProperty("CONTRACT_RESULT", "result.name");
        System.setProperty("CONTRACT_MATCH", "/resolved-route");
        System.setProperty("CONTRACT_ALIAS", "resolved-alias");
        System.setProperty("runtime-value", "must-not-resolve-runtime-input");

        var method = AnnotationTextProbe.class.getDeclaredMethod("measured", String.class);
        var dropwizard = new com.codahale.metrics.MetricRegistry();
        var registry = new MPMetricRegistry(dropwizard, "application");
        var interceptor = new MetricMethodInterceptor();
        var provider = MetricMethodInterceptor.class.getDeclaredField("registryProvider");
        provider.setAccessible(true);
        provider.set(interceptor, (com.google.inject.Provider<org.eclipse.microprofile.metrics.MetricRegistry>) () -> registry);
        var invocation = (org.aopalliance.intercept.MethodInvocation) Proxy.newProxyInstance(
                AnnotationTextProbe.class.getClassLoader(), new Class<?>[]{org.aopalliance.intercept.MethodInvocation.class},
                (p,m,a) -> switch (m.getName()) {
                    case "getMethod", "getStaticPart" -> method;
                    case "getArguments" -> new Object[]{"runtime-value"};
                    case "proceed" -> 0L;
                    default -> null;
                });
        try { Probe.expect(interceptor.invoke(invocation).equals(1L), "metric call counted"); }
        catch (Throwable failure) { throw new AssertionError("metric interceptor", failure); }
        var counter = dropwizard.getCounters().get("contract.counter.runtime-value;region=test;literal=value");
        Probe.expect(counter != null && counter.getCount() == 1, "resolved metric name and tags");

        var match = (Match) Proxy.newProxyInstance(AnnotationTextProbe.class.getClassLoader(), new Class<?>[]{Match.class},
                (p,m,a) -> switch (m.getName()) {
                    case "value" -> "CONTRACT_MATCH";
                    case "alias" -> "CONTRACT_ALIAS";
                    case "type" -> Match.MatchType.EQUALS;
                    default -> Match.class;
                });
        var toMatch = MetricsVertxConfigurator.class.getDeclaredMethod("toMatch", Match.class);
        toMatch.setAccessible(true);
        var resolvedMatch = (io.vertx.ext.dropwizard.Match) toMatch.invoke(new MetricsVertxConfigurator(), match);
        Probe.expect(resolvedMatch.getValue().equals("/resolved-route") && resolvedMatch.getAlias().equals("resolved-alias"), "resolved monitored route");

        var trace = new TraceMethodInterceptor();
        var name = TraceMethodInterceptor.class.getDeclaredMethod("resolveSpanName", Method.class);
        name.setAccessible(true);
        Probe.expect(name.invoke(trace, method).equals("contract.span"), "resolved span name");
        var attributes = new HashMap<String,Object>();
        var span = (io.opentelemetry.api.trace.Span) Proxy.newProxyInstance(AnnotationTextProbe.class.getClassLoader(),
                new Class<?>[]{io.opentelemetry.api.trace.Span.class}, (p,m,a) -> {
                    if (m.getName().equals("setAttribute")) attributes.put((String) a[0], a[1]);
                    return p;
                });
        var record = TraceMethodInterceptor.class.getDeclaredMethod("recordAttributes", io.opentelemetry.api.trace.Span.class, Method.class, Object[].class);
        record.setAccessible(true);
        record.invoke(trace, span, method, new Object[]{"runtime-value"});
        var returned = TraceMethodInterceptor.class.getDeclaredMethod("recordReturnAttribute", io.opentelemetry.api.trace.Span.class, Method.class, Object.class);
        returned.setAccessible(true);
        returned.invoke(trace, span, method, 7L);
        Probe.expect(attributes.equals(Map.of("argument.name", "runtime-value", "result.name", 7L)), "resolved attribute names and literal runtime values");
    }
}
