package bench.persistence.model;

import jakarta.persistence.*;

@Entity
@Table(name = "bench_warehouse")
public class Warehouse extends Row {
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "address_id", nullable = false)
    public Address address;
}
