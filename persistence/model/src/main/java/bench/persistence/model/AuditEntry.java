package bench.persistence.model;
import jakarta.persistence.*;
@Entity
@Table(name = "bench_audit_entry")
public class AuditEntry extends Row {
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "order_id", nullable = false)
    public PurchaseOrder order;
}
