from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime
from odoo.exceptions import UserError

class PlanillaParametrosCts(models.Model):

    _name="planilla.parametros.cts"
    cod_cts = fields.Many2one("planilla.inputs.nomina",help="Codigo para Grafificacion")


    cod_basico = fields.Many2one("hr.salary.rule",help="Codigo para Basico")
    cod_asignacion_familiar =fields.Many2one("hr.salary.rule",help="Codigo para asignacion familiar")
    cod_dias_faltas = fields.Many2one("planilla.worked.days",help="Codigo para dias faltados")

    cod_comisiones = fields.Many2many("hr.salary.rule",'param_comi_cts_default_rel',help="Codigo para Comisiones")
    cod_bonificaciones = fields.Many2many("hr.salary.rule",'param_boni_cts_default_rel',help="Codigo para Bonificaciones")
    cod_sobretiempos = fields.Many2one("hr.salary.rule",help="Codigo para Horas Sobretiempos")

    @api.model
    def create(self,vals):
        if len(self.env['planilla.parametros.cts'].search([])) >= 1:
            raise UserError(
                "Solo puede haber un registro de ajuste!")
        else:
            return super(PlanillaParametrosCts,self).create(vals)
