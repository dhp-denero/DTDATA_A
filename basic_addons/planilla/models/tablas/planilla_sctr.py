from odoo import models, fields, api

class PlanillaSctr(models.Model):
	_name="planilla.sctr"

	name = fields.Char('Descripcion')
	code = fields.Char('Codigo')
	porcentaje = fields.Float('% ', digits=(3, 2))