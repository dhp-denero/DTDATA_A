# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	def force_desconcile(self):
		for obj in self:
			partial_ids, lines = [], []
			for line in obj.line_ids:
				if line.full_reconcile_id:
					if line.full_reconcile_id.exchange_partial_rec_id:
						partial_ids.append(line.full_reconcile_id.exchange_partial_rec_id.id)
						lines.append(line.id)
			if partial_ids:
				sql = """
					delete from account_partial_reconcile where id in (%s);
					delete from account_move_line where id in (%s); 
				"""%(','.join(str(i) for i in partial_ids),
					 ','.join(str(line) for line in lines)
					)
				self.env.cr.execute(sql)