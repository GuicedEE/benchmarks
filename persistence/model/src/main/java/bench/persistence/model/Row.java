package bench.persistence.model;
import jakarta.persistence.*;
@MappedSuperclass
public abstract class Row {
    @Id public Long id;
    @Column(nullable = false, length = 120) private String label;
    @Version public long version;

    public void setLabel(String label) { this.label = label; }
    public String getLabel() { return label; }
}
