# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CustomExportFile(models.TransientModel):
	_name = 'custom.export.file'	
	
	output_name = fields.Char('Output filename', size=128)
	output_file = fields.Binary('Output file', readonly=True, filename="output_name")