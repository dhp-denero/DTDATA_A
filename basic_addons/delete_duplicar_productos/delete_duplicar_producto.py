# -*- coding: utf-8 -*-
from openerp.osv import osv
import base64
from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class stock_picking(models.Model):
	_inherit = 'product.product'
	
	@api.multi
	def copy(self, default=None):
		raise UserError('No esta permitido duplicar productos')

class stock_picking(models.Model):
	_inherit = 'product.template'
	
	@api.multi
	def copy(self, default=None):
		raise UserError('No esta permitido duplicar productos')