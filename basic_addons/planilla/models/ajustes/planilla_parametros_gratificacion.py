from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime
from odoo.exceptions import UserError

class PlanillaParametrosGratificacion(models.Model):

    _name="planilla.parametros.gratificacion"

    # cod_he25 = fields.Many2one("planilla.worked.days",help="Codigo horas extras 25%")
    # cod_he35 = fields.Many2one("planilla.worked.days",help="Codigo horas extras  35")
    # cod_he100 = fields.Many2one("planilla.worked.days",help="Codigo horas extras 100")
    # cod_bonificacion = fields.Many2one("hr.payslip.input")


    cod_basico = fields.Many2one("hr.salary.rule",help="Codigo para Basico")
    cod_gratificacion = fields.Many2one("planilla.inputs.nomina",help="Codigo para Grafificacion")
    # cod_asignacion_familiar =fields.Many2one("hr.payslip.input",help="Codigo para asignacion familiar")
    cod_asignacion_familiar =fields.Many2one("hr.salary.rule",help="Codigo para asignacion familiar")

    cod_bonificacion_9 = fields.Many2one("hr.salary.rule",help="Codigo para bonificacion 9%")
    cod_dias_faltas = fields.Many2one("planilla.worked.days",help="Codigo para dias faltados")

    cod_comisiones = fields.Many2many("hr.salary.rule",'param_comi_default_rel',help="Codigo para Comisiones")
    cod_bonificaciones = fields.Many2many("hr.salary.rule",'param_boni_default_rel',help="Codigo para Bonificaciones")
    cod_sobretiempos = fields.Many2one("hr.salary.rule",help="Codigo para Horas Sobretiempos")
    cod_wds = fields.Many2many('planilla.worked.days','param_wd_default_rel','param_id','wd_id','Cod Worked Days')

    @api.model
    def create(self,vals):
        if len(self.env['planilla.parametros.gratificacion'].search([])) >= 1:
            raise UserError(
                "Solo puede haber un registro de ajuste!")
        else:
            return super(PlanillaParametrosGratificacion,self).create(vals)