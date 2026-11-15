import java.lang.module.ModuleFinder;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.jar.JarFile;
import tools.jackson.databind.json.JsonMapper;

/** Derives module access, resources and application-specific native metadata from the exact build inputs. */
class NativeModuleAccess {
    @SuppressWarnings("unchecked") // Jackson maps preserve unrecognized upstream metadata keys.
    public static void main(String[] args) throws Exception {
        var options = new TreeSet<String>();
        var resources = new TreeSet<String>();
        var reflection = new TreeSet<String>();
        var excluded = new HashSet<String>();
        if (args.length > 4 && !args[4].equals("-")) {
            for (String line : Files.readAllLines(Path.of(args[4]))) {
                String provider = line.split("#", 2)[0].trim();
                if (!provider.isEmpty()) excluded.add(provider);
            }
        }
        var requested = new HashSet<>(Files.readAllLines(Path.of(args[2])));
        List<Path> jars;
        try (var paths = Files.list(Path.of(args[0]))) {
            jars = paths.filter(path -> path.toString().endsWith(".jar")).toList();
        }
        for (Path path : jars) {
            var descriptor = ModuleFinder.of(path).findAll().iterator().next().descriptor();
            String module = descriptor.name();
            // When providers are excluded, Native Image removes them from the JPMS
            // catalog but skips automatic reflection registration for that service.
            // Preserve construction of the remaining providers without rooting exclusions.
            for (var service : descriptor.provides()) {
                if (Collections.disjoint(service.providers(), excluded)) continue;
                for (String provider : service.providers()) if (!excluded.contains(provider)) {
                    reflection.add("{\"name\":\"" + provider + "\",\"condition\":{\"typeReachable\":\""
                            + service.service() + "\"},\"methods\":[{\"name\":\"<init>\",\"parameterTypes\":[]}]}");
                }
            }
            try (var jar = new JarFile(path.toFile())) {
                var entries = jar.entries();
                while (entries.hasMoreElements()) {
                    var entry = entries.nextElement();
                    if (requested.contains(entry.getName())) {
                        resources.add("{\"module\":\"" + module + "\",\"glob\":\"" + entry.getName() + "\"}");
                    }
                    if (!entry.getName().endsWith(".class")) continue;
                    String bytes;
                    try (var input = jar.getInputStream(entry)) {
                        bytes = new String(input.readAllBytes(), StandardCharsets.ISO_8859_1);
                    }
                    if (!bytes.contains("com/oracle/svm/core/annotate/TargetClass")
                            && !bytes.contains("org/graalvm/nativeimage/hosted/Feature")) continue;
                    String name = entry.getName().replaceFirst("^META-INF/versions/[0-9]+/", "");
                    int separator = name.lastIndexOf('/');
                    if (separator < 0) continue;
                    String pkg = name.substring(0, separator).replace('/', '.');
                    options.add("--add-opens=" + module + "/" + pkg + "=org.graalvm.nativeimage.builder");
                    options.add("--add-reads=" + module + "=org.graalvm.nativeimage");
                }
            }
        }
        Files.write(Path.of(args[1]), options);
        var metadata = Path.of(args[3]);
        Files.createDirectories(metadata);
        var mapper = new JsonMapper();
        var traceEntries = new ArrayList<Object>();
        boolean fullReflection = args.length > 6 && Boolean.parseBoolean(args[6]);
        if (args.length > 5) try (var application = new JarFile(args[5])) {
            for (String trace : List.of("sdk-trace", "guicedee-trace")) {
                var entry = application.getJarEntry("META-INF/native-image/dev.guicedee.benchmarks/" + trace + "/reachability-metadata.json");
                if (entry == null) throw new IllegalStateException("Missing SDK trace: " + trace);
                Map<?, ?> data;
                try (var input = application.getInputStream(entry)) { data = mapper.readValue(input, Map.class); }
                for (Object value : (List<?>) data.get("reflection")) {
                    var item = (Map<?, ?>) value;
                    if (!fullReflection && item.size() == 1 && item.get("type") instanceof String name
                            && name.startsWith("com.commercetools.api.models.")) {
                        // Unified metadata permits member queries on a type entry.
                        // Preserve that behavior when using an analysis-time condition
                        // in legacy metadata; class-name lookup alone loses annotations
                        // on model interfaces and can make overloaded setters ambiguous.
                        reflection.add(mapper.writeValueAsString(Map.of("name", name,
                                "condition", Map.of("typeReachable", name),
                                "queryAllDeclaredMethods", true, "queryAllPublicMethods", true,
                                "queryAllDeclaredConstructors", true, "queryAllPublicConstructors", true,
                                "allDeclaredFields", true, "allDeclaredClasses", true)));
                    } else traceEntries.add(item);
                }
                for (Object resource : (List<?>) data.get("resources")) resources.add(mapper.writeValueAsString(resource));
            }
            int parseOverloads = 0;
            for (String schema : List.of("cloud.firestore.v1", "cloud.monitoring.v3", "storage.v2")) {
                var entry = application.getJarEntry("META-INF/native-image/dev.guicedee.benchmarks/firebase-admin/com.google." + schema + "/reflect-config.json");
                if (entry == null) throw new IllegalStateException("Missing protobuf metadata: " + schema);
                List<Map<String, Object>> entries;
                try (var input = application.getInputStream(entry)) { entries = mapper.readValue(input, List.class); }
                for (var item : entries) {
                    if (!fullReflection && Boolean.TRUE.equals(item.get("allPublicMethods"))) {
                        var type = Class.forName((String) item.get("name"), false, NativeModuleAccess.class.getClassLoader());
                        var methods = new ArrayList<Object>();
                        for (var method : type.getMethods()) {
                            // Protobuf's FieldAccessorTable invokes generated accessors.
                            // Static parse convenience overloads are called directly by
                            // clients; retain query metadata but avoid rooting every codec.
                            if (Modifier.isStatic(method.getModifiers()) && Set.of("parseFrom", "parseDelimitedFrom").contains(method.getName())) {
                                parseOverloads++;
                                continue;
                            }
                            methods.add(Map.of("name", method.getName(), "parameterTypes", Arrays.stream(method.getParameterTypes()).map(Class::getTypeName).toList()));
                        }
                        item.remove("allPublicMethods");
                        item.put("methods", methods);
                    }
                    reflection.add(mapper.writeValueAsString(item));
                }
            }
            System.out.println("Native SDK metadata: full reflection=" + fullReflection + "; unrooted static protobuf parse overloads=" + parseOverloads);
        }
        Files.writeString(metadata.resolve("reachability-metadata.json"),
                "{\"resources\":[" + String.join(",", resources) + "],\"reflection\":" + mapper.writeValueAsString(traceEntries) + "}\n");
        // The SPI can be queried before the service type is initialized. Use an
        // analysis-time condition, not a runtime typeReached guard on constructors.
        Files.writeString(metadata.resolve("reflect-config.json"), "[" + String.join(",", reflection) + "]\n");
    }
}
