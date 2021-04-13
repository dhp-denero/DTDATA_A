# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging


class EmployeeExt(models.Model):
    _inherit = 'hr.employee'

    inter_account_bank = fields.Many2many('inter.account.banck', string='Cuenta Interbancaria')