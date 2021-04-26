# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import logging


class EmployeeExt(models.Model):
    _inherit = 'hr.employee'

    date_entry = fields.Date('Fecha de Ingreso')
    date_end = fields.Date('Fecha de Deceso')
