# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class FaultsBL(models.Model):

    _name = 'faults.bl'

    employee_id = fields.Many2one('hr.employee','Apellidos y Nombres')
    days = fields.Integer('Días', compute="_get_days_total")
    date_start = fields.Date("Fecha de Inicio")
    date_end = fields.Date("Fecha de Fin")
    period = fields.Many2one('hr.payslip.run', string="Periodo")
    slip_base_id = fields.Many2one('hr.payslip')

    def _get_days_total(self):
        for line in self:
            if line.date_end and line.date_start:
                date_i = datetime.strptime(line.date_start, "%Y-%m-%d")
                date_o = datetime.strptime(line.date_end, "%Y-%m-%d")
                line.days = abs(date_o - date_i).days + 1
            else:
                line.days = 0
