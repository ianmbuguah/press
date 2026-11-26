import datetime
import json
from http.cookies import SimpleCookie
from urllib.parse import unquote

import frappe
from frappe.auth import CookieManager

try:
	from frappe.oauth import get_cookie_dict_from_headers
except ImportError:
	# Removed from frappe.oauth in Frappe 16; same behaviour as the v15 helper.
	def get_cookie_dict_from_headers(r):
		cookie = SimpleCookie()
		if r.headers.get("Cookie"):
			cookie.load(r.headers.get("Cookie"))
		return cookie


@frappe.whitelist(allow_guest=True)
def update_preferences(preferences):
	preferences_dict = json.loads(preferences)

	if not frappe.local.cookie_manager:
		frappe.local.cookie_manager = CookieManager()

	cookie_manager = frappe.local.cookie_manager
	cookie_perms = get_cookie_dict_from_headers(frappe.local.request).get("cookie_perms")

	if cookie_perms:
		cookie_perms = json.loads(unquote(cookie_perms.value))

		# If was disabled before, now enabled or vice-versa
		if cookie_perms.get("analytics") != preferences_dict.get("analytics"):
			log_cookie_consent(preferences_dict)
	else:
		# Enabled for the first time
		if preferences_dict.get("analytics"):
			log_cookie_consent(preferences_dict)

	# Update the cookie
	expires = datetime.datetime.now() + datetime.timedelta(days=180)
	cookie_manager.set_cookie("cookie_perms", preferences, expires=expires)


def log_cookie_consent(preferences):
	frappe.get_doc(
		{
			"doctype": "Cookie Preference Log",
			"ip_address": frappe.local.request_ip,
			"agreed_to_analytics_cookies": preferences.get("analytics"),
			"agreed_to_functionality_cookies": preferences.get("functionality"),
			"agreed_to_performance_cookies": preferences.get("performance"),
		}
	).insert(ignore_permissions=True)
