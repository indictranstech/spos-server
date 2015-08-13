from __future__ import unicode_literals
from frappe import _
import frappe.defaults
from frappe.utils import cstr, flt,cint, get_datetime, get_time, getdate,nowdate,now_datetime
from frappe.defaults import get_user_permissions
import json
from frappe.core.doctype.communication.communication import make
import time


@frappe.whitelist(allow_guest=True)
def get_pos_required_data(sales_user):
	sales_user_permissions = get_user_permissions(sales_user)
	pos_dict = {} 
	pos_dict['customer'] = get_customer_list(sales_user_permissions.get('Customer'))
	pos_dict['item_group'] = get_item_group_list()
	pos_dict['vendor'] = get_supplier_list(sales_user_permissions.get('Supplier'))
	item_data = get_item_list(sales_user)
	pos_dict['price_list'] = item_data.get("price_list")
	pos_dict['item'] = item_data.get("item_list")
	pos_dict['company'] = frappe.db.sql(" select value from `tabSingles` where doctype='Global Defaults' and field='default_company' ",as_list=1)[0][0]	
	return pos_dict



@frappe.whitelist(allow_guest=True)
def get_customer_list(cust_list):
	result = []
	sales_user_cond = ''
	if cust_list:
		sales_user_cond = "where cu.name in ({0})".format(','.join('"{0}"'.format(customer) for customer in cust_list))
	result = frappe.db.sql("select cu.name as customer_id,cu.customer_name, ifnull((select concat_ws('\n',ad.address_line1,ad.address_line2,ad.city,ad.state,ad.pincode,ad.country,ad.email_id,ad.phone) from `tabAddress` as ad where  cu.name = ad.customer and ad.is_shipping_address = 1 limit 1 ),'')as cust_address from `tabCustomer` as cu {0}".format(sales_user_cond),as_dict=1)
	return result

@frappe.whitelist(allow_guest=True)
def get_item_group_list():
	result = frappe.db.sql("select name as item_group from `tabItem Group` ",as_list=1)
	return  [item_group[0] for item_group in result]

@frappe.whitelist(allow_guest=True)
def get_supplier_list(supplier_list):
	result = []
	sales_user_cond = ''
	if supplier_list:
		sales_user_cond = "where name in ({0}) ".format(','.join('"{0}"'.format(supplier) for supplier in supplier_list))
	result = frappe.db.sql("select name as vendor_id,(select group_concat(name) from `tabItem` where default_supplier=vendor_id) as item_list  from `tabSupplier` {0}".format(sales_user_cond),as_dict=1)
	for index,row in enumerate(result):
		result[index]["item_list"] = row.get("item_list").split(',') if row.get("item_list") else []
	return result	

@frappe.whitelist(allow_guest=True)
def get_item_list(sales_user):
	pos_price_list = "Standard Selling" 
	result = frappe.db.sql(" select ifnull(selling_price_list,0.0) from `tabPOS Profile` where user='{0}' ".format(sales_user),as_list=1)
	if result:
		pos_price_list = result[0][0] 
	item_data = {}
	item_data['price_list'] = pos_price_list
	item_data['item_list'] = frappe.db.sql(""" select it.name as item_code,it.description as item_description,it.item_group,it.barcode,
		ifnull( (select ip.price_list_rate
			from `tabItem Price` as ip
			where ip.price_list = '{0}'
			and ip.item_code = it.item_code
			),0.0 ) as cost
	from `tabItem` it""".format(pos_price_list),as_dict=1)
	return item_data


@frappe.whitelist(allow_guest=True)
def create_so_and_po(order_dict,email,sync=None):
	try:
		order = json.loads(order_dict)
		if cint(sync) == 1:
			create_spos_sync_record()
		frappe.session.user = 'Administrator' if email == 'administrator' else email
		letter_head = frappe.db.get_value("Supplier",order.values()[0]['supplier'],'letter_head')
		so_flag = create_sales_order(order_dict,letter_head)
		po_flag = create_purchase_order(order_dict,letter_head)
		if so_flag == True and po_flag == True:
			check_spos_log_already_exists(order.keys()[0])
			return "success"
	except Exception,e:
		if not frappe.db.get_value("SPOS Log",{"pos_timestamp":order.keys()[0]},"name"):
			log_doc = frappe.new_doc("SPOS Log")
			log_doc.pos_timestamp = order.keys()[0]
			log_doc.order_data = cstr(order.values()[0])
			log_doc.trace_back = frappe.get_traceback()
			log_doc.save(ignore_permissions=1)
			return "success"
	return "fail"					

