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
            dict(label="Country", fieldname="country_cf", width=120),
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
            dict(
                label="Item Name",
                fieldname="item_name",
                width=200,
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
                label="Points",
                fieldname="points",
                fieldtype="Float",
                width=90,
            ),
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
    if filters.get("customer"):
        where_clause.append("si.customer = %(customer)s")
    if filters.get("customer_group"):
        where_clause.append("cus.customer_group = %(customer_group)s")
    if filters.get("territory"):
        where_clause.append("cus.territory = %(territory)s")
    if filters.get("country"):
        where_clause.append("cus.country_cf = %(country)s")

    return " where " + " and ".join(where_clause) if where_clause else ""


def get_data(filters):
    data = frappe.db.sql(
        """
            with fn_sales as        
            (
                select si.sales_partner, si.customer, cus.customer_group, cus.territory, cus.country_cf,
                sit.item_code, sit.item_name, it.sales_uom,
                sum(FLOOR(sit.qty * sale_ucd.conversion_factor/default_sales_ucd.conversion_factor)) qty
                from `tabSales Invoice` si 
                inner join `tabSales Invoice Item` sit on sit.parent = si.name
                inner join tabItem it on it.item_code = sit.item_code
                inner join `tabUOM Conversion Detail` sale_ucd on sale_ucd.parent = sit.item_code and sale_ucd.uom = sit.uom
                inner join `tabUOM Conversion Detail` default_sales_ucd on default_sales_ucd.parent = sit.item_code and default_sales_ucd.uom = it.sales_uom
                inner join tabCustomer cus on cus.name = si.customer 
                {where_conditions}
                group by si.sales_partner, si.customer, cus.customer_group, cus.territory, cus.country_cf, sit.parent, sit.item_code, sit.item_name
            )
            select fn_sales.customer, fn_sales.item_code, fn_sales.item_name, fn_sales.sales_uom,
            sum(fn_sales.qty) qty,
            sum(case when cgp.qty_to_point_conversion is null then 0 else round(qty*cgp.qty_to_point_conversion,2) end) points,
            fn_sales.sales_partner, fn_sales.customer_group, fn_sales.territory, fn_sales.country_cf
            from fn_sales
            left outer join `tabCustomer Groupwise Points` cgp on cgp.parent = fn_sales.item_code 
            and cgp.customer_group = fn_sales.customer_group
            group by fn_sales.customer, fn_sales.item_code, fn_sales.item_name, fn_sales.sales_uom,
            fn_sales.sales_partner, fn_sales.customer_group, fn_sales.territory, fn_sales.country_cf
        """.format(
            where_conditions=get_conditions(filters)
        ),
        filters,
        as_dict=True,
        # debug=True,
    )

    if filters.get("group_by") == "Customer" and data:
        df = pandas.DataFrame.from_records(data)
        df1 = pandas.pivot_table(
            df,
            index=[
                "customer",
                "sales_partner",
                "customer_group",
                "territory",
                "country_cf",
            ],
            values=["points"],
            fill_value="",
            aggfunc=sum,
            dropna=True,
        )
        df2 = df1.reset_index()
        data = df2.to_dict("r")
    return data
