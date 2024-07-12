frappe.ui.form.on('Purchase Receipt', {
    refresh: function(frm) {
        frm.add_custom_button(__('Generate and Print Barcodes'), function() {
            // Fetch barcode settings from the custom doctype
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Barcode Settings',
                    fields: ['name', 'page_width', 'page_height', 'barcode_width', 'barcode_height']
                },
                callback: function(r) {
                    if (r.message) {
                        let options = r.message.map(setting => ({
                            label: `${setting.name} (Page: ${setting.page_width}mm x ${setting.page_height}mm, Barcode: ${setting.barcode_width}mm x ${setting.barcode_height}mm)`,
                            value: setting.name
                        }));

                        // Prompt the user to select barcode settings
                        frappe.prompt([
                            {
                                'fieldname': 'barcode_setting',
                                'fieldtype': 'Select',
                                'label': 'Barcode Setting',
                                'options': options,
                                'reqd': 1
                            }
                        ], function(values) {
                            frappe.call({
                                method: 'barcode_scanner.api.generate_barcodes_for_purchase_receipt',
                                args: {
                                    purchase_receipt: frm.doc.name,
                                    barcode_setting: values.barcode_setting
                                },
                                callback: function(r) {
                                    if (r.message && r.message.pdf_base64) {
                                        var pdfData = 'data:application/pdf;base64,' + r.message.pdf_base64;
                                        var pdfWindow = window.open("");
                                        pdfWindow.document.write("<iframe width='100%' height='100%' src='" + pdfData + "'></iframe>");
                                    } else {
                                        frappe.msgprint('No barcodes generated.');
                                    }
                                }
                            });
                        }, 'Set Barcode Settings', 'Generate');
                    } else {
                        frappe.msgprint('No barcode settings found.');
                    }
                }
            });
        });
    }
});