# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

import odoo.addons.decimal_precision as dp
from odoo import _, api, exceptions, fields, models


class PurchaseRequestLineMakePurchaseOrderIn(models.TransientModel):
	_inherit = "purchase.request.line.make.purchase.order"
	order_type = fields.Many2one('purchase.order.type',required=True,string='Type')
	print("hola")
	@api.model
	def _prepare_purchase_order(self, picking_type, location, company):
		if not self.supplier_id:
			raise exceptions.Warning(
				_('Enter a supplier.'))
		supplier = self.supplier_id
		data = {
			'origin': '',
			'partner_id': self.supplier_id.id,
			'fiscal_position_id': supplier.property_account_position_id and
			supplier.property_account_position_id.id or False,
			'picking_type_id': picking_type.id,
			'company_id': company.id,
			'order_type' : self.order_type.id
			}
		return data