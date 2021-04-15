# coding=utf-8

from odoo import models, api, fields, exceptions


class StockLocationIt(models.Model):
	_name = 'stock.location.it'

	name = fields.Char(u'Ubicación')
	product_id = fields.Many2one('product.product','Producto')
	## ubicación de odoo al que pertenece:
	location_code =fields.Many2one('stock.location',u'Ubicación general')

	@api.multi
	@api.constrains('product_id','location_code')
	def _check_duplicate_locations(self):
		for obj in self:
			exists = self.env['stock.location.it'].search(['&',('product_id','=',obj.product_id[0].id),('location_code','=',obj.location_code[0].id)])

			if len(exists) != 1:
				name = str(obj.product_id[0].name)
				message = u"Alerta! \n Ya existe una Ubicación definida para el producto  "+ name + u" en esta ubicación general de almacén." 
				raise exceptions.ValidationError(message)