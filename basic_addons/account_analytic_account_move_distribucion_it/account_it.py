# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _


class account_move_line(models.Model):
	_inherit = 'account.move.line'

	@api.multi
	def create_analytic_lines(self):
		""" Create analytic items upon validation of an account.move.line having an analytic account. This
			method first remove any existing analytic item related to the line before creating any new one.
		"""
		self.mapped('analytic_line_ids').unlink()
		for obj_line in self:
			if obj_line.analytic_account_id:				
				vals_line = obj_line._prepare_analytic_line()[0]
				if obj_line.analytic_account_id.distribucion_analitica:
					total = vals_line['amount']
					resto = vals_line['amount']
					cont = 1
					for ele in obj_line.analytic_account_id.detalle_distribucion:
						other = {
							'name':vals_line['name'],
							'date':vals_line['date'],
							'account_id':ele.analytic_line_id.id,
							'tag_ids':vals_line['tag_ids'],
							'unit_amount':vals_line['unit_amount'],
							'product_id':vals_line['product_id'],
							'product_uom_id':vals_line['product_uom_id'],
							'amount': round((vals_line['amount']*ele.porcentaje) / 100.0,2) if cont != len(obj_line.analytic_account_id.detalle_distribucion) else resto,
							'general_account_id':vals_line['general_account_id'],
							'ref':vals_line['ref'],
							'move_id':vals_line['move_id'],
							'user_id':vals_line['user_id']
						}
						cont += 1
						resto += -(round((vals_line['amount']*ele.porcentaje) / 100.0,2))
						self.env['account.analytic.line'].create(other)
				else:
					self.env['account.analytic.line'].create(vals_line)
