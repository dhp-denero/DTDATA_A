# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class EmployeeExt(models.Model):
    _name = 'inter.account.banck'
    _inherit = 'res.partner.bank'
