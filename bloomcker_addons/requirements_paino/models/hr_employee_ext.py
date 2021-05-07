# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class EmployeeExt(models.Model):
	_inherit = 'hr.employee'

	date_entry_bl = fields.Date('Fecha de Ingreso',compute='_entry_bl')
	date_end_bl = fields.Date('Fecha de Salida',compute='_end_bl')

	bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account Number',
		domain="[('partner_id', '=', address_home_id)]", help='Employee bank inherit')

	bank_account_cts_id = fields.Many2one('res.partner.bank', string='Cuenta CTS',
		domain="[('partner_id', '=', address_home_id)]", help='Cuenta CTS')


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
