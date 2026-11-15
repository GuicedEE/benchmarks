package bench.persistence.model;
import jakarta.persistence.*;
@Entity
@Table(name = "bench_region")
public class Region extends Row {
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "country_id", nullable = false)
    public Country country;
}
