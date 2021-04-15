# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime


class PlanillaExportPlameRem(models.Model):
    _name = 'planilla.export.plame.rem'
    _auto = False

    tipo_doc = fields.Char('Tpo Documento')
    identification_id = fields.Char('Nro. documento del trabajador')
    codigo_remunerativo = fields.Float(
        'Código de concepto remunerativo y/o no remunerativo', digits=(12, 2))
    monto_devengado = fields.Float(
        'Monto devengado', digits=(12, 2))
    monto_pagado_descontado = fields.Float(
        'Monto pagado/descontado', digits=(12, 2))
