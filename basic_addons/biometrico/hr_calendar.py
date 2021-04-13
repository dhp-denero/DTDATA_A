from odoo import api, fields, models, exceptions, tools, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from decimal import *

class ResourceCalendar(models.Model):
	_inherit = 'resource.calendar'

	@api.multi
	def get_wizard(self):
		wizard = self.env['resource.calendar.wizard'].create({'name':'Generar Dias'})
		return{
			'name':'Generar Dias',
			'type':'ir.actions.act_window',
			'res_id':wizard.id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'resource.calendar.wizard',
			'views':[[self.env.ref('biometrico.view_resource_calendar_wizard_form').id,'form']],
			'target':'new',
			'context':self._context
		}

class ResourceCalendarAttendance(models.Model):
	_inherit = 'resource.calendar.attendance'

	@api.multi
	def delete_line(self):
		calendar = self.calendar_id
		self.unlink()
		return calendar.refresh()

class ResourceCalendarWizard(models.TransientModel):
	_name = 'resource.calendar.wizard'

	day_lines = fields.One2many('resource.calendar.wizard.line','calendar_wizard_id')
	date_from = fields.Date('Fecha Desde')
	date_to = fields.Date('Fecha Hasta')
	hour_from = fields.Float('Hora Desde')
	hour_to = fields.Float('Hora Hasta')
	unequal_calendar = fields.Boolean('Horario Desigual',default=True)
	monday = fields.Boolean('Lunes',default=False)
	tuesday = fields.Boolean('Martes',default=False)
	wednesday = fields.Boolean('Miercoles',default=False)
	thursday = fields.Boolean('Jueves',default=False)
	friday = fields.Boolean('Viernes',default=False)
	saturday = fields.Boolean('Sabado',default=False)
	sunday = fields.Boolean('Domingo',default=False)

	def get_day(self,day):
		if day == '0':
			return 'L'
		elif day == '1':
			return 'M'
		elif day == '2':
			return 'X'
		elif day == '3':
			return 'J'
		elif day == '4':
			return 'V'
		elif day == '5':
			return 'S'
		else:
			return 'D'

	@api.multi
	def generate_days(self):
		for calendar_id in self._context['active_ids']:
			if self.unequal_calendar:
				for line in self.day_lines:
					self.env['resource.calendar.attendance'].create({
							'name':self.get_day(line.day),
							'dayofweek':line.day,
							'hour_from':line.hour_from,
							'hour_to':line.hour_to,
							'date_from':self.date_from,
							'date_to':self.date_to,
							'calendar_id':calendar_id
						})
			else:
				if self.monday:
					self.env['resource.calendar.attendance'].create({
							'name':'L',
							'dayofweek':'0',
							'hour_from':self.hour_from,
							'hour_to':self.hour_to,
							'date_from':self.date_from,
							'date_to':self.date_to,
							'calendar_id':calendar_id
						})
				if self.tuesday:
					self.env['resource.calendar.attendance'].create({
							'name':'M',
							'dayofweek':'1',
							'hour_from':self.hour_from,
							'hour_to':self.hour_to,
							'date_from':self.date_from,
							'date_to':self.date_to,
							'calendar_id':calendar_id
						})
				if self.wednesday:
					self.env['resource.calendar.attendance'].create({
							'name':'X',
							'dayofweek':'2',
							'hour_from':self.hour_from,
							'hour_to':self.hour_to,
							'date_from':self.date_from,
							'date_to':self.date_to,
							'calendar_id':calendar_id
						})
				if self.thursday:
					self.env['resource.calendar.attendance'].create({
							'name':'J',
							'dayofweek':'3',
							'hour_from':self.hour_from,
							'hour_to':self.hour_to,
							'date_from':self.date_from,
							'date_to':self.date_to,
							'calendar_id':calendar_id
						})
				if self.friday:
					self.env['resource.calendar.attendance'].create({
							'name':'V',
							'dayofweek':'4',
							'hour_from':self.hour_from,
							'hour_to':self.hour_to,
							'date_from':self.date_from,
							'date_to':self.date_to,
							'calendar_id':calendar_id
						})
				if self.saturday:
					self.env['resource.calendar.attendance'].create({
							'name':'S',
							'dayofweek':'5',
							'hour_from':self.hour_from,
							'hour_to':self.hour_to,
							'date_from':self.date_from,
							'date_to':self.date_to,
							'calendar_id':calendar_id
						})
				if self.sunday:
					self.env['resource.calendar.attendance'].create({
							'name':'D',
							'dayofweek':'6',
							'hour_from':self.hour_from,
							'hour_to':self.hour_to,
							'date_from':self.date_from,
							'date_to':self.date_to,
							'calendar_id':calendar_id
						})

class ResourceCalendarWizardLine(models.TransientModel):
	_name = 'resource.calendar.wizard.line'

	calendar_wizard_id = fields.Many2one('resource.calendar.wizard')
	day = fields.Selection([('0','Lunes'),
							('1','Martes'),
							('2','Miercoles'),
							('3','Jueves'),
							('4','Viernes'),
							('5','Sabado'),
							('6','Domingo')],'Dia')
	hour_from = fields.Float('Hora Desde')
	hour_to = fields.Float('Hora Hasta')

class HrEmployeeWizard(models.Model):
	_name = 'hr.employee.wizard'

	reference_name = fields.Char('Nombre de referencia')
	referenced_calendar = fields.Many2one('resource.calendar','Horario Plantilla')
	automatic_add = fields.Boolean('Agregar Automaticamente')

	@api.multi
	def generate_calendars(self):
		for employee_id in self._context['active_ids']:
			attendance_ids = []
			employee = self.env['hr.employee'].browse(employee_id)
			if self.automatic_add:
				t = self.env['resource.calendar'].create({
							'name':self.reference_name+' - '+employee.name_related,
							'uom_id':self.referenced_calendar.uom_id.id
						})
				for line in self.referenced_calendar.attendance_ids:
					a = self.env['resource.calendar.attendance'].create({
							'name':line.name,
							'dayofweek':line.dayofweek,
							'hour_from':line.hour_from,
							'hour_to':line.hour_to,
							'date_from':line.date_from,
							'date_to':line.date_to,
							'calendar_id':t.id
						})
					attendance_ids.append(a.id)

				t.write({'attendance_ids':[(6,0,attendance_ids)]})
				employee.write({'calendar_id':t.id})
			else:
				self.env['resource.calendar'].create({
							'name':self.reference_name+' - '+employee.name_related,
							'uom_id':self.referenced_calendar.uom_id.id
						})
				for line in self.referenced_calendar.attendance_ids:
					a = self.env['resource.calendar.attendance'].create({
							'name':line.name,
							'dayofweek':line.dayofweek,
							'hour_from':line.hour_from,
							'hour_to':line.hour_to,
							'date_from':line.date_from,
							'date_to':line.date_to,
							'calendar_id':t.id
						})
					attendance_ids.append(a.id)

				t.write({'attendance_ids':[(6,0,attendance_ids)]})
				