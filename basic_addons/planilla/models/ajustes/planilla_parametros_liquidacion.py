from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime
from odoo.exceptions import UserError


class PlanillaParametrosLiquidacion(models.Model):

    _name="planilla.parametros.liquidacion"

    cod_vacacion_devengada = fields.Many2one("planilla.inputs.nomina",help="Codigo para Vacaciones Devengadas")
    cod_vacacion_trunca = fields.Many2one("planilla.inputs.nomina",help="Codigo para Vavaciones Truncas")
    cod_cts = fields.Many2one("planilla.inputs.nomina",help="Codigo para CTS")
    cod_cts_trunca = fields.Many2one("planilla.inputs.nomina",help="Codigo para CTS Trunca")
    cod_gratificacion= fields.Many2one("planilla.inputs.nomina",help="Codigo para Grafificacion")
    cod_gratificacion_trunca = fields.Many2one("planilla.inputs.nomina",help="Codigo para Grafificacion Trunca")
    cod_bonificacion_9 = fields.Many2one("planilla.inputs.nomina",help="Codigo para Bonificacion 9% Trunca")
    cod_indemnizacion = fields.Many2one("planilla.inputs.nomina",help="Codigo para Indemnizacion")


    @api.model
    def create(self,vals):
        if len(self.env['planilla.parametros.liquidacion'].search([])) >= 1:
            raise ValidationError(
                "Solo puede haber un registro de ajuste de liquidacion!")
        else:
            return super(PlanillaParametrosLiquidacion,self).create(vals)

    @api.model
    def get_parametros_liquidacion(self):

        parametros_liquidacion = self.search([], limit=1)
        if not parametros_liquidacion.cod_vacacion_devengada.codigo:
            raise UserError(
                'Debe configurar parametros de gratificacion cod_vacacion_devengada Nomina->configuracion->parametros liquidacion')
        elif not parametros_liquidacion.cod_vacacion_trunca.codigo:
            raise UserError(
                'Debe configurar parametros de gratificacion cod_vacacion_trunca Nomina->configuracion->parametros liquidacion')
        elif not parametros_liquidacion.cod_cts_trunca.codigo:
            raise UserError(
                'Debe configurar parametros de gratificacion cod_cts_trunca Nomina->configuracion->parametros liquidacion')
        elif not parametros_liquidacion.cod_cts.codigo:
            raise UserError(
                'Debe configurar parametros de gratificacion cod_cts Nomina->configuracion->parametros liquidacion')
        elif not parametros_liquidacion.cod_gratificacion_trunca.codigo:
            raise UserError(
                'Debe configurar parametros de gratificacion cod_gratificacion_trunca Nomina->configuracion->parametros liquidacion')
        elif not parametros_liquidacion.cod_gratificacion.codigo:
            raise UserError(
                'Debe configurar parametros de gratificacion cod_gratificacion Nomina->configuracion->parametros liquidacion')
        elif not parametros_liquidacion.cod_bonificacion_9.codigo:
            raise UserError(
                'Debe configurar parametros de gratificacion cod_bonificacion_9 Nomina->configuracion->parametros liquidacion')
        elif not parametros_liquidacion.cod_indemnizacion.codigo:
            raise UserError(
                'Debe configurar parametros de gratificacion cod_indemnizacion Nomina->configuracion->parametros liquidacion')
        else:
            return parametros_liquidacion