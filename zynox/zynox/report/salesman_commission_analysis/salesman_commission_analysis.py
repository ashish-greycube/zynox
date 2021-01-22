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
            dict(label="Salesman", fieldname="sales_partner", width=160,),
            dict(
                label="Commission",
                fieldname="commission_amount",
                fieldtype="Currency",
                width=110,
            ),
        ]
    else:
        return [
            dict(label="Salesman", fieldname="sales_partner", width=160,),
            dict(label="Item Code", fieldname="item_code", width=160,),
            dict(label="Item Name", fieldname="item_name", width=160,),
            dict(label="Qty", fieldname="qty", fieldtype="Float", width=90,),
            dict(
                label="Sales Amount",
                fieldname="sales_amount",
                fieldtype="Currency",
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
    where_clause = []
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
    with fn as
    (
        select c.name customer, icgc.item, sd.from, sd.to, sd.commission_percent, icgc.default_sales_uom
        from `tabItem Customer Group Commission` icgc
        inner join `tabItem Customer Group Commission Slab Detail` sd on sd.parent = icgc.name
        inner join tabCustomer c on c.customer_group = icgc.customer_group
    ),
    fn2 as
    (
        select si.sales_partner, sit.item_code, sit.item_name, 
        sit.qty * ifnull(ucd.conversion_factor,1) qty, 
        sit.base_net_amount sales_amount, fn.commission_percent,
        fn.commission_percent * sit.base_net_amount * ifnull(ucd.conversion_factor,1) *.01 commission_amount
        from `tabSales Invoice` si
        inner join `tabSales Invoice Item` sit on sit.parent = si.name
        left outer join fn on fn.customer = si.customer and sit.qty BETWEEN fn.from and fn.to
        left outer join `tabUOM Conversion Detail` ucd on sit.uom <> fn.default_sales_uom and sit.uom = ucd.uom
        {where_conditions}
    )
    select
        fn2.sales_partner, fn2.item_code, fn2.item_name, sum(fn2.qty) qty,
        sum(fn2.sales_amount) sales_amount, max(fn2.commission_percent) commission_percent,
        sum(fn2.commission_amount) commission_amount
    from 
        fn2
    group by
        fn2.sales_partner, fn2.item_code, fn2.item_name""".format(
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

