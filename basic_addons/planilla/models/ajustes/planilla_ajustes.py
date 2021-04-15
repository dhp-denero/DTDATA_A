from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime
from odoo.exceptions import UserError


class PlanillaAjustes(models.Model):

    _name = "planilla.ajustes"

    cod_neto_pagar = fields.Many2one("hr.salary.rule")
    cod_remuneracion_asegurable = fields.Many2one("hr.salary.rule")
    diario_provisiones = fields.Many2one("account.journal",string='Diario para Provisiones')
    cod_dias_laborados = fields.Many2one("planilla.worked.days")
    cod_dias_no_laborados = fields.Many2one("planilla.worked.days")
    cod_dias_subsidiados = fields.Many2many("planilla.worked.days",'settings_worked_days_default_rel','settings_id','wd_id',string="Codigos dias Subsidiados")
    ruc = fields.Char("RUC", default='Asigname valor en ajustes')
    afiliacion_sin_regimen_id = fields.Many2one("planilla.afiliacion")
    planilla_tabular_columnas = fields.Text("Columnas para planilla tabular")
    essalud_rules = fields.Many2many('hr.salary.rule','settings_essalud_default_rel','settings_id','rule_id','Reglas Salariales Essalud')

    @api.model
    def create(self, vals):
        if len(self.env['planilla.ajustes'].search([])) >= 1:
            raise ValidationError(
                "Solo puede haber un registro de ajuste!")
        else:
            return super(PlanillaAjustes, self).create(vals)

    @api.model
    def get_parametros_ajustes(self):

        parametros_ajustes = self.search([], limit=1)
        if not parametros_ajustes.cod_neto_pagar.code \
            or not parametros_ajustes.cod_remuneracion_asegurable.code \
            or not parametros_ajustes.cod_dias_laborados.codigo \
            or not parametros_ajustes.cod_dias_no_laborados.codigo \
            or not parametros_ajustes.cod_dias_subsidiados \
            or not parametros_ajustes.ruc \
            or not parametros_ajustes.afiliacion_sin_regimen_id:
            raise UserError(
                'Debe crear un registro de ajuste en:  Nomina->Parametros->Parametros Boleta de Pago')
        # if not parametros_ajustes.cod_neto_pagar.code:
        #     raise UserError(
        #         'Debe configurar parametros de gratificacion cod_neto_pagar Nomina->configuracion->parametros gratificacion')
        # elif not parametros_ajustes.cod_remuneracion_asegurable.code:
        #     raise UserError(
        #         'Debe configurar parametros de gratificacion cod_remuneracion_asegurable Nomina->configuracion->parametros gratificacion')
        # elif not parametros_ajustes.cod_dias_laborados.codigo:
        #     raise UserError(
        #         'Debe configurar parametros de gratificacion cod_dias_laborados Nomina->configuracion->parametros gratificacion')
        # elif not parametros_ajustes.cod_dias_no_laborados.codigo:
        #     raise UserError(
        #         'Debe configurar parametros de gratificacion cod_dias_no_laborados Nomina->configuracion->parametros gratificacion')
        # elif not parametros_ajustes.cod_dias_subsidiados.codigo:
        #     raise UserError(
        #         'Debe configurar parametros de gratificacion cod_dias_subsidiados Nomina->configuracion->parametros gratificacion')
        # elif not parametros_ajustes.ruc:
        #     raise UserError(
        #         'Debe configurar parametros de gratificacion ruc Nomina->configuracion->parametros gratificacion')
        # elif not parametros_ajustes.afiliacion_sin_regimen_id:
        #     raise UserError(
        #         'Debe configurar parametros de gratificacion afiliacion_sin_regimen_id Nomina->configuracion->parametros gratificacion')
        else:
            return parametros_ajustes
