# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class FaultsBL(models.Model):

    _name = 'faults.bl'

    employee_id = fields.Many2one('hr.employee','Apellidos y Nombres')
    days = fields.Integer('Días')
    date_start = fields.Date("Fecha de Inicio")
    date_end = fields.Date("Fecha de Fin")
    period = fields.Many2one('hr.payslip.run', string="Periodo")
    slip_base_id = fields.Many2one('hr.payslip')