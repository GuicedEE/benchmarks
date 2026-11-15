-- Shared schema: Hibernate validates it; DDL is outside application timing.
create table bench_country (
    id bigint primary key,
    label varchar(120) not null,
    version bigint not null
);

create table bench_region (
    id bigint primary key,
    label varchar(120) not null,
    version bigint not null,
    country_id bigint not null references bench_country(id)
);

create table bench_address (
    id bigint primary key,
    label varchar(120) not null,
    version bigint not null,
    region_id bigint not null references bench_region(id)
);

create table bench_customer (
    id bigint primary key,
    label varchar(120) not null,
    version bigint not null,
    address_id bigint not null references bench_address(id)
);

create table bench_supplier (
    id bigint primary key,
    label varchar(120) not null,
    version bigint not null,
    address_id bigint not null references bench_address(id)
);

create table bench_category (
    id bigint primary key,
    label varchar(120) not null,
    version bigint not null,
    supplier_id bigint not null references bench_supplier(id)
);

create table bench_product (
    id bigint primary key,
    label varchar(120) not null,
    version bigint not null,
    category_id bigint not null references bench_category(id),
    supplier_id bigint not null references bench_supplier(id)
);

create table bench_warehouse (
    id bigint primary key,
    label varchar(120) not null,
    version bigint not null,
    address_id bigint not null references bench_address(id)
);

create table bench_inventory (
    id bigint primary key,
    label varchar(120) not null,
    version bigint not null,
    product_id bigint not null references bench_product(id),
    warehouse_id bigint not null references bench_warehouse(id)
);

create table bench_purchase_order (
    id bigint primary key,
    label varchar(120) not null,
    version bigint not null,
    customer_id bigint not null references bench_customer(id)
);

create table bench_order_line (
    id bigint primary key,
    label varchar(120) not null,
    version bigint not null,
    order_id bigint not null references bench_purchase_order(id),
    product_id bigint not null references bench_product(id)
);

create table bench_payment (
    id bigint primary key,
    label varchar(120) not null,
    version bigint not null,
    order_id bigint not null references bench_purchase_order(id)
);

create table bench_shipment (
    id bigint primary key,
    label varchar(120) not null,
    version bigint not null,
    order_id bigint not null references bench_purchase_order(id),
    warehouse_id bigint not null references bench_warehouse(id)
);

create table bench_shipment_item (
    id bigint primary key,
    label varchar(120) not null,
    version bigint not null,
    shipment_id bigint not null references bench_shipment(id),
    line_id bigint not null references bench_order_line(id)
);

create table bench_audit_entry (
    id bigint primary key,
    label varchar(120) not null,
    version bigint not null,
    order_id bigint not null references bench_purchase_order(id)
);
