# Copyright (c) 2013, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint
import pandas
from operator import itemgetter


def execute(filters=None):
    return get_columns(filters), get_data(filters)


def get_columns(filters):
    if filters.get("show_summary"):
        return [
            dict(
                label="Salesman",
                fieldname="sales_partner",
                width=160,
            ),
            dict(
                label="Commission",
                fieldname="commission_amount",
                fieldtype="Currency",
                width=110,
            ),
        ]
    else:
        return [
            dict(
                label="Salesman",
                fieldname="sales_partner",
                width=160,
            ),
            dict(
                label="Item Code",
                fieldname="item_code",
                width=160,
            ),
            dict(
                label="Item Name",
                fieldname="item_name",
                width=160,
            ),
            dict(
                label="Qty",
                fieldname="qty",
                fieldtype="Float",
                width=90,
            ),
            dict(
                label="Sales UOM",
                fieldname="sales_uom",
                fieldtype="Data",
                width=90,
            ),
            dict(
                label="Sales Amount",
                fieldname="sales_amount",
                fieldtype="Currency",
                width=110,
            ),
            dict(
                label="Customer Group",
                fieldname="customer_group",
                width=110,
            ),
            dict(
                label="Percentage",
                fieldname="commission_percent",
                fieldtype="Float",
                width=90,
            ),
            dict(
                label="Commission",
                fieldname="commission_amount",
                fieldtype="Currency",
                width=110,
            ),
        ]


def get_conditions(filters):
    where_clause = ["si.docstatus = 1"]
    if filters.get("from_date"):
        where_clause.append("si.posting_date >= %(from_date)s")
    if filters.get("to_date"):
        where_clause.append("si.posting_date <= %(to_date)s")
    if filters.get("salesman"):
        where_clause.append("si.sales_partner = %(salesman)s")

    return " where " + " and ".join(where_clause) if where_clause else ""


def get_data(filters):

    data = frappe.db.sql(
        """
    with fn_comm as
    (
        select icgc.customer_group, icgc.item item_code, sd.from, 
        sd.to, sd.commission_percent, icgc.default_sales_uom
        from `tabItem Customer Group Commission` icgc
        inner join `tabItem Customer Group Commission Slab Detail` sd on sd.parent = icgc.name
    ),
    fn_sales as
    (
        select si.sales_partner, cus.customer_group, sit.item_code, sit.item_name,
        sum(sit.base_net_amount) sales_amount,
        sum(round(sit.qty * sale_ucd.conversion_factor/default_sales_ucd.conversion_factor,2)) qty,
        it.sales_uom
        from `tabSales Invoice` si 
        inner join `tabSales Invoice Item` sit on sit.parent = si.name
        inner join tabItem it on it.item_code = sit.item_code
        inner join `tabUOM Conversion Detail` sale_ucd on sale_ucd.parent = sit.item_code and sale_ucd.uom = sit.uom
        inner join `tabUOM Conversion Detail` default_sales_ucd on default_sales_ucd.parent = sit.item_code and default_sales_ucd.uom = it.sales_uom
        inner join tabCustomer cus on cus.name = si.customer 
        {where_conditions}
        group by si.sales_partner, cus.customer_group, sit.item_code, sit.item_name
    )
    select fn_sales.sales_partner, fn_sales.customer_group, fn_sales.item_code, fn_sales.item_name, fn_sales.sales_uom,
    sum(fn_sales.qty) qty, sum(fn_sales.sales_amount) sales_amount,
    coalesce(fn_comm.commission_percent,0) commission_percent,
    round(sum(coalesce(fn_comm.commission_percent,0) * fn_sales.sales_amount * .01),2) commission_amount
    from fn_sales
    left outer join fn_comm on fn_comm.customer_group = fn_sales.customer_group 
    and fn_comm.item_code = fn_sales.item_code
    and fn_sales.qty BETWEEN fn_comm.from and fn_comm.to
    group by fn_sales.sales_partner, fn_sales.item_code, fn_sales.item_name, 
    fn_sales.sales_uom, fn_comm.commission_percent, fn_sales.customer_group
""".format(
            where_conditions=get_conditions(filters)
        ),
        filters,
        as_dict=True,
        # debug=True,
    )

    if filters.get("show_summary"):
        df = pandas.DataFrame.from_records(data)
        df1 = df[["sales_partner", "commission_amount"]]
        g = df1.groupby("sales_partner", as_index=False).agg("sum")
        data = g.to_dict("r")
        data = sorted(data, key=itemgetter("sales_partner"))

    return data
