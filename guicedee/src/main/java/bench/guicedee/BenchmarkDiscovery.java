package bench.guicedee;

import bench.guicedee.rest.Resource;
import bench.guicedee.service.Service;
import com.guicedee.client.services.IGuiceDiscovery;
import java.util.Collection;
import java.util.List;

/** Application metadata for the SPI variant; excluded completely from the scanner JAR. */
public final class BenchmarkDiscovery implements IGuiceDiscovery<BenchmarkDiscovery> {
    @Override
    public Collection<Class<?>> classes() {
        return List.of(Main.class, Resource.class, Service.class);
    }
}
