# -*- coding: utf-8 -*-

from openerp import models, fields, api,exceptions , _
from suds.client import Client
from openerp.osv import osv
import re

class res_partner(models.Model):
	_inherit = 'res.partner'

	#SE AGREGAN EL DISTRITO,DEPARTAMENTE Y CIUDAD AL NOMBRE
	@api.one
	def verify_ruc(self):
		res = super(res_partner, self).verify_ruc()
		cadena = ''
		if self.street:
			cadena = self.street
		if self.district_id:
			cadena = cadena +'  '+self.district_id.name
		if self.province_id:
			cadena = cadena +' - '+self.province_id.name
		if self.state_id:
			cadena = cadena +' - '+self.state_id.name
		self.street = cadena
		print(cadena)
		return res