@frappe.whitelist(allow_guest=True)
def create_sales_order(order_dict,letter_head):
	order = json.loads(order_dict)
	if not frappe.db.get_value("Sales Order",{"pos_timestamp":order.keys()[0]},"name"):
		so_doc = frappe.new_doc("Sales Order")
		order_dict = order.values()[0]
		order_dict["delivery_date"] =  nowdate()
		order_dict["pos_timestamp"] = order.keys()[0]
		order_dict["letter_head"] = letter_head 
		so_doc.update(order_dict)
		so_doc.flags.ignore_permissions = 1
		try:
			so_doc.submit()
		except Exception,e:
			raise e
		args = {
			'customer': order_dict["customer"],
			'title': "Sales Order Confirmation",
			'vendor': order_dict["supplier"],
			'so_name':so_doc.name
		}
		send_mail_with_attachment("Sales Order",so_doc.name,order_dict["customer"],"templates/pages/sales_order_template.html",args)
	return True


@frappe.whitelist(allow_guest=True)
def create_purchase_order(order_dict,letter_head):
	order = json.loads(order_dict)
	if not frappe.db.get_value("Purchase Order",{"pos_timestamp":order.keys()[0]},"name"):
		po_doc = frappe.new_doc("Purchase Order")
		order_dict = order.values()[0]
		order_dict = add_req_by_date_in_child_table(order_dict)
		order_dict["pos_timestamp"] = order.keys()[0]
		order_dict["letter_head"] = letter_head
		order_dict.pop("selling_price_list",None)
		po_doc.update(order_dict)
		po_doc.flags.ignore_permissions = 1
		try:
			po_doc.submit()
		except Exception,e:
			raise e
		args = {
			'vendor': order_dict["supplier"],
			'title': "Purchase Order Confirmation",
			'customer': order_dict["customer"],
			'po_name':po_doc.name
		}
		send_mail_with_attachment("Purchase Order",po_doc.name,order_dict["supplier"],"templates/pages/purchase_order_template.html",args)
	return True	

			
@frappe.whitelist(allow_guest=True)
def add_req_by_date_in_child_table(order_dict):
	child_list = order_dict.get("items")
	for child in child_list:
		child["schedule_date"] = nowdate()
		child["uom"] = "Nos"
		child["conversion_factor"] = 1
		child.pop("doctype",None)
	order_dict["items"] = child_list
	return order_dict


@frappe.whitelist(allow_guest=True)
def send_mail_with_attachment(doctype,docname,recipient,template,args):
	receipent_email_id = get_email_id_of_receipent(recipient,doctype)
	if receipent_email_id:
		frappe.sendmail(recipients=receipent_email_id, sender=None, subject=doctype+" Confirmation",
			message=frappe.get_template(template).render(args),attachments=[frappe.attach_print(doctype,docname, file_name=docname)])


@frappe.whitelist(allow_guest=True)
def get_email_id_of_receipent(recipient,doctype):
	if doctype == "Sales Order":
		email_cond = "customer"
	if doctype == "Purchase Order":
		email_cond = "supplier"	
	return frappe.db.sql("select max(email_id) from `tabContact` where %(cond)s='%(recipient)s' "%{"recipient":recipient,"cond":email_cond},as_list=1)[0][0]


@frappe.whitelist(allow_guest=True)
def check_spos_log_already_exists(key):
	spos_log_name = frappe.db.get_value("SPOS Log",{"pos_timestamp":key},"name")
	if spos_log_name:
		frappe.delete_doc("SPOS Log",spos_log_name)

@frappe.whitelist(allow_guest=True)
def create_spos_sync_record():
	sr_doc = frappe.new_doc("SPOS Sync Record")
	sr_doc.sync_name = "SPOS Sync for JStorage Data"
	sr_doc.sync_date = nowdate()
	sr_doc.sync_start_time = now_datetime().strftime("%H:%M:%S")
	sr_doc.save(ignore_permissions=1)

@frappe.whitelist(allow_guest=True)
def check_for_connectivity():
	return "success"	