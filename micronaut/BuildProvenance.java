import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Build-time input inventory, executed using the builder JDK, never packaged into the application. */
class BuildProvenance {
    static String quote(String value) {
        return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t") + "\"";
    }
    static String sha(Path file) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file)));
    }
    public static void main(String[] args) throws Exception {
        var root = Path.of("/src");
        var sources = new ArrayList<String>();
        try (var paths = Files.walk(root)) {
            for (var file : paths.filter(Files::isRegularFile).sorted().toList()) {
                if (file.toString().contains("/target/")) continue;
                sources.add("{\"path\":" + quote(root.relativize(file).toString()) + ",\"sha256\":" + quote(sha(file))
                        + ",\"content\":" + quote(Files.readString(file)) + "}");
            }
        }
        var dependencies = new ArrayList<String>();
        var sdks = new ArrayList<String>();
        var traceFile = root.resolve("micronaut/src/main/resources/META-INF/native-image/bench/micronaut/trace-inputs.json");
        String trace = Files.exists(traceFile) ? Files.readString(traceFile) : null;
        boolean nativeBuild = Files.isRegularFile(root.resolve("micronaut/target/application"));
        if (nativeBuild && trace == null) throw new IllegalStateException("Native metadata inputs are missing; trace the JVM image first");
        var metadataOwners = List.of("com/commercetools/sdk/", "org/asynchttpclient/", "tools/jackson/",
                "org/javamoney/", "javax/money/", "com/fasterxml/jackson/core/jackson-annotations/", "com/google/");
        for (var name : Files.readString(root.resolve("micronaut/target/classpath.txt")).strip().split(":")) {
            var file = Path.of(name);
            var relative = Path.of("/root/.m2/repository").relativize(file);
            if (relative.toString().startsWith("com/guicedee/")) throw new IllegalStateException("GuicedEE dependency: " + name);
            String hash = sha(file);
            if (nativeBuild && metadataOwners.stream().anyMatch(relative.toString()::startsWith)
                    && (!trace.contains(quote(relative.toString())) || !trace.contains(quote(hash))))
                throw new IllegalStateException("SDK metadata is stale; retrace changed dependency: " + relative);
            String entry = "{\"path\":" + quote(relative.toString()) + ",\"sha256\":" + quote(hash) + "}";
            dependencies.add(entry);
            if (relative.toString().startsWith("com/google/firebase/firebase-admin/")
                    || relative.toString().startsWith("com/commercetools/sdk/commercetools-sdk-java-api/")) sdks.add(entry);
        }
        if (sdks.size() != 2) throw new IllegalStateException("Expected both upstream vendor SDKs");
        Files.writeString(root.resolve("micronaut/target/build-provenance.json"),
                "{\"dependencyMode\":\"standard\",\"sourcesAtImageBuild\":[" + String.join(",", sources)
                + "],\"resolvedDependencies\":[" + String.join(",", dependencies)
                + "],\"sdkJars\":[" + String.join(",", sdks) + "]}\n");
    }
}
