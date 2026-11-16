module bench.guicedee.cdi.nativeimage {
    requires bench.guicedee.cdi.spi;
    requires com.guicedee.nativeimage;
    requires static org.graalvm.nativeimage;
    requires commercetools.sdk.java.api;
    requires firebase.admin;
    requires java.logging;

    opens bench.nativecompat to
            org.graalvm.nativeimage.builder;

    provides com.guicedee.nativeimage.GuiceNativeConfiguration with
            bench.guicedee.nativeconfig.BenchmarkNativeConfiguration;
}
