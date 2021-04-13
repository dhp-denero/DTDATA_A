# -*- coding: utf-8 -*-
import datetime
from openerp.osv import osv
from openerp import models, fields, api

from odoo.exceptions import UserError, ValidationError
from odoo import _


class account_move(models.Model):
	_inherit = 'account.move'

	@api.multi
	def conciliacion_special(self):
		for i in self:
			self.env.cr.execute(""" 
					UPDATE ACCOUNT_MOVE_LINE set amount_residual = 0, reconciled= true where move_id = """ +str(i.id)+ """
				  """)
		return {}