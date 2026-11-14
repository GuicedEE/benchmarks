package bench.workload;

import com.commercetools.api.client.ProjectApiRoot;
import com.commercetools.api.defaultconfig.ApiRootBuilder;
import com.commercetools.api.models.graph_ql.GraphQLRequest;
import io.vrap.rmf.base.client.oauth2.ClientCredentials;
import com.google.auth.oauth2.AccessToken;
import com.google.auth.oauth2.GoogleCredentials;
import com.google.firebase.FirebaseApp;
import com.google.firebase.FirebaseOptions;
import com.google.firebase.cloud.FirestoreClient;
import com.google.cloud.firestore.Firestore;
import java.net.URI;
import java.net.http.*;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;

/** Identical vendor work in both adapters. All external traffic is directed to local fixtures. */
public final class Workload implements AutoCloseable {
    public record Order(String sku, int quantity) {}
    private final String upstream;
    private final HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2)).build();
    private ProjectApiRoot api;
    private FirebaseApp firebase;
    private Firestore firestore;
    public Workload(String upstream) {
        URI uri = URI.create(upstream);
        if (!Set.of("localhost", "127.0.0.1", "mock", "host.docker.internal").contains(uri.getHost()))
            throw new IllegalArgumentException("Benchmark upstream must be a local fixture");
        this.upstream = upstream;
    }
    private synchronized ProjectApiRoot api() {
        if (api == null) api = ApiRootBuilder.of().defaultClient(
                ClientCredentials.of().withClientId("fixture").withClientSecret("fixture").build(),
                upstream + "/oauth/token", upstream).build("benchmark");
        return api;
    }
    @SuppressWarnings("unchecked")
    public CompletionStage<Map<String, Object>> quote(Order order) {
        return api().get().execute().thenCompose(project -> api().graphql().post(GraphQLRequest.builder()
                .query("query Stock { inventoryEntries { results { availableQuantity } } }").build()).execute()
                .thenApply(response -> {
                    var data = (Map<String, Object>) response.getBody().getData();
                    var inventory = (Map<String, Object>) data.get("inventoryEntries");
                    var stock = (Map<String, Object>) ((List<?>) inventory.get("results")).getFirst();
                    return Map.<String, Object>of("sku", order.sku(), "quantity", order.quantity(),
                            "total", order.quantity() * 125, "available", stock.get("availableQuantity"),
                            "project", project.getBody().getName());
                }));
    }
    public CompletionStage<String> remote(String path) {
        return http.sendAsync(HttpRequest.newBuilder(URI.create(upstream + path)).timeout(Duration.ofSeconds(5)).GET().build(),
                HttpResponse.BodyHandlers.ofString()).thenApply(response -> {
            if (response.statusCode() != 200) throw new IllegalStateException("upstream " + response.statusCode());
            return response.body();
        });
    }
    private synchronized Firestore firestore() {
        if (firestore == null) {
            // Runner always supplies FIRESTORE_EMULATOR_HOST; no real credentials or cloud project.
            firebase = FirebaseApp.initializeApp(FirebaseOptions.builder().setProjectId("demo-devsuite")
                    .setCredentials(GoogleCredentials.create(new AccessToken("owner", new Date(Long.MAX_VALUE))))
                    .build(), "benchmark");
            firestore = FirestoreClient.getFirestore(firebase);
        }
        return firestore;
    }
    public CompletionStage<Map<String, Object>> firebase(String id) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                var document = firestore().collection("quotes").document(id);
                document.set(Map.of("sku", "fixture", "total", 250)).get(5, TimeUnit.SECONDS);
                var value = document.get().get(5, TimeUnit.SECONDS);
                return Map.of("id", id, "sku", value.getString("sku"), "total", value.getLong("total"));
            } catch (Exception e) { throw new CompletionException(e); }
        });
    }
    public void close() throws Exception {
        if (api != null) api.close();
        if (firestore != null) firestore.close();
        if (firebase != null) firebase.delete();
        http.close();
    }
}
