from __future__ import unicode_literals
import frappe
import frappe.defaults
from frappe.utils import cstr, flt,cint, get_datetime, get_time, getdate,nowdate
from frappe.defaults import get_user_permissions
import json


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
	return pos_dict



@frappe.whitelist(allow_guest=True)
def get_customer_list(cust_list):
	result = []
	sales_user_cond = ''
	if cust_list:
		sales_user_cond = "where name in ({0})".format(','.join('"{0}"'.format(customer) for customer in cust_list))
	result = frappe.db.sql("select name as customer_id,customer_name from `tabCustomer` {0}".format(sales_user_cond),as_dict=1)
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
	item_data['item_list'] = frappe.db.sql(""" select it.name as item_code,it.description as item_description,it.item_group,
		ifnull( (select ip.price_list_rate
			from `tabItem Price` as ip
			where ip.price_list = '{0}'
			and ip.item_code = it.item_code
			),0.0 ) as cost
	from `tabItem` it""".format(pos_price_list),as_dict=1)
	return item_data


@frappe.whitelist(allow_guest=True)
def create_so_and_po(order_dict,email):
	frappe.session.user = json.loads(email)
	so_flag = create_sales_order(order_dict)
	po_flag = create_purchase_order(order_dict)
	if so_flag == True and po_flag == True:
		return "success"
	else:
		return "fail"	

@frappe.whitelist(allow_guest=True)
def create_sales_order(order_dict):
	return_flag = False
	order = json.loads(order_dict)
	if not frappe.db.get_value("Sales Order",{"pos_timestamp":order.keys()[0]},"name"):
		so_doc = frappe.new_doc("Sales Order")
		order_dict = order.values()[0]
		order_dict["delivery_date"] =  nowdate()
		order_dict["pos_timestamp"] = order.keys()[0]
		so_doc.update(order_dict)
		so_doc.flags.ignore_permissions = 1
		so_doc.submit()
		return_flag = True
	return return_flag


@frappe.whitelist(allow_guest=True)
def create_purchase_order(order_dict):
	return_flag = False
	order = json.loads(order_dict)
	if not frappe.db.get_value("Purchase Order",{"pos_timestamp":order.keys()[0]},"name"):
		po_doc = frappe.new_doc("Purchase Order")
		order_dict = order.values()[0]
		order_dict = add_req_by_date_in_child_table(order_dict)
		order_dict["pos_timestamp"] = order.keys()[0]
		po_doc.update(order_dict)
		po_doc.flags.ignore_permissions = 1
		po_doc.submit()
		return_flag = True
	return return_flag		

			
@frappe.whitelist(allow_guest=True)
def add_req_by_date_in_child_table(order_dict):
	child_list = order_dict.get("items")
	for child in child_list:
		child["schedule_date"] = nowdate()
		child["uom"] = "Nos"
		child["conversion_factor"] = 1
	order_dict["items"] = child_list
	return order_dict
