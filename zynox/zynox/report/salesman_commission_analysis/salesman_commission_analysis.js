// Copyright (c) 2016, greycube and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["SalesMan Commission Analysis"] = {
  filters: [
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
      fieldname: "salesman",
      label: __("Salesman"),
      fieldtype: "Link",
      options: "Sales Partner",
    },
    {
      fieldname: "show_summary",
      label: __("Show Summary"),
      fieldtype: "Check",
    },
  ],
};
