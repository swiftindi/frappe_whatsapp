// Copyright (c) 2022, Shridhar Patil and contributors
// For license information, please see license.txt

frappe.ui.form.on("WhatsApp Message", {
    refresh: function(frm) {
      frappe.db.get_list('Customer', { fields: ['name'] })
        .then(function(result) {
          var customerNames = result.map(function(item) {
            return item.name;
          });
          cur_frm.set_df_property("a", "options", customerNames);
        });
      frappe.db.get_list('Customer Group', { fields: ['name'] })
        .then(function(result) {
          var groupNames = result.map(function(item) {
            return item.name;
          });
          cur_frm.set_df_property("gruppo", "options", groupNames);
        });
      frappe.db.get_list('WhatsApp Templates', { fields: ['name'] })
        .then(function(result) {
          var templateNames = result.map(function(item) {
            return item.name;
          });
          cur_frm.set_df_property("templates", "options", templateNames);
        });
    },
    switch: function(frm) {
      if (frm.doc.switch) {
        cur_frm.set_df_property("a", "read_only", 1);
        cur_frm.set_df_property("gruppo", "read_only", 0);
        cur_frm.set_df_property("templates", "read_only", 1);
        cur_frm.set_df_property("notifica", "read_only", 1);
      } else {
        cur_frm.set_df_property("a", "read_only", 0);
        cur_frm.set_df_property("gruppo", "read_only", 1);
        cur_frm.set_df_property("templates", "read_only", 0);
        cur_frm.set_df_property("notifica", "read_only", 0);
      }
    },
    notifica: function(frm) {
      if (frm.doc.notifica) {
        cur_frm.set_df_property("a", "read_only", 1);
        cur_frm.set_df_property("gruppo", "read_only", 1);
        cur_frm.set_df_property("switch", "read_only", 1);
        cur_frm.set_df_property("templates", "read_only", 0);
      } else {
        cur_frm.set_df_property("a", "read_only", 0);
        cur_frm.set_df_property("gruppo", "read_only", 0);
        cur_frm.set_df_property("switch", "read_only", 0);
        cur_frm.set_df_property("templates", "read_only", 1);
      }
    }
  });
  