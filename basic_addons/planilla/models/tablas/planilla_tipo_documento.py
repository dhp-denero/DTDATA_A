# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class hr_salary_rule(models.Model):

    _name = 'planilla.tipo.documento'
    _description = 'TABLA 3: TIPO DE DOCUMENTO DE IDENTIDAD'
    _rec_name = 'descripcion'
    codigo_sunat = fields.Char(string='Codigo Sunat')
    codigo_afp = fields.Char(string='Codigo AFP')
    descripcion = fields.Text(string='Descripcion')
    descripcion_abrev = fields.Char(string='Descripcion abreviada')
