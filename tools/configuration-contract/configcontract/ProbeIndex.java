package configcontract;
import com.guicedee.client.services.IGuiceDiscovery;
import java.util.*;
public final class ProbeIndex implements IGuiceDiscovery<ProbeIndex> {
    public Collection<Class<?>> classes() {
        return "spi".equals(System.getProperty("GUICEDEE_DISCOVERY_MODE")) && !"pkg".equals(System.getProperty("config.contract.declaration"))
                ? List.of(configcontract.type.Options.class) : List.of();
    }
    public Collection<Package> packages() {
        return "spi".equals(System.getProperty("GUICEDEE_DISCOVERY_MODE")) && !"type".equals(System.getProperty("config.contract.declaration"))
                ? List.of(configcontract.pkg.Marker.class.getPackage()) : List.of();
    }
}
