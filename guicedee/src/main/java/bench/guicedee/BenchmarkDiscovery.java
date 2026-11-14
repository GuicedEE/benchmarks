package bench.guicedee;

import com.guicedee.client.services.IGuiceDiscovery;
import bench.guicedee.rest.Resource;
import bench.guicedee.service.Service;
import java.util.Collection;
import java.util.List;

/** Application metadata for the SPI variant; excluded completely from the scanner JAR. */
public final class BenchmarkDiscovery implements IGuiceDiscovery<BenchmarkDiscovery> {
    @Override
    public Collection<Class<?>> classes() {
        return List.of(Resource.class, Service.class);
    }
}
