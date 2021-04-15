# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from odoo.exceptions import UserError

class StockMove(models.Model):
	_inherit = 'stock.move'

	def set_default_price_unit_from_product(self):
		""" Por defecto coloca el standard_price de producto, si es compra, asignar el precio de la línea de pedido de compra """
		super(StockMove,self).set_default_price_unit_from_product()
		for move in self.filtered('purchase_line_id'): # re-write
			move.write({'price_unit': move.purchase_line_id.price_unit})