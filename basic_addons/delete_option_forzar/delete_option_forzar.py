# -*- coding: utf-8 -*-
from openerp.osv import osv
import base64
from odoo import models, fields, api
from datetime import datetime, timedelta


class stock_picking(models.Model):
	_inherit = 'stock.picking'

	
	@api.model
	def hide_forzar_disponibilidad(self):
		if self.env.ref('stock_picking_mass_action.action_force_availability'):
  			self.env.ref('stock_picking_mass_action.action_force_availability').unlink()