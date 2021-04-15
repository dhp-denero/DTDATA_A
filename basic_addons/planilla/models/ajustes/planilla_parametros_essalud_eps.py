from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime
from odoo.exceptions import UserError
#FIXME deprecado 09/11/2018
class PlanillaParametrosEssalud(models.Model):

    _name="planilla.parametros.essalud.eps"
    ratio_essalud = fields.Float('% EsSalud', digits=(12, 2),help="Este valor se usara para el calculo del 9% en gratificacion y cts",default=9.0)
    ratio_eps =  fields.Float('% Eps', digits=(12, 2),help="Este valor se usara para el calculo del 9% en gratificacion y cts",default=6.75)


    @api.model
    def create(self,vals):
        if len(self.env['planilla.parametros.essalud.eps'].search([])) >= 1:
            raise UserError(
                "Solo puede haber un registro de ajuste!")
        else:
            return super(PlanillaParametrosEssalud,self).create(vals)

    @api.model
    def get_parametros_essalud_eps(self):

        parametros_essalud_eps = self.search([
        ], limit=1)
        if not parametros_essalud_eps.ratio_essalud:
            raise UserError(
                'Debe configurar parametros de essalud_eps ratio_essalud Nomina->configuracion->parametros essalud_eps')
        elif not parametros_essalud_eps.ratio_eps:
            raise UserError(
                'Debe configurar parametros de essalud_eps ratio_eps Nomina->configuracion->parametros essalud_eps')
        return parametros_essalud_eps