package bench.persistence.model;

import jakarta.persistence.*;

@Entity
@Table(name = "bench_address")
public class Address extends Row {
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "region_id", nullable = false)
    public Region region;
}
