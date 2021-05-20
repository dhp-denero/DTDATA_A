# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class EmployeeExt(models.Model):
	_inherit = 'hr.employee'

	def _default_entry_bl(self):
		contract_ids = self.env['hr.contract'].search([('employee_id','=',self.id)])
		_logger.info(contract_ids)
		if contract_ids:
			contract_ids_sorted_by_date_start = contract_ids.sorted(lambda c: c.date_start)
			return contract_ids_sorted_by_date_start[0].date_start

	def _default_end_bl(self):
		contract_ids = self.env['hr.contract'].search([('employee_id','=',self.id)])
		if contract_ids:
			contract_ids_sorted_by_date_start = contract_ids.sorted(lambda c: c.date_start)
			if contract_ids_sorted_by_date_start[-1].date_end:
				return contract_ids_sorted_by_date_start[-1].date_end

	date_entry_bl = fields.Date('Fecha de Ingreso',default=lambda self: self._default_entry_bl())
	date_end_bl = fields.Date('Fecha de Salida',default=_default_end_bl)

	bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account Number',
		domain="[('partner_id', '=', address_home_id)]", help='Employee bank inherit')

	bank_account_cts_id = fields.Many2one('res.partner.bank', string='Cuenta CTS',
		domain="[('partner_id', '=', address_home_id)]", help='Cuenta CTS')
<<<<<<< Updated upstream


	@api.multi
	@api.depends('contract_ids.date_start')
	def _entry_bl(self):
		for record in self:
			if record.contract_ids:
				contract_ids_sorted_by_date_start = record.contract_ids.sorted(lambda c: c.date_start)
				record.date_entry_bl = contract_ids_sorted_by_date_start[0].date_start

	@api.multi
	@api.depends('contract_ids.date_end')
	def _end_bl(self):
		for record in self:
			if record.contract_ids:
				contract_ids_sorted_by_date_start = record.contract_ids.sorted(lambda c: c.date_start)
				_logger.info(contract_ids_sorted_by_date_start)
				if contract_ids_sorted_by_date_start[-1].date_end:
					record.date_end_bl = contract_ids_sorted_by_date_start[-1].date_end
				_logger.info(contract_ids_sorted_by_date_start[-1])

	def get_view_bank(self):
		return {
			"type": "ir.actions.act_window",
			"res_model": "res.partner.bank",
			"views": [[False, "form"]],
			"target": "new",
		}
=======
>>>>>>> Stashed changes
