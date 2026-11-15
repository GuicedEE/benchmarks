package bench.persistence.model;
import jakarta.persistence.*;
@Entity
@Table(name = "bench_purchase_order")
public class PurchaseOrder extends Row {
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "customer_id", nullable = false)
    public Customer customer;
}
