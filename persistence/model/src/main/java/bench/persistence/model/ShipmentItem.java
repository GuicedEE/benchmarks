package bench.persistence.model;
import jakarta.persistence.*;
@Entity
@Table(name = "bench_shipment_item")
public class ShipmentItem extends Row {
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "shipment_id", nullable = false)
    public Shipment shipment;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "line_id", nullable = false)
    public OrderLine line;
}
