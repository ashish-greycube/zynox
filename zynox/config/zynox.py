from __future__ import unicode_literals
from frappe import _
import frappe


def get_data():
    config = [
        {
            "label": _("Documents"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Item Customer Group Commission",
                    "label": "Item Customer Group Commission",
                    "description": "Item Customer Group Commission",
                },
            ],
        },
        {
            "label": _("Reports"),
            "items": [
                {
                    "type": "report",
                    "name": "SalesMan Commission Analysis",
                    "label": "SalesMan Commission Analysis",
                    "is_query_report": True,
                    "doctype": "Sales Invoice",
                    "description": "SalesMan Commission Analysis",
                    "route": "#query-report/SalesMan Commission Analysis",
                },
                {
                    "type": "report",
                    "name": "Salesmanwise Profit",
                    "label": "Salesmanwise Profit",
                    "is_query_report": True,
                    "doctype": "Sales Invoice",
                    "description": "Salesmanwise Profit",
                    "route": "#query-report/Salesmanwise Profit",
                },
                {
                    "type": "report",
                    "name": "Customer Bonus Report",
                    "label": "Customer Bonus Report",
                    "is_query_report": True,
                    "doctype": "Sales Invoice",
                    "description": "Customer Bonus Report",
                    "route": "#query-report/Customer Bonus Report",
                },
                # {
                #     "type": "report",
                #     "name": "Customerwise Bonus Report",
                #     "label": "Customerwise Bonus Report",
                #     "is_query_report": True,
                #     "doctype": "Sales Invoice",
                #     "description": "Customerwise Bonus Report",
                #     "route": "#query-report/Customerwise Bonus Report",
                # },
            ],
        },
    ]
    return config
