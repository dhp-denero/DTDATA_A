# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime


class PlanillaActualizarAfps(models.TransientModel):

    _name = "planilla.actualizar.afps"

    fecha_ini = fields.Date("Fecha inicio", required="1")
    fecha_fin = fields.Date("Fecha fin", required="1")

    @api.multi
    def do_rebuild(self):

        afiliacion_lines = self.env['planilla.afiliacion.line'].search(
            [('fecha_ini', '=', self.fecha_ini), ('fecha_fin', '=', self.fecha_fin)])
        for afiliacion_porcentaje in afiliacion_lines:
            entidad = afiliacion_porcentaje.planilla_afiliacion_id.entidad
            afiliacion_salary_rule_ids = self.env['hr.salary.rule'].search(
                [('code', 'ilike', entidad+'_')])

            for salary_rule in afiliacion_salary_rule_ids:
                col = salary_rule.code.split('_')[1].strip().lower()
                salary_rule.amount_fix = getattr(afiliacion_porcentaje, col)
