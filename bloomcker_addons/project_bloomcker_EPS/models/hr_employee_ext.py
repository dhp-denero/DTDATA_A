# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging


class EmployeeExt(models.Model):
    _inherit = 'hr.employee'

    eps_check = fields.Boolean(name="EPS", help="Posee EPS", compute="_get_eps_check")
    import_mobility = fields.Boolean(string="Condición de Trabajo", help="Posee Importe por Movilidad?", default=False)
    plan_eps = fields.Char('Plan EPS', related="contract_id.plan_eps")
    import_food = fields.Float('Importe Alimentario', default=0)
    work_condition = fields.Float('Condición de Trabajo', default=0)
    work_condition_fuel = fields.Float('Condición de Trabajo Combustible', default=0)

    def _get_eps_check(self):
        for record in self:
            if record.contract_id.seguro_salud_id.seguro == 'EPS':
                record.eps_check = True
            else:
                record.eps_check = False
