from odoo import api, fields, models, tools, _

class HrEmployee(models.Model):

	_inherit = 'resource.calendar'

	average_hours = fields.Float('Horas Diarias de Trabajo')