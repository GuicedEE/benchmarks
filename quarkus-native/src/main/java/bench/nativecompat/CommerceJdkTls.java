package bench.nativecompat;

import com.oracle.svm.core.annotate.Alias;
import com.oracle.svm.core.annotate.Substitute;
import com.oracle.svm.core.annotate.TargetClass;
import com.commercetools.internal.shaded.io.netty.handler.ssl.*;
import java.security.*;
import java.security.cert.X509Certificate;
import java.util.List;
import java.util.Map;
import javax.net.ssl.*;

/** The same JDK TLS branch selected by Netty when its optional tcnative library is absent. */
@TargetClass(className = "com.commercetools.internal.shaded.io.netty.handler.ssl.SslContext", onlyWith = AbsentOptionalBackends.CommerceOpenSsl.class)
final class CommerceJdkTls {

    @Substitute
    static SslContext newClientContextInternal(SslProvider provider, Provider sslProvider,
            X509Certificate[] trust, TrustManagerFactory tmf, X509Certificate[] certificates,
            PrivateKey key, String password, KeyManagerFactory kmf, Iterable<String> ciphers,
            CipherSuiteFilter filter, ApplicationProtocolConfig apn, String[] protocols,
            long cacheSize, long timeout, boolean startTls, boolean ocsp, SecureRandom random,
            String keyStore, String endpointAlgorithm, List<SNIServerName> serverNames,
            Map.Entry<SslContextOption<?>, Object>[] options, List<OpenSslCredential> credentials) throws SSLException {
        CommerceTlsChecks.check(provider, ocsp, credentials);
        return (SslContext) (Object) new CommerceJdkClient(sslProvider, trust, tmf, certificates,
                key, password, kmf, ciphers, filter, apn, protocols, cacheSize, timeout,
                random, keyStore, endpointAlgorithm, serverNames, new CommerceResumption());
    }

    @Substitute
    static SslContext newServerContextInternal(SslProvider provider, Provider sslProvider,
            X509Certificate[] trust, TrustManagerFactory tmf, X509Certificate[] certificates,
            PrivateKey key, String password, KeyManagerFactory kmf, Iterable<String> ciphers,
            CipherSuiteFilter filter, ApplicationProtocolConfig apn, long cacheSize, long timeout,
            ClientAuth clientAuth, String[] protocols, boolean startTls, boolean ocsp, SecureRandom random,
            String keyStore, Map.Entry<SslContextOption<?>, Object>[] options,
            List<OpenSslCredential> credentials) throws SSLException {
        CommerceTlsChecks.check(provider, ocsp, credentials);
        return (SslContext) (Object) new CommerceJdkServer(sslProvider, trust, tmf, certificates,
                key, password, kmf, ciphers, filter, apn, cacheSize, timeout, clientAuth,
                protocols, startTls, random, keyStore, new CommerceResumption());
    }
}

final class CommerceTlsChecks {
    static void check(SslProvider provider, boolean ocsp, List<OpenSslCredential> credentials) {
        if (provider != null && provider != SslProvider.JDK)
            throw new UnsatisfiedLinkError("Optional Netty tcnative library is not installed");
        if (ocsp) throw new IllegalArgumentException("OCSP is not supported with SslProvider.JDK");
        if (credentials != null && !credentials.isEmpty())
            throw new IllegalArgumentException("OpenSslCredential is not supported with SslProvider.JDK");
    }
}

@TargetClass(className = "com.commercetools.internal.shaded.io.netty.handler.ssl.ResumptionController", onlyWith = AbsentOptionalBackends.CommerceOpenSsl.class)
final class CommerceResumption {
    @Alias CommerceResumption() {}
}

@TargetClass(className = "com.commercetools.internal.shaded.io.netty.handler.ssl.SslHandler$SslEngineType", onlyWith = AbsentOptionalBackends.CommerceOpenSsl.class)
final class CommerceEngineType {
    @Alias static CommerceEngineType JDK;
    @Substitute static CommerceEngineType forEngine(SSLEngine engine) { return JDK; }
}

@TargetClass(className = "com.commercetools.internal.shaded.io.netty.handler.ssl.JdkSslClientContext", onlyWith = AbsentOptionalBackends.CommerceOpenSsl.class)
final class CommerceJdkClient {
    @Alias CommerceJdkClient(Provider provider, X509Certificate[] trust, TrustManagerFactory tmf,
            X509Certificate[] certificates, PrivateKey key, String password, KeyManagerFactory kmf,
            Iterable<String> ciphers, CipherSuiteFilter filter, ApplicationProtocolConfig apn,
            String[] protocols, long cacheSize, long timeout, SecureRandom random, String keyStore,
            String endpointAlgorithm, List<SNIServerName> serverNames, CommerceResumption resumption) throws SSLException {}
}

@TargetClass(className = "com.commercetools.internal.shaded.io.netty.handler.ssl.JdkSslServerContext", onlyWith = AbsentOptionalBackends.CommerceOpenSsl.class)
final class CommerceJdkServer {
    @Alias CommerceJdkServer(Provider provider, X509Certificate[] trust, TrustManagerFactory tmf,
            X509Certificate[] certificates, PrivateKey key, String password, KeyManagerFactory kmf,
            Iterable<String> ciphers, CipherSuiteFilter filter, ApplicationProtocolConfig apn,
            long cacheSize, long timeout, ClientAuth clientAuth, String[] protocols, boolean startTls,
            SecureRandom random, String keyStore, CommerceResumption resumption) throws SSLException {}
}
