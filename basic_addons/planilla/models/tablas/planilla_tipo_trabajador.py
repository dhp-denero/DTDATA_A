# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class PlanillaTipoTrabajador(models.Model):

    _name = 'planilla.tipo.trabajador'
    _description = 'TABLA 8: "TIPO DE TRABAJADOR, PENSIONISTA O PRESTADOR DE SERVICIOS"'
    _rec_name = 'descripcion'

    codigo = fields.Char(string='Codigo')
    descripcion = fields.Text(string='Descripcion')
    descripcion_abrev = fields.Char(string='Descripcion abreviada')
