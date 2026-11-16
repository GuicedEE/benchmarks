package bench.persistence.model;

import jakarta.persistence.*;

@Entity
@Table(name = "bench_product")
public class Product extends Row {
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "category_id", nullable = false)
    public Category category;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "supplier_id", nullable = false)
    public Supplier supplier;
}
