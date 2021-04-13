from odoo import api, fields, models, exceptions, tools, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

colors = [  ('red', 'Rojo'),
			('yellow', 'Amarillo'),
			('green', 'Verde'),
			('sky_blue', 'Celeste'),
			('blue', 'Azul'),
			('purple', 'Morado'),
			('pink', 'Rosado'),
			('gray', 'Gris'),
			('white', 'Blanco')]

class HrReportsConfig(models.Model):
	_name = 'hr.reports.config'

	attendance_color = fields.Selection(colors,'Color para Asistencia')
	justification_color = fields.Selection(colors,'Color para Justificacion')
	permission_color = fields.Selection(colors,'Color para Permiso')
	late_color = fields.Selection(colors,'Color para Tardanza')
	lack_color = fields.Selection(colors,'Color para Falta')

	@api.model
	def create(self,vals):
		if len(self.env['hr.reports.config'].search([])) > 0:
			raise UserError('No se puede crear mas de una configuracion')
		else:
			t = super(HrReportsConfig,self).create(vals)
			return t