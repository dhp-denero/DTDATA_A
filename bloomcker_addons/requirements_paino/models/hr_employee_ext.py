# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import logging


class EmployeeExt(models.Model):
	_inherit = 'hr.employee'

	date_entry_bl = fields.Date('Fecha de Ingreso')
	date_end_bl = fields.Date('Fecha de Salida')

	bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account Number',
		domain="[('partner_id', '=', address_home_id)]", help='Employee bank inherit')

	bank_account_cts_id = fields.Many2one('res.partner.bank', string='Cuenta CTS',
		domain="[('partner_id', '=', address_home_id)]", help='Cuenta CTS')

	# def get_view_bank(self):
    #     return {
    #         'domain' : filtro,
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'account.move.line.book',
    #         'view_mode': 'tree',
    #         'view_type': 'form',
    #         'views': [(False, 'tree')],
    #     }
