# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime


class PlanillaGratificacionLine(models.Model):
    _name = 'planilla.liquidacion.gratificacion.line'

    planilla_liquidacion_id = fields.Many2one(
        'planilla.liquidacion', "Planilla Liquidacion")
    employee_id = fields.Many2one(
        'hr.employee', "Empleado")
    contract_id =  fields.Many2one(
        'hr.contract', "Planilla Contrato")
    identification_number = fields.Char("Nro Documento", size=9)
    last_name_father = fields.Char("Apellido Paterno")
    last_name_mother = fields.Char("Apellido Materno")
    names = fields.Char("Nombres")
    fecha_ingreso = fields.Date("Fecha Ingreso")
    fecha_computable = fields.Date("Fecha Computo")
    fecha_cese = fields.Date("Fecha Cese")
    meses = fields.Integer("Meses")
    dias = fields.Integer("Dias")
    faltas = fields.Integer("Faltas")
    basico = fields.Float(u"Básico", digits=(10, 2))
    a_familiar = fields.Float("A. Familiar", digits=(10, 2))
    comision = fields.Float(u"Comision", digits=(10, 2))
    bonificacion = fields.Float(u"Bonificación", digits=(10, 2))
    horas_extras_mean = fields.Float("Prom. Hras extras", digits=(10, 2))
    remuneracion_computable = fields.Float("Rem. Com.", digits=(10, 2))
    monto_x_mes = fields.Float("M. por Mes", digits=(10, 2))
    monto_x_dia = fields.Float(u"M. por Día", digits=(10, 2))
    monto_x_meses = fields.Float("Grat. Por los\nMeses", digits=(10, 2))
    monto_x_dias = fields.Float(u"Grat. Por los\nDías", digits=(10, 2))
    total_faltas = fields.Float(u"Total Faltas", digits=(10, 2))
    total_gratificacion = fields.Float(u"Total\nGratificación", digits=(10, 2))
    plus_9 = fields.Float(u"Bonif. 9%", digits=(10, 2))
    total = fields.Float(u"Total Pagar", digits=(10, 2))
    orden = fields.Integer('Orden')