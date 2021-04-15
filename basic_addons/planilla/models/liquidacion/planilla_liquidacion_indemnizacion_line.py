# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime


class PlanillaLiquidacionIndemnizacionsLine(models.Model):
    _name = 'planilla.liquidacion.indemnizacion.line'

    planilla_liquidacion_id = fields.Many2one(
        'planilla.liquidacion', "Planilla Liquidacion")
    employee_id = fields.Many2one(
        'hr.employee', "Empleado")
    contract_id = fields.Many2one(
        'hr.contract', "Planilla Contrato")
    identification_number = fields.Char("Nro Documento", size=9)
    last_name_father = fields.Char("Apellido Paterno")
    last_name_mother = fields.Char("Apellido Materno")
    names = fields.Char("Nombres")
    fecha_ingreso = fields.Date("Fecha Ingreso")
    fecha_cese = fields.Date("Fecha Cese")
    monto = fields.Float("Monto", digits=(10, 2))
    orden = fields.Integer('Orden')