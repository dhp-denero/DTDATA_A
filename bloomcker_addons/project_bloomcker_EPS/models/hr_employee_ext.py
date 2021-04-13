# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging


class EmployeeExt(models.Model):
    _inherit = 'hr.employee'

    eps_check = fields.Boolean(name="EPS", help="Posee EPS", default=False)
    import_mobility = fields.Boolean(string="Condición de Trabajo", help="Posee Importe por Movilidad?", default=False)
    plan_eps = fields.Char('Plan EPS')
    import_food = fields.Float('Importe Alimentario', default=0)
    work_condition = fields.Float('Condición de Trabajo', default=0)
    work_condition_fuel = fields.Float('Condición de Trabajo Combustible', default=0)
