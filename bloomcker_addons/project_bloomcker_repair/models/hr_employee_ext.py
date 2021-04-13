# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import logging

class EmployeeExt(models.Model):
    _inherit = 'hr.employee'

    sald_vacaciones = fields.Integer('Devengo Vacaciones', readonly=True)