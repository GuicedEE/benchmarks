package bench.persistence.guicedee;
import com.guicedee.client.services.IGuiceDiscovery;
import bench.persistence.model.Graph;
import java.util.*;
public final class Discovery implements IGuiceDiscovery<Discovery> {
    public Collection<Class<?>> classes() {
        var types = new ArrayList<Class<?>>(Graph.ENTITIES);
        types.addAll(List.of(Database.class, Resource.class, Store.class));
        return types;
    }
}
