package bench.workload;

import com.commercetools.api.client.ProjectApiRoot;
import com.commercetools.api.defaultconfig.ApiRootBuilder;
import com.commercetools.api.models.graph_ql.GraphQLRequest;
import com.google.auth.oauth2.AccessToken;
import com.google.auth.oauth2.GoogleCredentials;
import com.google.cloud.firestore.Firestore;
import com.google.firebase.FirebaseApp;
import com.google.firebase.FirebaseOptions;
import com.google.firebase.cloud.FirestoreClient;
import io.vrap.rmf.base.client.oauth2.ClientCredentials;
import java.net.URI;
import java.net.http.*;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

/** Identical vendor work in both adapters. All external traffic is directed to local fixtures. */
public final class Workload implements AutoCloseable {
    public record Order(String sku, int quantity) {}

    private final String upstream;
    private final HttpClient http;
    private final boolean diagnostics;
    private final AtomicBoolean firstQuote = new AtomicBoolean(true);
    private final AtomicBoolean firstFirestore = new AtomicBoolean(true);
    private ProjectApiRoot api;
    private FirebaseApp firebase;
    private Firestore firestore;

    public Workload(String upstream) {
        this(upstream, false);
    }

    public Workload(String upstream, boolean diagnostics) {
        URI uri = URI.create(upstream);
        if (!Set.of("localhost", "127.0.0.1", "mock", "host.docker.internal").contains(uri.getHost()))
            throw new IllegalArgumentException("Benchmark upstream must be a local fixture");
        this.upstream = upstream;
        this.diagnostics = diagnostics;
        var trace = WorkloadTrace.start("workload-construction", diagnostics);
        http = trace.sync(
                "jdk-http-client-initialization",
                () -> HttpClient.newBuilder()
                        .connectTimeout(Duration.ofSeconds(2))
                        .build());
        trace.finish(true);
    }

    private synchronized ProjectApiRoot api() {
        if (api == null)
            api = ApiRootBuilder.of()
                    .defaultClient(
                            ClientCredentials.of()
                                    .withClientId("fixture")
                                    .withClientSecret("fixture")
                                    .build(),
                            upstream + "/oauth/token",
                            upstream)
                    .build("benchmark");
        return api;
    }

    @SuppressWarnings("unchecked")
    public CompletionStage<Map<String, Object>> quote(Order order) {
        var trace = WorkloadTrace.start("first-quote", diagnostics && firstQuote.compareAndSet(true, false));
        try {
            var client = trace.sync("vendor-client-initialization", this::api);
            return trace.complete(trace.async(
                            "vendor-rest-including-oauth", () -> client.get().execute())
                    .thenCompose(project -> trace.async(
                                    "vendor-graphql",
                                    () -> client.graphql()
                                            .post(GraphQLRequest.builder()
                                                    .query("query Stock { inventoryEntries { results {"
                                                            + " availableQuantity } } }")
                                                    .build())
                                            .execute())
                            .thenApply(response -> {
                                var data =
                                        (Map<String, Object>) response.getBody().getData();
                                var inventory = (Map<String, Object>) data.get("inventoryEntries");
                                var stock = (Map<String, Object>) ((List<?>) inventory.get("results")).getFirst();
                                return Map.<String, Object>of(
                                        "sku",
                                        order.sku(),
                                        "quantity",
                                        order.quantity(),
                                        "total",
                                        order.quantity() * 125,
                                        "available",
                                        stock.get("availableQuantity"),
                                        "project",
                                        project.getBody().getName());
                            })));
        } catch (RuntimeException | Error failure) {
            trace.finish(false);
            throw failure;
        }
    }

    public CompletionStage<String> remote(String path) {
        return http.sendAsync(
                        HttpRequest.newBuilder(URI.create(upstream + path))
                                .timeout(Duration.ofSeconds(5))
                                .GET()
                                .build(),
                        HttpResponse.BodyHandlers.ofString())
                .thenApply(response -> {
                    if (response.statusCode() != 200)
                        throw new IllegalStateException("upstream " + response.statusCode());
                    return response.body();
                });
    }

    private synchronized Firestore firestore() {
        if (firestore == null) {
            // Runner always supplies FIRESTORE_EMULATOR_HOST; no real credentials or cloud project.
            firebase = FirebaseApp.initializeApp(
                    FirebaseOptions.builder()
                            .setProjectId("demo-devsuite")
                            .setCredentials(
                                    GoogleCredentials.create(new AccessToken("owner", new Date(Long.MAX_VALUE))))
                            .build(),
                    "benchmark");
            firestore = FirestoreClient.getFirestore(firebase);
        }
        return firestore;
    }

    public CompletionStage<Map<String, Object>> firebase(String id) {
        var trace = WorkloadTrace.start("first-firestore", diagnostics && firstFirestore.compareAndSet(true, false));
        return trace.complete(CompletableFuture.supplyAsync(() -> {
            try {
                var document = trace.sync("firestore-client-initialization", this::firestore)
                        .collection("quotes")
                        .document(id);
                trace.sync("firestore-write-await", () -> await(document.set(Map.of("sku", "fixture", "total", 250))));
                var value = trace.sync("firestore-read-await", () -> await(document.get()));
                return Map.<String, Object>of("id", id, "sku", value.getString("sku"), "total", value.getLong("total"));
            } catch (Exception e) {
                throw new CompletionException(e);
            }
        }));
    }

    private static <T> T await(java.util.concurrent.Future<T> future) {
        try {
            return future.get(5, TimeUnit.SECONDS);
        } catch (Exception failure) {
            throw new CompletionException(failure);
        }
    }

    public void close() throws Exception {
        if (api != null) api.close();
        if (firestore != null) firestore.close();
        if (firebase != null) firebase.delete();
        http.close();
    }
}
