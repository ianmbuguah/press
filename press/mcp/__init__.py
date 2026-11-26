# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.data import sbool

try:
	import frappe_mcp
except ImportError:
	# frappe-mcp is not installed on Frappe 16 / Python 3.14 (its pydantic pin conflicts
	# with the framework). Other modules import helpers from press.mcp.tools, so keep the
	# package importable with a stand-in whose decorators leave functions unchanged.
	frappe_mcp = None


class _MCPUnavailable:
	def __init__(self, name):
		self.name = name

	def register(self, *args, **kwargs):
		def decorator(fn):
			def unavailable(*a, **kw):
				frappe.throw("MCP is not available: the frappe-mcp package is not installed")

			unavailable.__name__ = fn.__name__
			return frappe.whitelist()(unavailable)

		return decorator

	def tool(self, *args, **kwargs):
		return lambda fn: fn


mcp = frappe_mcp.MCP("press-mcp") if frappe_mcp else _MCPUnavailable("press-mcp")


@mcp.register()
def handler():
	frappe.only_for("System Manager")

	user_type = frappe.get_cached_value("User", frappe.session.user, "user_type")

	# Allow unchecked access to System Users
	if user_type != "System User":
		frappe.throw("Access not allowed for this URL", frappe.AuthenticationError)

	# MCP feature flag should be enabled
	if not sbool(str(frappe.get_value("Press Settings", None, "enable_mcp"))):
		frappe.throw("MCP is not enabled", frappe.AuthenticationError)

	import press.mcp.tools.actions
	import press.mcp.tools.codebase
	import press.mcp.tools.documents
	import press.mcp.tools.routes
	import press.mcp.tools.telemetry

	_ = press.mcp.tools.codebase
	_ = press.mcp.tools.documents
	_ = press.mcp.tools.routes
	_ = press.mcp.tools.telemetry
	_ = press.mcp.tools.actions
