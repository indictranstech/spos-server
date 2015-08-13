import frappe

def validate_duplicate_supplier_account(doc, method):
	supplier_list = []
	for row in doc.get('supplier_account_'):
		if row.supplier not in supplier_list:
			supplier_list.append(row.supplier)
		else:
			frappe.msgprint("Duplicate entry found for supplier %s "%row.supplier, raise_exception=1)
			break
