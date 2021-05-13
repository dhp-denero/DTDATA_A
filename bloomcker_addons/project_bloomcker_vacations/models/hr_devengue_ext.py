# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging


class DevengueExt(models.Model):
    _inherit = 'hr.devengue'

    date_start = fields.Date("Fecha de Inicio")
    date_end = fields.Date("Fecha de Fin")

    @api.model
    def create(self, vals):
        result = super(DevengueExt,self).create(vals)

        slip = self.env['hr.payslip'].search([('id', '=', vals["slip_id"])])
        days_total = 0
        for i in slip.periodos_devengue:
            days_total += i.dias

        for days_line in slip.worked_days_line_ids:
            if days_line.code == "DVAC":
                days_line.number_of_days = days_total
            elif days_line.code == "DLAB":
                days_line.number_of_days = days_line.number_of_days - days_total

        return result
