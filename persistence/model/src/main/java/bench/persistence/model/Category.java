package bench.persistence.model;
import jakarta.persistence.*;
@Entity
@Table(name = "bench_category")
public class Category extends Row {
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "supplier_id", nullable = false)
    public Supplier supplier;
}
