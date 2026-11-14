package bench.nativecompat;

import com.oracle.svm.core.annotate.Substitute;
import com.oracle.svm.core.annotate.TargetClass;
import java.util.function.BooleanSupplier;

/** Preserve the SDK's JVM behavior when optional codecs/logging implementations are absent. */
public final class AbsentOptionalBackends {
    private static boolean absent(String name) {
        try {
            Class.forName(name, false, AbsentOptionalBackends.class.getClassLoader());
            return false;
        } catch (ClassNotFoundException | LinkageError absent) {
            return true;
        }
    }
    public static final class Zstd implements BooleanSupplier {
        public boolean getAsBoolean() { return absent("com.github.luben.zstd.Zstd"); }
    }
    public static final class Brotli implements BooleanSupplier {
        public boolean getAsBoolean() { return absent("com.google.firebase.internal.shaded.com.aayushatharva.brotli4j.Brotli4jLoader"); }
    }
    public static final class Log4j implements BooleanSupplier {
        public boolean getAsBoolean() { return absent("com.google.firebase.internal.shaded.io.grpc.netty.shaded.io.netty.util.internal.logging.Log4J2Logger"); }
    }
    public static final class Log4j1 implements BooleanSupplier {
        public boolean getAsBoolean() { return absent("com.google.firebase.internal.shaded.org.apache.log4j.Logger"); }
    }
    public static final class CommerceOpenSsl implements BooleanSupplier {
        public boolean getAsBoolean() { return absent("com.commercetools.internal.shaded.io.netty.internal.tcnative.SSL"); }
    }
    public static final class FirebaseBouncyCastle implements BooleanSupplier {
        public boolean getAsBoolean() { return absent("com.google.firebase.internal.shaded.org.bouncycastle.openssl.PEMParser"); }
    }
}

@TargetClass(className = "com.commercetools.internal.shaded.io.netty.handler.ssl.OpenSsl", onlyWith = AbsentOptionalBackends.CommerceOpenSsl.class)
final class Target_CommerceOpenSsl {
    @Substitute public static boolean isAvailable() { return false; }
    @Substitute public static void ensureAvailability() {
        throw new UnsatisfiedLinkError("Optional Netty tcnative library is not installed");
    }
}

@TargetClass(className = "com.google.firebase.internal.shaded.org.apache.hc.client5.http.impl.ZstdRuntime", onlyWith = AbsentOptionalBackends.Zstd.class)
final class Target_ZstdRuntime {
    @Substitute public static boolean available() { return false; }
}

@TargetClass(className = "com.google.firebase.internal.shaded.org.apache.hc.client5.http.impl.Brotli4jRuntime", onlyWith = AbsentOptionalBackends.Brotli.class)
final class Target_BrotliRuntime {
    @Substitute public static boolean available() { return false; }
}

@TargetClass(className = "com.google.firebase.internal.shaded.io.grpc.netty.shaded.io.netty.util.internal.logging.Log4J2LoggerFactory", onlyWith = AbsentOptionalBackends.Log4j.class)
final class Target_Log4jFactory {
    @Substitute
    public com.google.firebase.internal.shaded.io.grpc.netty.shaded.io.netty.util.internal.logging.InternalLogger newInstance(String name) {
        // Netty catches this to select an installed logging backend, as on the JVM.
        throw new NoClassDefFoundError("Optional Log4j backend is not installed");
    }
}

@TargetClass(className = "com.google.firebase.internal.shaded.io.grpc.netty.shaded.io.netty.util.internal.logging.Log4JLoggerFactory", onlyWith = AbsentOptionalBackends.Log4j1.class)
final class Target_Log4j1Factory {
    @Substitute
    public com.google.firebase.internal.shaded.io.grpc.netty.shaded.io.netty.util.internal.logging.InternalLogger newInstance(String name) {
        throw new NoClassDefFoundError("Optional Log4j 1.x backend is not installed");
    }
}
