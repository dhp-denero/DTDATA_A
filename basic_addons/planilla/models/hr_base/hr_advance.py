from odoo import api, fields, models, tools, _

class HrAdvance(models.Model):
	_name = 'hr.advance'

	employee_id = fields.Many2one('hr.employee','Empleado')
	amount = fields.Float('Monto')
	date = fields.Date('Fecha de Adelanto')
	advance_type_id = fields.Many2one('hr.advance.type','Tipo de Adelanto')
	state = fields.Selection([('not payed','No Pagado'),('paid out','Pagado')],default='not payed')

class HrAdvanceType(models.Model):
	_name = 'hr.advance.type'

	name = fields.Char('Nombre')
	input_id = fields.Many2one('planilla.inputs.nomina','Input')
	discount_type = fields.Selection([('07','Julio'),('12','Diciembre')],'T. Dscto. Gratificacion')