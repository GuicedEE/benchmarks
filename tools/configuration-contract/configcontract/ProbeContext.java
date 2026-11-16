package configcontract;
import com.guicedee.client.IGuiceContext;
import com.guicedee.client.services.IGuiceProvider;
import io.github.classgraph.ClassGraph;

/** Discovery-only context; cannot accidentally inject or connect to external services. */
public final class ProbeContext implements IGuiceProvider {
    @Override public IGuiceContext get() {
        return (IGuiceContext) java.lang.reflect.Proxy.newProxyInstance(IGuiceContext.class.getClassLoader(),
                new Class<?>[]{IGuiceContext.class}, (proxy, method, args) -> {
                    if (method.getName().equals("getScanResult")) return new ClassGraph().enableClasspath()
                            .enableClassInfo().enableAnnotationInfo().ignoreClassVisibility().acceptPackages(
                                    "duplicate".equals(System.getProperty("config.contract.declaration"))
                                            ? new String[]{"configcontract.pkg", "configcontract.type"}
                                            : new String[]{"configcontract." + System.getProperty("config.contract.declaration")})
                            .scan();
                    throw new UnsupportedOperationException(method.getName());
                });
    }
}
