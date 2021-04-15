# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime


class PlanillaExportFile(models.TransientModel):
	_name = 'planilla.export.file'	
	
	output_name = fields.Char('Output filename', size=128)
	output_file = fields.Binary('Output file', readonly=True, filename="output_name")
