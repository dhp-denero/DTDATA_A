# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class PlanillaTipoSuspencion(models.Model):

    _name = 'planilla.tipo.suspension'
    _description = 'TABLA 21: "TIPO DE SUSPENSION DE LA RELACION LABORAL"'
    _rec_name = 'descripcion'

    codigo = fields.Char(string='Codigo')
    descripcion = fields.Text(string='Descripcion')
    descripcion_abrev = fields.Char(string='Descripcion abreviada')
    ajustes_vacaciones_id = fields.Many2one('planilla.control.vacaciones.ajustes')
