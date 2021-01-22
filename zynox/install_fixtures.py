# -*- coding: utf-8 -*-
# Copyright (c) 2020, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.desk.page.setup_wizard.setup_wizard import make_records


def after_migrate():
    custom_fields = [
        {
            "doctype": "Custom Field",
            "dt": "Company",
            "label": "Default Bonus Account",
            "fieldname": "default_bonus_account_cf",
            "insert_after": "cost_center",
            "fieldtype": "Link",
            "options": "Account",
            "reqd": 1,
        }
    ]
    for d in custom_fields:
        if not frappe.get_meta(d["dt"]).has_field(d["fieldname"]):
            frappe.get_doc(d).insert()

