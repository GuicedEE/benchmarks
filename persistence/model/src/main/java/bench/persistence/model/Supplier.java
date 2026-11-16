package bench.persistence.model;

import jakarta.persistence.*;

@Entity
@Table(name = "bench_supplier")
public class Supplier extends Row {
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "address_id", nullable = false)
    public Address address;
}
