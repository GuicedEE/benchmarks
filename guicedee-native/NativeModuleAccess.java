import java.lang.module.ModuleFinder;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.jar.JarFile;

/** Opens dependency-owned substitution packages to the hosted image builder, never to application modules. */
class NativeModuleAccess {
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
        Files.writeString(metadata.resolve("reachability-metadata.json"),
                "{\"resources\":[" + String.join(",", resources) + "]}\n");
        // The SPI can be queried before the service type is initialized. Use an
        // analysis-time condition, not a runtime typeReached guard on constructors.
        Files.writeString(metadata.resolve("reflect-config.json"), "[" + String.join(",", reflection) + "]\n");
    }
}
