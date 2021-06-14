# -*- coding: utf-8 -*-
from openerp import models, fields, api
from odoo.exceptions import UserError, ValidationError


class CertificateQuintaWizard(models.TransientModel):
	_name = 'certificate.quinta.wizard'

	employee_ids = fields.Many2many('hr.employee', 'empleados')
	current = fields.Many2one('planilla.liquidacion', 'Liquidación')

	def do_rebuild(self):
		current = self.env['planilla.liquidacion'].search([('id', '=', int(self.env.context.get('current_id')))])
		self.current = int(self.env.context.get('current_id'))
		if self.employee_ids:
			return self.env['report'].get_action(self, 'quinta_ext.certificate_quinta_report')
		else:
			raise ValidationError(u'Debe tomar al menos un Empleado')

	def buscar_dicc(self, it, clave, valor, total):
		for dicc in it:
			if dicc[clave] == valor:
				dicc["total"] += total
				return it
		return False


	def get_rem_bruta(self, employee):
		employee_id = self.env['hr.employee'].search([('id', '=', int(employee))])
		lines = self.env['hr.payslip.line'].search([('employee_id', '=', employee_id.id)])
		ingresos = []
		for line in lines:
			if line.category_id.code == "ING" and line.slip_id.date_from <= self.current.date_start and line.slip_id.date_from[0:4] == self.current.year:
				flag = self.buscar_dicc(ingresos, "code", line.code, line.total)
				if flag:
					ingresos = flag
				else:
					if line.total:
						vals = {
							'code':line.code,
							'total':line.total,
							'name':line.name
						}
						ingresos.append(vals)
		return ingresos

	def sum_rem_bruta(self, ingresos):
		total = 0
		for ingreso in ingresos:
			total += ingreso['total']
		return total

	def get_deducion(self, total):
		deduccion = self.env['planilla.quinta.categoria'].search([], limit=1)
		if deduccion:
			for line in deduccion.uits:
				if line.anio.name == self.current.year:
					return [line.valor * 7,  line.valor, total - line.valor * 7]
		else:
			raise ValidationError(u'No hay registro de parametros de quinta')
		raise ValidationError(u'No hay registro de año fiscal en parametros de quinta')

	def get_impuesto_renta(self):
		deduccion = self.env['planilla.quinta.categoria'].search([], limit=1)
		impuestos = []
		if deduccion:
			for line in deduccion.limites:
				vals = {
					'limite': line.limite,
					'monto': line.monto,
					'tasa': 0,
					'total': 0,
				}
				for tasa in deduccion.tasas:
					if vals['limite'] == tasa.limite:
						vals['tasa'] = tasa.tasa*100
						vals['total'] = vals['monto'] * tasa.tasa
				impuestos.append(vals)

			return impuestos
		else:
			raise ValidationError(u'No hay registro de parametros de quinta')
