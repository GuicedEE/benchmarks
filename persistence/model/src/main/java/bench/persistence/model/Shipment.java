package bench.persistence.model;
import jakarta.persistence.*;
@Entity
@Table(name = "bench_shipment")
public class Shipment extends Row {
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "order_id", nullable = false)
    public PurchaseOrder order;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "warehouse_id", nullable = false)
    public Warehouse warehouse;
}
