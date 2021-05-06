# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import logging


class EmployeeExt(models.Model):
    _inherit = 'hr.employee'

    date_entry_bl = fields.Date('Fecha de Ingreso')
    date_end_bl = fields.Date('Fecha de Salida')

    def get_view_bank(self):
        return {
            'domain' : filtro,
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line.book',
            'view_mode': 'tree',
            'view_type': 'form',
            'views': [(False, 'tree')],
        }
