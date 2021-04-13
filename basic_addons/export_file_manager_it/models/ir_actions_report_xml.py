# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class IrActionsReportXml(models.Model):
	_inherit = 'ir.actions.report.xml'

	# add EFM; Export File Manager Reports item
	report_type = fields.Selection(selection_add=[('efm_reports', 'EFM Reports')])