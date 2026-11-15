package bench.persistence.model;
import jakarta.persistence.*;
@Entity
@Table(name = "bench_inventory")
public class Inventory extends Row {
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "product_id", nullable = false)
    public Product product;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "warehouse_id", nullable = false)
    public Warehouse warehouse;
}
