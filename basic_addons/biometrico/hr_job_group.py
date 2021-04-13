from odoo import api, fields, models, exceptions, tools, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from decimal import *
	
class HrJobGroup(models.Model):
	_name = "hr.job.group"

	name = fields.Char('Nombre del Grupo')
	boss_id = fields.Many2one('hr.employee','Jefe de Grupo')
	related_partner = fields.Many2one('res.partner',related='boss_id.address_home_id',store=True)
	employee_ids = fields.Many2many('hr.employee','job_group_employee_default_rel','job_group_id','employee_id',"Empleados")

	@api.constrains('related_partner')
	def _check_partner(self):
		for group in self:
			if not group.related_partner:
				raise exceptions.ValidationError(_('El empleado seleccionado no tiene un partner asignado'))
			if self.env['hr.job.group'].search([('related_partner','=',group.related_partner.id),('id','!=',group.id)]):
				raise exceptions.ValidationError(_('No se puede crear dos grupos con el mismo jefe'))