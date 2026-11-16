package bench.persistence.guicedee;

import bench.persistence.model.Graph;
import com.guicedee.client.services.IGuiceDiscovery;
import java.util.*;

public final class Discovery implements IGuiceDiscovery<Discovery> {
    public Collection<Class<?>> classes() {
        var types = new ArrayList<Class<?>>(Graph.ENTITIES);
        types.addAll(List.of(Main.class, Database.class, Resource.class, Store.class));
        return types;
    }
}
