# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime

class PlanillaLiquidacionPdfWizard(models.TransientModel):

    _name="planilla.liquidacion.pdf.wizard"

    forma       = fields.Selection([('1','Todos'),('2','Uno')],'Imprimir',required=True,default='1')
    employee_id = fields.Many2one('hr.employee','Empleado')

    @api.multi
    def do_rebuild(self):
        hl = self.env['planilla.liquidacion'].search([('id','=',self.env.context['active_id'])])[0]
        hllc = self.env['planilla.liquidacion.vacaciones.line'].search([('planilla_liquidacion_id','=',hl.id),('employee_id','=',self.employee_id.id)])
        
        if self.forma == '1':
            return hl.get_liquidacion_pdf(self.env.context['employees'])
        if self.forma == '2':
            if not len(hllc):
                raise ValidationError("Alerta!", u"No existe el empleado seleccionado en liquidaciones.")
            else:
                return hl.get_liquidacion_pdf(self.employee_id.id)
        return True