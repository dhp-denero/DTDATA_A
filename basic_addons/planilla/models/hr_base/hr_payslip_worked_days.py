

# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError


class HrPayslipWorkedDays(models.Model):
    _inherit='hr.payslip.worked_days'

    tasa = fields.Float(string='Tasa')
    minutos = fields.Float(string='Minutos')
