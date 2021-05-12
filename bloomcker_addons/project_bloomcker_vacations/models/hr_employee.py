# -*- coding: utf-8 -*-
from odoo import models, fields, api

class EmployeeExt(models.Model):
	_inherit = 'hr.employee'

	name_total = fields.Char('Nombre Completo', compute='get_name_total')

	def get_name_total(self):
		for record in self:
			record.name_total = record.nombres + ' ' + record.a_paterno + ' ' + record.a_materno
