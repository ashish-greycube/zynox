# Copyright (c) 2013, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import erpnext
from frappe.utils import cast_fieldtype, cint
import pandas
from operator import itemgetter


def execute(filters=None):
    if not filters.get("company"):
        filters.company = erpnext.get_default_company()
    return get_columns(filters), get_data(filters)


def get_columns(filters):
    return [
        dict(
            label="Salesman",
            fieldname="sales_partner",
            width=160,
        ),
        dict(
            label="Sales Amount",
            fieldname="sales_amount",
            fieldtype="Currency",
            width=100,
        ),
        dict(
            label="COGS",
            fieldname="cogs",
            fieldtype="Currency",
            width=100,
        ),
        dict(
            label="Expense W/O Bonus",
            fieldname="expense_wo_bonus",
            fieldtype="Currency",
            width=100,
        ),
        dict(
            label="Bonus",
            fieldname="bonus",
            fieldtype="Currency",
            width=100,
        ),
        dict(
            label="Total Expense",
            fieldname="total_expense",
            fieldtype="Currency",
            width=160,
        ),
        dict(
            label="Profit",
            fieldname="profit",
            fieldtype="Currency",
            width=160,
        ),
    ]


def get_conditions(filters):
    where_clause = []
    where_clause.append("si.docstatus = 1")
    if filters.get("from_date"):
        where_clause.append("si.posting_date >= %(from_date)s")
    if filters.get("to_date"):
        where_clause.append("si.posting_date <= %(to_date)s")
    if filters.get("salesman"):
        where_clause.append("si.sales_partner = %(salesman)s")

    return " where " + " and ".join(where_clause) if where_clause else ""


def get_data(filters):
    """
    This report depends on the following erpnext core reports: 'General Ledger' & 'Gross Profit'
    If there are any changes in the above erpnext reports, this report will need to be changed accordingly
    """
    invoices = frappe.db.sql(
        """
        select 
            si.sales_partner, si.name sales_invoice, sum(sit.base_net_amount) sales_amount,
            0 cogs, 0 expenses_wo_bonus, 0 bonus, 0 total_expense, 0 profit
        from 
            `tabSales Invoice` si
        inner join 
            `tabSales Invoice Item` sit on sit.parent = si.name
            {where_conditions}
        group by si.sales_partner, si.name
        """.format(
            where_conditions=get_conditions(filters)
        ),
        filters,
        as_dict=True,
        # debug=True,
    )

    if not invoices:
        return []

    # Uses ERPNext 'Gross Profit' report for buying_amount as COGS
    from erpnext.accounts.report.gross_profit.gross_profit import (
        execute as get_gross_profit,
    )

    filters.group_by = "Invoice"
    columns, gross_profit = get_gross_profit(filters)

    if not gross_profit:
        return []

    invoice_idx, buying_amount_idx = -1, -1
    for idx, col in enumerate(columns):
        if not isinstance(col, str):
            continue
        if _("Sales Invoice") in col:
            invoice_idx = idx
        elif _("Buying Amount") in col:
            buying_amount_idx = idx

    if invoice_idx < 0 or buying_amount_idx < 0:
        frappe.throw(
            _(
                "This report depends on Erpnext 'Gross Profit' report for Buying Amount, which cannot be found. "
            )
        )

    gross_profit_data = [[d[invoice_idx], d[buying_amount_idx]] for d in gross_profit]
    df = pandas.DataFrame(gross_profit_data, columns=["sales_invoice", "buying_amount"])
    g = df.groupby("sales_invoice", as_index=False).agg("sum")

    for d in g.to_dict("r"):
        for inv in [i for i in invoices if i["sales_invoice"] == d["sales_invoice"]]:
            inv.cogs = d.get("buying_amount", 0)

    df = pandas.DataFrame.from_records(invoices)

    df1 = pandas.pivot_table(
        df,
        index=[
            "sales_partner",
        ],
        values=[
            "sales_amount",
            "cogs",
            "expenses_wo_bonus",
            "bonus",
            "total_expense",
            "profit",
        ],
        fill_value=0,
        aggfunc=sum,
        dropna=True,
    )
    df1.reset_index(inplace=True)
    data = df1.to_dict("r")

    expense_bonus = get_expense_and_bonus(filters)

    for d in data:
        for i in expense_bonus:
            if d.get("sales_partner") == i.get("sales_partner"):
                d.update(i)
        d["total_expense"] = (
            d.get("cogs", 0) + d.get("expense_wo_bonus", 0) + d.get("bonus", 0)
        )
        d["profit"] = d.get("sales_amount", 0) - d.get("total_expense", 0)
        if not d.get("expense_wo_bonus"):
            d["expense_wo_bonus"] = 0
    return data


def get_expense_and_bonus(filters):
    # Uses ERPNext General Ledger report
    # Bonus = Sum(Debit-Credit) for account = company.default_bonus_account_cf & Cost Center = invoice.sales_partner.cost_center
    # Expenses W/o Bonus = Sum(Debit-Credit) for accounts (Cost Center = invoice.sales_partner.cost_center & root_type = 'Expense')

    from erpnext.accounts.report.general_ledger.general_ledger import (
        execute as get_general_ledger,
    )

    filters.group_by = "Group by Account"
    _, gl_entries = get_general_ledger(filters)

    expense_accounts = ("",)
    sales_partner_cost_centers = {
        d.cost_center_cf: d.name
        for d in frappe.db.get_all("Sales Partner", fields=["name", "cost_center_cf"])
    }

    gl_entries = list(
        filter(
            lambda x: x.get("account") in expense_accounts
            or x.get("cost_center") in sales_partner_cost_centers.keys(),
            gl_entries,
        )
    )

    default_bonus_account = frappe.db.get_value(
        "Company", filters.company, "default_bonus_account_cf"
    )
    for d in gl_entries:
        d["sales_partner"] = sales_partner_cost_centers.get(d["cost_center"])
        if d.get("account") == default_bonus_account:
            d["bonus"] = d.get("debit") - d.get("credit")
            d["expense_wo_bonus"] = 0
        else:
            d["expense_wo_bonus"] = d.get("debit") - d.get("credit")
            d["bonus"] = 0

    df = pandas.DataFrame.from_records(gl_entries)
    df1 = df[["sales_partner", "bonus", "expense_wo_bonus"]]
    g = df1.groupby("sales_partner", as_index=False).agg("sum")

    return g.to_dict("r")
