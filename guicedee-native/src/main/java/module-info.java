module bench.guicedee.nativeimage {
    requires bench.guicedee;
    requires com.guicedee.nativeimage;
    requires static org.graalvm.nativeimage;
    requires commercetools.sdk.java.api;
    requires firebase.admin;
    requires java.logging;
    opens bench.nativecompat to org.graalvm.nativeimage.builder;
    provides com.guicedee.nativeimage.GuiceNativeConfiguration with bench.guicedee.nativeconfig.BenchmarkNativeConfiguration;
}
