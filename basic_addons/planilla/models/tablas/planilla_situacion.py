# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class PlanillaSituacion(models.Model):

    _name = 'planilla.situacion'
    _description = 'TABLA 15: "SITUACION DEL TRABAJADOR O PENSIONISTA"'
    _rec_name = 'descripcion'

    codigo = fields.Char(string='Codigo')
    descripcion = fields.Text(string='Descripcion',required=True)
    descripcion_abrev = fields.Char(string='Descripcion abreviada',required=True)
