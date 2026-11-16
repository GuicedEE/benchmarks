package bench.micronaut;

import bench.workload.Workload;
import io.micronaut.runtime.Micronaut;
import io.micronaut.serde.annotation.SerdeImport;
import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.info.Info;

@SerdeImport(Workload.Order.class)
@OpenAPIDefinition(info = @Info(title = "benchmark", version = "1.0"))
public class Application {
    public static void main(String[] args) {
        Micronaut.run(Application.class, args);
    }
}
