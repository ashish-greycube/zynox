// Copyright (c) 2016, GreyCube Technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Customer Bonus Report"] = {
  filters: [
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",
      default: frappe.defaults.get_user_default("Company"),
      reqd: 1,
    },
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date",
      default: moment().startOf("month").add(-1, "M"),
      reqd: 1,
    },
    {
      fieldname: "to_date",
      label: __("To Date"),
      fieldtype: "Date",
      default: moment(),
      reqd: 1,
    },
    {
      fieldname: "customer",
      label: __("customer"),
      fieldtype: "Link",
      options: "Customer",
    },
    {
      fieldname: "customer_group",
      label: __("Customer Group"),
      fieldtype: "Link",
      options: "Customer Group",
    },
    {
      fieldname: "territory",
      label: __("Territory"),
      fieldtype: "Link",
      options: "Territory",
    },
    {
      fieldname: "country",
      label: __("Country"),
      fieldtype: "Link",
      options: "Country",
    },

    {
      fieldname: "group_by",
      label: __("Group By"),
      fieldtype: "Select",
      options: "Item\nCustomer",
      default: "Item",
    },
  ],
};
