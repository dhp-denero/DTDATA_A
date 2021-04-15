# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime

class PlanillaCtsLine(models.Model):
    _name = 'planilla.liquidacion.cts.line'

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
    fecha_computable = fields.Date("Fecha Computable")
    fecha_cese = fields.Date("Fecha Cese")
    basico = fields.Float(u"Básico", digits=(10, 2))
    a_familiar = fields.Float("A. Familiar", digits=(10, 2))
    gratificacion = fields.Float(u"1/6 Gratificación", digits=(10, 2))
    horas_extras_mean = fields.Float("Prom. Hras extras", digits=(10, 2))
    bonificacion = fields.Float(u"Bonificación", digits=(10, 2))
    comision = fields.Float(u"Comision", digits=(10, 2))
    base = fields.Float(u"Base", digits=(10, 2))
    monto_x_mes = fields.Float("M. por Mes", digits=(10, 2))
    monto_x_dia = fields.Float(u"M. por Día", digits=(10, 2))
    faltas = fields.Integer("Faltas")
    meses = fields.Integer("Meses")
    dias = fields.Integer(u"Días")
    monto_x_meses = fields.Float("Monto. Por los\nMeses", digits=(10, 2))
    monto_x_dias = fields.Float(u"Monto. Por los\nDías", digits=(10, 2))
    total_faltas = fields.Float("Total Faltas", digits=(10, 2))
    cts_soles = fields.Float("CTS \n Soles", digits=(10, 2))
    intereses_cts = fields.Float("Intereses \n CTS", digits=(10, 2))
    otros_dtos = fields.Float("Otros \n Cdtos", digits=(10, 2))
    cts_a_pagar = fields.Float("CTS a\n Pagar", digits=(10, 2))
    tipo_cambio_venta = fields.Float("Tipo de\nCambio\nVenta", digits=(10, 2))
    cts_dolares = fields.Float("CTS \nDolares", digits=(10, 2))
    cta_cts = fields.Char("CTA \nCTS")
    banco = fields.Many2one(
        string=u'Banco',
        comodel_name='res.bank',
        ondelete='set null',
    )
    orden = fields.Integer('Orden')

    @api.onchange('cts_soles', 'otros_dtos', 'intereses_cts')
    def _recalcula_cts(self):
        self.cts_a_pagar = self.cts_soles+self.intereses_cts-self. otros_dtos