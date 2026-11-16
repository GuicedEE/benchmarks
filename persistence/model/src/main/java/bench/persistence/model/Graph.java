package bench.persistence.model;

import java.util.*;
import java.util.stream.*;

/** The identical mapping, graph plan and query used by both persistence adapters. */
public final class Graph {
    private Graph() {}

    public static final List<Class<?>> ENTITIES = List.of(
            Country.class,
            Region.class,
            Address.class,
            Customer.class,
            Supplier.class,
            Category.class,
            Product.class,
            Warehouse.class,
            Inventory.class,
            PurchaseOrder.class,
            OrderLine.class,
            Payment.class,
            Shipment.class,
            ShipmentItem.class,
            AuditEntry.class);
    public static final String QUERY = """
        select co, r, a, c, s, k, p, w, i, o, l, pa, sh, si, au
        from AuditEntry au join au.order o join o.customer c join c.address a
        join a.region r join r.country co
        join OrderLine l on l.order = o join l.product p join p.category k join p.supplier s
        join Inventory i on i.product = p join i.warehouse w
        join Payment pa on pa.order = o
        join Shipment sh on sh.order = o and sh.warehouse = w
        join ShipmentItem si on si.shipment = sh and si.line = l
        where o.id = :id
        """;
    private static final String[] ALIASES = {
        "co", "r", "a", "c", "s", "k", "p", "w", "i", "o", "l", "pa", "sh", "si", "au"
    };
    private static final String[][] LINKS = {
        {},
        {"country"},
        {"region"},
        {"address"},
        {"address"},
        {"supplier"},
        {"category", "supplier"},
        {"address"},
        {"product", "warehouse"},
        {"customer"},
        {"order", "product"},
        {"order"},
        {"order", "warehouse"},
        {"shipment", "line"},
        {"order"}
    };
    public static final String PROJECTED_QUERY = "select "
            + IntStream.range(0, ALIASES.length)
                    .mapToObj(i -> Stream.concat(
                                    Stream.of("id", "label", "version"),
                                    Arrays.stream(LINKS[i]).map(link -> link + ".id"))
                            .map(field -> ALIASES[i] + "." + field)
                            .collect(Collectors.joining(", ")))
                    .collect(Collectors.joining(", "))
            + " " + QUERY.substring(QUERY.indexOf("from "));

    public static List<Row> create(long id) {
        var country = row(new Country(), id);
        var region = row(new Region(), id);
        region.country = country;
        var address = row(new Address(), id);
        address.region = region;
        var customer = row(new Customer(), id);
        customer.address = address;
        var supplier = row(new Supplier(), id);
        supplier.address = address;
        var category = row(new Category(), id);
        category.supplier = supplier;
        var product = row(new Product(), id);
        product.category = category;
        product.supplier = supplier;
        var warehouse = row(new Warehouse(), id);
        warehouse.address = address;
        var inventory = row(new Inventory(), id);
        inventory.product = product;
        inventory.warehouse = warehouse;
        var purchaseOrder = row(new PurchaseOrder(), id);
        purchaseOrder.customer = customer;
        var orderLine = row(new OrderLine(), id);
        orderLine.order = purchaseOrder;
        orderLine.product = product;
        var payment = row(new Payment(), id);
        payment.order = purchaseOrder;
        var shipment = row(new Shipment(), id);
        shipment.order = purchaseOrder;
        shipment.warehouse = warehouse;
        var shipmentItem = row(new ShipmentItem(), id);
        shipmentItem.shipment = shipment;
        shipmentItem.line = orderLine;
        var auditEntry = row(new AuditEntry(), id);
        auditEntry.order = purchaseOrder;
        return List.of(
                country,
                region,
                address,
                customer,
                supplier,
                category,
                product,
                warehouse,
                inventory,
                purchaseOrder,
                orderLine,
                payment,
                shipment,
                shipmentItem,
                auditEntry);
    }

    private static <T extends Row> T row(T value, long id) {
        value.id = id;
        value.setLabel(value.getClass().getSimpleName() + ":" + id);
        return value;
    }

    public static List<Row> rows(List<Object[]> result) {
        if (result.size() != 1) throw new MissingGraph();
        return Arrays.stream(result.getFirst()).map(Row.class::cast).toList();
    }

    private record Projection(long id, Map<String, String> labels, Map<String, Long> versions) {}

    private static Projection projection(List<Object[]> result) {
        if (result.size() != 1) throw new MissingGraph();
        Object[] values = result.getFirst();
        if (values.length != 64) throw new IllegalStateException("Incomplete entity projection");
        var labels = new LinkedHashMap<String, String>();
        var versions = new LinkedHashMap<String, Long>();
        long id = ((Number) values[0]).longValue();
        int position = 0;
        for (int i = 0; i < ENTITIES.size(); i++) {
            if (((Number) values[position++]).longValue() != id) throw new IllegalStateException("Mismatched graph");
            String name = ENTITIES.get(i).getSimpleName();
            labels.put(name, (String) values[position++]);
            versions.put(name, ((Number) values[position++]).longValue());
            for (String link : LINKS[i]) {
                if (((Number) values[position++]).longValue() != id)
                    throw new IllegalStateException("Mismatched relationship: " + name + "." + link);
            }
        }
        return new Projection(id, labels, versions);
    }

    public static Map<String, Object> project(List<Object[]> result) {
        var value = projection(result);
        return Map.of("id", value.id(), "entities", value.labels(), "versions", value.versions());
    }

    public static List<Row> detached(List<Object[]> result) {
        var value = projection(result);
        var rows = create(value.id());
        for (int i = 0; i < rows.size(); i++) {
            String name = ENTITIES.get(i).getSimpleName();
            rows.get(i).setLabel(value.labels().get(name));
            rows.get(i).version = value.versions().get(name);
        }
        return rows;
    }

    public static void update(List<Row> rows) {
        rows.forEach(row -> row.setLabel(row.getLabel() + ":updated"));
    }

    public static List<Row> reverse(List<Row> rows) {
        return rows.reversed();
    }

    public static final class MissingGraph extends RuntimeException {}

    public static final class RollbackProbe extends RuntimeException {}
}
