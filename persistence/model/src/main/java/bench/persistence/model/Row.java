package bench.persistence.model;
import jakarta.persistence.*;
@MappedSuperclass
public abstract class Row {
    @Id public Long id;
    @Column(nullable = false, length = 120) public String label;
    @Version public long version;
}
