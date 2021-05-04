# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging


class PayslipExt(models.Model):
    _inherit = 'hr.payslip'

    grat_julio = fields.Float(u'Gratificación de Julio', compute="_get_grat_julio")

    def _get_grat_julio(self):
        date = self.date_from
        f = date[0:5]+"07"+date[7:]
        payslip_run_id = self.env['hr.payslip.run'].search([('date_start', '=', f)], limit=1)
        self.grat_julio = 0
        if payslip_run_id:
            for line in payslip_run_id.slip_ids:
                if line.employee_id == self.employee_id:
                    gra = 0
                    bon = 0
                    for rule in line.line_ids:
                        if rule.code == "GRA":
                            gra = rule.total
                        elif rule.code == "BON9":
                            bon = rule.total

                    self.grat_julio = gra + bon
