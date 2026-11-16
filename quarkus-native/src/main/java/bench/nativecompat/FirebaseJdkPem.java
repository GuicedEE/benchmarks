package bench.nativecompat;

import com.google.firebase.internal.shaded.io.grpc.netty.shaded.io.netty.buffer.ByteBuf;
import com.oracle.svm.core.annotate.Alias;
import com.oracle.svm.core.annotate.Substitute;
import com.oracle.svm.core.annotate.TargetClass;
import java.io.File;
import java.io.InputStream;
import java.security.PrivateKey;

/** Retain Netty's ordinary PEM parser when its optional Bouncy Castle backend is absent. */
@TargetClass(
        className = "com.google.firebase.internal.shaded.io.grpc.netty.shaded.io.netty.handler.ssl.SslContext",
        onlyWith = AbsentOptionalBackends.FirebaseBouncyCastle.class)
final class FirebaseJdkPem {
    @Substitute
    static PrivateKey toPrivateKey(File file, String password, boolean tryBouncyCastle) throws Exception {
        return file == null ? null : getPrivateKeyFromByteBuffer(FirebasePemReader.readPrivateKey(file), password);
    }

    @Substitute
    protected static PrivateKey toPrivateKey(InputStream stream, String password) throws Exception {
        return stream == null ? null : getPrivateKeyFromByteBuffer(FirebasePemReader.readPrivateKey(stream), password);
    }

    @Alias
    private static native PrivateKey getPrivateKeyFromByteBuffer(ByteBuf buffer, String password) throws Exception;
}

@TargetClass(
        className = "com.google.firebase.internal.shaded.io.grpc.netty.shaded.io.netty.handler.ssl.PemReader",
        onlyWith = AbsentOptionalBackends.FirebaseBouncyCastle.class)
final class FirebasePemReader {
    @Alias
    static native ByteBuf readPrivateKey(File file) throws Exception;

    @Alias
    static native ByteBuf readPrivateKey(InputStream stream) throws Exception;
}
