# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models

from datetime import datetime

class PlanillaAfiliacion(models.Model):
    _name = "planilla.afiliacion"
    _rec_name ="entidad"
    entidad= fields.Char("Entidad",help="Nombre de la AFP o ONP",required=True)     
    com_fija= fields.Float("Comision Fija")
    com_mix= fields.Float("Comision Mixta")
    prima_s= fields.Float("Prima Seguro")
    fondo= fields.Float("Fondo de Jubilacion")
    rem_ase= fields.Float("Remuneracion Asegurable")
    account_id = fields.Many2one('account.account','Cuenta Contable')




#FIXME: deprecado eliminar en el futuro
class PlanillaAfiliacionLine(models.Model):

    _name="planilla.afiliacion.line"
    _rec_name = "fondo"

    fecha_ini = fields.Date("Fecha inicio",required="1")
    fecha_fin = fields.Date("Fecha fin",required="1")
    fondo= fields.Float("Fondo",help="ESTE CAMPO  ES DE TIPO NUMERICO Y SIRVE PARA GUARDAR LA TASA QUE TIENE EN ESE PERIODO LA ENTIDAD ( AFP) ")  
    comf= fields.Float("% Comision",help="SIRVE PAA GUARDAR LA COMISION SOBRE FLUJO")
    comm= fields.Float("% Comision Mixta",help="SIRVE PARA GUARDAR EL PORCENTAJE DE COMISION MIXTA")
    segi= fields.Float("% Seguro invalides",help="SIRVE PARA GUARDAR EL PORCENTAJE DE SEGURO DE INVALIDEZ ,  QUE TIENE CADA AFP , ES UN CAMPO DE TIPO NUMERIC ")
    remmax= fields.Float("Remuneracion Maxima",help="SIRVE PARA GUARDAR LA REMUNERACION MAXIMA ASEGURABLE QUE  TIENE CADA AFP , ES UN CAMPO DE TIPO NUMERIC ")

    planilla_afiliacion_id = fields.Many2one('planilla.afiliacion', string="Afiliacion",required=True)
    


    @api.multi
    def _open_wizard(self):
        return {
            'name':'Duplicar Periodo',
            'type': 'ir.actions.act_window',
            'res_model': 'planilla.afiliacion.line.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }

    @api.multi
    def _open_wizard_actualizar(self):
        return {
            'name':'Actualizar AFP',
            'type': 'ir.actions.act_window',
            'res_model': 'planilla.actualizar.afps',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }

