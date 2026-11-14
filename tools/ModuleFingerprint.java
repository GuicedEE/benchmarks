import java.lang.module.ModuleFinder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;

/** Fingerprint installed jimage modules without resolving/initializing application classes. */
public class ModuleFingerprint {
    public static void main(String[] args) throws Exception {
        for (var reference : ModuleFinder.ofSystem().findAll().stream()
                .sorted(java.util.Comparator.comparing(r -> r.descriptor().name())).toList()) {
            var moduleHash = MessageDigest.getInstance("SHA-256");
            long bytes = 0;
            int count = 0;
            try (var reader = reference.open(); var names = reader.list()) {
                for (String name : names.sorted().toList()) {
                    var entry = reader.open(name);
                    if (entry.isEmpty()) continue;
                    var contentHash = MessageDigest.getInstance("SHA-256");
                    try (var input = entry.get()) {
                        byte[] buffer = new byte[16384];
                        int read;
                        while ((read = input.read(buffer)) != -1) {
                            contentHash.update(buffer, 0, read);
                            bytes += read;
                        }
                    }
                    moduleHash.update(name.getBytes(StandardCharsets.UTF_8));
                    moduleHash.update((byte) 0);
                    byte[] digest = contentHash.digest();
                    moduleHash.update(digest);
                    if (args.length > 0 && reference.descriptor().name().equals(args[0]))
                        System.out.println("RESOURCE\t"+name+"\t"+HexFormat.of().formatHex(digest));
                    count++;
                }
            }
            System.out.println(reference.descriptor().name()+"\t"+count+"\t"+bytes+"\t"+HexFormat.of().formatHex(moduleHash.digest()));
        }
    }
}
