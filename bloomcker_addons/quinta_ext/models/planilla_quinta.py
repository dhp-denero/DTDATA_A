# -*- coding: utf-8 -*-
from openerp import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PlanillaLiquidacion(models.Model):
	_inherit = "planilla.liquidacion"

	@api.multi
	def get_certificado_quinta_wizard(self):
		return {
			'name': 'Exportar certificado de Quinta',
			'type': 'ir.actions.act_window',
			'res_model': 'certificate.quinta.wizard',
			'view_type': 'form',
			'view_mode': 'form',
			'views': [[False, "form"]],
			'target': 'new',
			'context': {'current_id': self.id,'employees':[line.employee_id.id for line in self.planilla_vacaciones_lines]}
			}
