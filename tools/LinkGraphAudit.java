import java.lang.module.*;
import java.util.*;

/** Inspect the installed image without loading application classes or dropping SPI providers. */
public class LinkGraphAudit {
    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException("Usage: LinkGraphAudit <application-module>");
        }
        var finder = ModuleFinder.ofSystem();
        var roots = Set.of(args[0]);
        var required = Configuration.empty().resolve(finder, ModuleFinder.of(), roots);
        var bound = Configuration.empty().resolveAndBind(finder, ModuleFinder.of(), roots);
        var requiredNames = names(required);
        var boundNames = names(bound);
        var modules = new TreeMap<String, Object>();
        for (var ref : finder.findAll()) {
            var descriptor = ref.descriptor();
            var requires = new TreeMap<String, Object>();
            for (var dependency : descriptor.requires()) {
                requires.put(dependency.name(), Map.of("static", dependency.modifiers().contains(ModuleDescriptor.Requires.Modifier.STATIC),
                        "transitive", dependency.modifiers().contains(ModuleDescriptor.Requires.Modifier.TRANSITIVE)));
            }
            long bytes = 0;
            long entries = 0;
            try (var reader = ref.open(); var resources = reader.list()) {
                for (var name : resources.toList()) {
                    var data = reader.read(name);
                    if (data.isPresent()) {
                        var buffer = data.get();
                        bytes += buffer.remaining();
                        entries++;
                        reader.release(buffer);
                    }
                }
            }
            var providers = new TreeMap<String, Object>();
            for (var provider : descriptor.provides()) providers.put(provider.service(), provider.providers());
            modules.put(descriptor.name(), Map.of("requires", requires, "uses", new TreeSet<>(descriptor.uses()),
                    "provides", providers, "resourceBytesUncompressed", bytes, "resourceCount", entries,
                    "requiredFromApplication", requiredNames.contains(descriptor.name()),
                    "reachableWithServiceBinding", boundNames.contains(descriptor.name())));
        }
        System.out.println(json(Map.of("root", args[0], "requiredClosure", requiredNames,
                "serviceBoundClosure", boundNames, "modules", modules)));
    }

    private static Set<String> names(Configuration configuration) {
        var result = new TreeSet<String>();
        for (var module : configuration.modules()) result.add(module.name());
        return result;
    }

    private static String json(Object value) {
        if (value instanceof String text) return "\"" + text.replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
        if (value instanceof Map<?, ?> map) {
            var items = new ArrayList<String>();
            for (var entry : map.entrySet()) items.add(json(entry.getKey()) + ":" + json(entry.getValue()));
            return "{" + String.join(",", items) + "}";
        }
        if (value instanceof Collection<?> list) {
            var items = new ArrayList<String>();
            for (var item : list) items.add(json(item));
            return "[" + String.join(",", items) + "]";
        }
        return String.valueOf(value);
    }
}
