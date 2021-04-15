# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime


class PlanillaVacacionesLine(models.Model):
    _name = 'planilla.liquidacion.vacaciones.line'

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
    fecha_computable = fields.Date("Fecha Computo")
    fecha_cese = fields.Date("Fecha Cese")
    faltas = fields.Integer("Faltas")
    basico = fields.Float(u"Básico", digits=(10, 2))
    afam = fields.Float(u"A. \n Familiar", digits=(10, 2))
    comision = fields.Float(u"Comision", digits=(10, 2))
    bonificacion = fields.Float(u"Bonificación", digits=(10, 2))
    horas_extras_mean = fields.Float("Prom. Hras extras", digits=(10, 2))
    remuneracion_computable = fields.Float("Rem. Com.", digits=(10, 2))
    meses = fields.Integer("Meses")
    dias = fields.Integer("Dias")
    monto_x_mes = fields.Float("M. por Mes", digits=(10, 2))
    monto_x_dia = fields.Float(u"M. por Día", digits=(10, 2))
    vacaciones_devengadas = fields.Float(
        u"Vacaciones\n Devengadas", digits=(10, 2))
    vacaciones_truncas = fields.Float(u"Vacaciones\n truncas", digits=(10, 2))
    total_vacaciones = fields.Float(u"Total\n vacaciones", digits=(10, 2))
    onp = fields.Float(u"ONP", digits=(10, 2))
    afp_jub = fields.Float(u"AFP JUB", digits=(10, 2))
    afp_si = fields.Float(u"AFP SI", digits=(10, 2))
    afp_com = fields.Float(u"AFP COM", digits=(10, 2))
    neto_total = fields.Float(u"Neto Total", digits=(10, 2))
    orden = fields.Integer('Orden')

    @api.onchange('vacaciones_devengadas', 'vacaciones_truncas', 'contract_id')
    def onchange_vacaciones_devengadas(self):
        self.total_vacaciones = self.vacaciones_devengadas+self.vacaciones_truncas
        if self.contract_id.afiliacion_id.entidad.lower() == 'onp':
            self.onp = self.contract_id.afiliacion_id.fondo/100*self.total_vacaciones
        else:
            self.afp_jub = self.contract_id.afiliacion_id.fondo/100*self.total_vacaciones
            self.afp_si = self.contract_id.afiliacion_id.prima_s/100*self.total_vacaciones
            self.afp_com = self.contract_id.afiliacion_id.com_mix/100*self.total_vacaciones

        if self.contract_id.regimen_laboral_empresa == 'microempresa':
            self.total_vacaciones = 0
        elif self.contract_id.regimen_laboral_empresa == 'pequenhaempresa':
            self.total_vacaciones /= 2.0

        self.neto_total = self.total_vacaciones - \
            (self.onp+self.afp_jub+self.afp_si+self.afp_com)

    @api.multi
    def write(self, vals):
        if 'vacaciones_devengadas' in vals:
            vals['total_vacaciones'] = self.vacaciones_truncas + \
                vals['vacaciones_devengadas']
            onp = 0
            afp_jub = 0
            afp_si = 0
            afp_com = 0
            if self.contract_id.afiliacion_id.entidad.lower() == 'onp':
                onp = self.contract_id.afiliacion_id.fondo / \
                    100*vals['total_vacaciones']
            else:
                afp_jub = self.contract_id.afiliacion_id.fondo / \
                    100*vals['total_vacaciones']
                afp_si = self.contract_id.afiliacion_id.prima_s / \
                    100*vals['total_vacaciones']
                afp_com = self.contract_id.afiliacion_id.com_mix / \
                    100*vals['total_vacaciones']
            if self.contract_id.regimen_laboral_empresa == 'microempresa':
                vals['total_vacaciones'] = 0
            elif self.contract_id.regimen_laboral_empresa == 'pequenhaempresa':
                vals['total_vacaciones'] /= 2.0

            neto_total = vals['total_vacaciones'] - \
                (onp+afp_jub+afp_si+afp_com)
            vals['onp'] = onp
            vals['afp_jub'] = afp_jub
            vals['afp_si'] = afp_si
            vals['afp_com'] = afp_com
            vals['total_vacaciones'] = vals['total_vacaciones']
            vals['neto_total'] = neto_total
        super(PlanillaVacacionesLine, self).write(vals)
