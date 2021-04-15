# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime


class PlanillaExportPlameHorasRem(models.Model):
    _name = 'planilla.export.plame.horas.rem'
    _auto = False

    tipo_doc = fields.Char('Tpo Documento')
    identification_id = fields.Char('Nro. documento del trabajador')
    horas_ordinarias = fields.Float(
        'Horas Ordinarias Trabajadas', digits=(12, 2))
    minutos_ordinarios = fields.Char()
    horas_sobretiempo = fields.Float(
        'Horas sobretiempo', digits=(12, 2))
    minutos_sobretiempo = fields.Float(
        'Minutos sobretiempo', digits=(12, 2))
