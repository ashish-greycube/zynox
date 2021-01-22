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
    if filters.get("group_by") == "Customer":
        return [
            dict(
                label="Customer Name",
                fieldname="customer",
                fieldtype="Link",
                options="Customer",
                width=200,
            ),
            dict(label="Customer Group", fieldname="customer_group", width=200),
            dict(label="Points", fieldname="points", fieldtype="Float", width=90),
            dict(label="Sales Partner", fieldname="sales_partner", width=200),
            dict(label="Territory", fieldname="territory", width=120),
            # dict(label="Country", fieldname="country", width=120),
        ]
    else:
        return [
            dict(
                label="Customer Name",
                fieldname="customer",
                fieldtype="Link",
                options="Customer",
                width=200,
            ),
            dict(
                label="Item Code",
                fieldname="item_code",
                fieldtype="Link",
                options="Item",
                width=200,
            ),
            dict(label="Item Name", fieldname="item_name", width=200,),
            dict(label="Qty", fieldname="qty", fieldtype="Float", width=90,),
            dict(label="Points", fieldname="points", fieldtype="Float", width=90,),
            # dict(label="Sales Partner", fieldname="sales_partner", width=120),
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
    data = []
    if filters.get("group_by") == "Customer":
        data = frappe.db.sql(
            """
            select 
                si.sales_partner, sum(sit.qty) qty, si.customer, si.customer_group, si.territory, 
                sum(coalesce(cgp.qty_to_point_conversion,0)/(sit.qty * ifnull(ucd.conversion_factor,1))) points
            from 
                `tabSales Invoice` si
            inner join 
                `tabSales Invoice Item` sit on sit.parent = si.name
            inner join 
                `tabItem` it on it.item_code = sit.item_code
            left outer join 
                `tabCustomer Groupwise Points` cgp on cgp.parent = sit.item_code
            left outer join 
                `tabUOM Conversion Detail` ucd on sit.uom <> it.sales_uom and sit.uom = ucd.uom         
            {where_conditions}
            group by 
                si.sales_partner, si.customer, si.customer_group, si.territory
            """.format(
                where_conditions=get_conditions(filters)
            ),
            filters,
            as_dict=True,
            # debug=True,
        )
    else:
        data = frappe.db.sql(
            """
            select 
                si.sales_partner, sit.item_code, sit.item_name, sum(sit.qty) qty,
                si.customer, si.customer_group, si.territory, 
                sum(coalesce(cgp.qty_to_point_conversion,0)/(sit.qty * ifnull(ucd.conversion_factor,1))) points
            from 
                `tabSales Invoice` si
            inner join 
                `tabSales Invoice Item` sit on sit.parent = si.name
            inner join 
                `tabItem` it on it.item_code = sit.item_code
            left outer join 
                `tabCustomer Groupwise Points` cgp on cgp.parent = sit.item_code
            left outer join 
                `tabUOM Conversion Detail` ucd on sit.uom <> it.sales_uom and sit.uom = ucd.uom         
            {where_conditions}
            group by 
                si.sales_partner, sit.item_code, sit.item_name, si.customer, si.customer_group, si.territory
            """.format(
                where_conditions=get_conditions(filters)
            ),
            filters,
            as_dict=True,
            # debug=True,
        )

    return data
