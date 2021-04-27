# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import logging

class ControlExt(models.Model):
    _inherit = 'account.move'

    icbp  = fields.Float('I.C.B.P.', digits=(12,2), compute="_get_icbp")

    def _get_icbp(self):
        # raise UserError(str(self.tax_line_ids))
        self.icbp = 0.00
        for line in self.line_ids:
            if line.name == 'ICBP':
                self.icbp = line.credit
