# -*- coding: utf-8 -*-
from __future__ import unicode_literals

app_name = "spos"
app_title = "spos"
app_publisher = "New Indictrans Technologies Pvt Ltd"
app_description = "spos"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "saurabh.p@indictranstech.com"
app_version = "0.0.1"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/spos/css/spos.css"
# app_include_js = "/assets/spos/js/spos.js"

# include js, css files in header of web template
# web_include_css = "/assets/spos/css/spos.css"
# web_include_js = "/assets/spos/js/spos.js"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "spos.install.before_install"
# after_install = "spos.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "spos.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"spos.tasks.all"
# 	],
# 	"daily": [
# 		"spos.tasks.daily"
# 	],
# 	"hourly": [
# 		"spos.tasks.hourly"
# 	],
# 	"weekly": [
# 		"spos.tasks.weekly"
# 	]
# 	"monthly": [
# 		"spos.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "spos.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "spos.event.get_events"
# }

