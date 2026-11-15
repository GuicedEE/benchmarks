package bench.persistence.model;
import jakarta.persistence.*;
@Entity
@Table(name = "bench_order_line")
public class OrderLine extends Row {
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "order_id", nullable = false)
    public PurchaseOrder order;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "product_id", nullable = false)
    public Product product;
}
