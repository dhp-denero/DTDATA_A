# -*- coding: utf-8 -*-
from openerp import _, api, fields, models
from odoo.osv import expression

class stock_move(models.Model):
	_inherit='stock.move'

	@api.model
	def create(self,vals):
		t = super(stock_move,self).create(vals)
		t.write({})
		return t

	@api.one
	def write(self,vals):
		t = super(stock_move,self).write(vals)		
		for a in self:
			if a.picking_id and a.picking_id.type_code_stock == 'outgoing':
				order = self.env['sale.order.line'].search([('procurement_group_id','=',a.picking_id.group_id.id)],limit=1).order_id
				a.picking_id.partner_id = order.partner_id.id
				a.picking_id.partner_order_id = order.partner_order_id.id
				a.picking_id.street_ref = order.partner_shipping_id.comment
				a.picking_id.einvoice_12 = self.env['einvoice.catalog.12'].search([('code','=','01')])[0].id
				a.picking_id.fecha_kardex = a.picking_id.min_date
		return t
