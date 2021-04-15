# coding=utf-8

from odoo import fields, models, api, exceptions


class ProductProduct(models.Model):
	_inherit = 'product.product'
	locations_ids = fields.One2many('stock.location.it', 'product_id', string='Ubicaciones')

	@api.constrains('locations_ids')
	def _check_duplicate_locations(self):
		loc_tmp = []
		for obj in self:
			ids = self.locations_ids
			for item in ids:
				loc_tmp.append(item[0].location_code[0].id)
			if loc_tmp != list(set(loc_tmp)):
				raise exceptions.ValidationError(u"Solo se puede asignar una ubicación por Ubicación de almacén")