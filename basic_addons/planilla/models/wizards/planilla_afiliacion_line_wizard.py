# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime

class PlanillaAfiliacionLineWizard(models.TransientModel):

    _name="planilla.afiliacion.line.wizard"
    #usados para el wizard para duplicar periodos

    fecha_ini = fields.Date("Fecha inicio",required="1")
    fecha_fin = fields.Date("Fecha fin",required="1")
    fecha_from_dest = fields.Date("Fecha inicio",required="1")
    fecha_to_dest = fields.Date("Fecha fin",required="1")

    @api.multi
    def do_rebuild(self):
        periodo_afiliacion_line_ids = self.env['planilla.afiliacion.line'].search( [('fecha_ini','=',self.fecha_ini ),('fecha_fin','=',self.fecha_fin )] )
        for row in periodo_afiliacion_line_ids:
            data = {
                'fecha_ini':self.fecha_from_dest,
                'fecha_fin':self.fecha_to_dest,
                'planilla_afiliacion_id':row.planilla_afiliacion_id.id,
                'fondo':row.fondo,
                'comf':row.comf,
                'comm':row.comm,
                'segi':row.segi,
                'remmax':row.remmax,
            }
            self.env['planilla.afiliacion.line'].create(data)