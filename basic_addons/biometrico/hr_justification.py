from odoo import api, fields, models, exceptions, tools, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from decimal import *
	
#Este modelo se utiliza para las justificaciones pero tambien lo utilizo como wizard
class HrAttendancePeriodWizard(models.Model):
	_name = "hr.justification"

	type_just_id = fields.Many2one('hr.justification.type','Tipo de Justificacion')
	related_bool = fields.Boolean(related="type_just_id.is_permission")
	
	def _get_employee(self):
		return self.env['hr.employee'].search([('address_home_id.id','=',self.env['res.users'].browse(self._uid).partner_id.id)],limit=1)
		 
	employee_id = fields.Many2one('hr.employee','Empleado',default=_get_employee)
	line_id = fields.Many2one('hr.attendance.period.line')
	hours = fields.Float('Tiempo Justificado')
	date = fields.Date('Fecha de Justificacion')
	motivo = fields.Text('Motivo')
	permission_from = fields.Date('Permiso Desde')
	permission_to = fields.Date('Permiso Hasta')
	state = fields.Selection([('draft', 'Borrador'),
							  ('approved', 'Aprobado'),
							  ('canceled', 'Cancelado')], default="draft")
	attendance_id = fields.Many2one('hr.attendance.it', 'Asistencia',ondelete='cascade')
	approver_user = fields.Many2one('res.partner', 'Aprobado por')
	canceler_user = fields.Many2one('res.partner', 'Cancelado por')
	is_lack = fields.Boolean(default=False)

	@api.multi
	def unlink(self):
		for j in self:
			if j.type_just_id.is_permission:
				self.env['hr.attendance.it'].search([('date','>=',j.permission_from),('date','<=',j.permission_to),('justification_id','=',j.id)]).unlink()
			return super(HrAttendancePeriodWizard,self).unlink()

	@api.multi
	def approve_justification(self):
		self.approver_user = self.env['res.users'].browse(self._uid).partner_id.id
		self.state = 'approved'


	@api.multi
	def cancel_justification(self):
		self.canceler_user = self.env['res.users'].browse(self._uid).partner_id.id
		self.state = 'canceled'

	@api.multi
	def unapprove_justification(self):
		if self.is_lack:
			self.attendance_id.unlink()
		else:
			self.state = 'draft'

	@api.multi
	def name_get(self):
		result = []
		for justification in self:
			if justification.related_bool:
				name = "Permiso %s para %s" %(justification.type_just_id.name,justification.employee_id.name_related)
				result.append((justification.id,name))
			else:
				name = "Justificacion %s para %s" %(justification.type_just_id.name,justification.employee_id.name_related)
				result.append((justification.id,name))
		return result

	@api.constrains('permission_from','permission_to','related_bool')
	def _check_ranges(self):
		for obj in self:
			justificaciones = self.env['hr.employee'].browse(obj['employee_id'].id).justification_ids
			if obj['related_bool']:
				justificaciones = filter(lambda j:j.related_bool,justificaciones)
				for justificacion in justificaciones:
					#Esta logica se utiliza para verificar que el rango de fechas enviado al crear la justificacion
					#no esta ni dentro del rango de otra justificacion ni englobe el rango de alguna justificacion
					#asegurandonos de que este nuevo rango solo este despues o antes que otro rango de fechas
					if justificacion.id != obj['id']:
						if (obj['permission_from'] <= justificacion.permission_from and obj['permission_to'] >= justificacion.permission_to) or \
						   (justificacion.permission_from <= obj['permission_from'] and justificacion.permission_to >= obj['permission_to']) or \
						   (obj['permission_from'] >= justificacion.permission_from and obj['permission_from'] <= justificacion.permission_to) or \
						   (obj['permission_to'] >= justificacion.permission_from and obj['permission_to'] <= justificacion.permission_to):
							raise UserError('Este empleado ya tiene un permiso dentro de este rango de fechas')

	@api.multi
	def get_wizard(self,line,flag=False):
		context = {
					'default_employee_id':line.employee_id.id,
					'default_hours':line.late_minutes,
					'default_date':line.check_in[:10] if line.check_in else line.check_out[:10]
				}
		if flag:
			res_id = line.justification_id.id if line.justification_id else self.id
			context['default_attendance_id'] = line.id
		else:
			res_id = line.attendance_id.justification_id
			res_id = res_id.id if res_id else self.id
			context['default_attendance_id'] = line.attendance_id.id
			context['default_line_id'] = line.id
		return {
			'name':_('Justificacion'),
			'type':'ir.actions.act_window',
			'res_id':res_id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'hr.justification',
			'views':[[self.env.ref('biometrico.period_line_wizard').id,'form']],
			'target':'new',
			'context': context
		}

	@api.multi
	def get_tree_view(self):
		usuarios_hd = self.env['res.groups'].search([('name','=','Usuario RRHH')]).users.ids
		usuarios_b = self.env['res.groups'].search([('name','=','Usuario Jefe')]).users.ids
		if self._uid in usuarios_hd:
			return {
				'name':_('Justificaciones'),
				'type':'ir.actions.act_window',
				'view_type':'form',
				'view_mode':'tree,form',
				'res_model':'hr.justification',
				'context':{'search_default_group_by_employee':1}
			}
		elif self._uid in usuarios_b:
			partner_id = self.env['res.users'].browse(self._uid).partner_id
			job_group_id = self.env['hr.job.group'].search([('related_partner','=',partner_id.id)],limit=1)
			employee_ids = [i.id for i in job_group_id.employee_ids]
			return {
				'name':_('Mis Asistencias'),
				'type':'ir.actions.act_window',
				'view_type':'form',
				'view_mode':'tree,form',
				'res_model':'hr.justification',
				'context':{'search_default_group_by_employee':1},
				'domain':[('employee_id','in',employee_ids)]
			}
		else:
			return {
				'name':_('Justificaciones'),
				'type':'ir.actions.act_window',
				'view_type':'form',
				'view_mode':'tree,form',
				'res_model':'hr.justification',
				'domain':[('employee_id.address_home_id.id','=',self.env['res.users'].browse(self._uid).partner_id.id)]
			}

	@api.multi
	def add_justification(self):
		usuarios = self.env['res.groups'].search([('name','=','Usuario Jefe')]).users.ids
		justifications = [i.id for i in self.env['hr.employee'].browse(self.employee_id.id).justification_ids]
		justifications.append(self.id)
		self.employee_id.write({'justification_ids':[(6,0,justifications)]})
		self.attendance_id.write({'justification_id':self.id})
		if self._uid in usuarios:
			self.approve_justification()
	
	@api.multi
	def generate_attendances(self):
		def daterange(date1, date2):
			for n in range(int ((date2 - date1).days + 1)):
				yield date1 + timedelta(n)

		p_from = datetime.strptime(self.permission_from,'%Y-%m-%d')
		p_to = datetime.strptime(self.permission_to,'%Y-%m-%d')
		
		for dt in daterange(p_from,p_to):
			self.env['hr.attendance.it'].create({
					'employee_id':self.employee_id.id,
					'check_in':dt.replace(hour=0, minute=0, second=0) + timedelta(hours=5),
					'check_out':dt.replace(hour=23, minute=59, second=59) + timedelta(hours=5),
					'justificacion_id':self.id,
					'flag':True
				})
		return self.env['planilla.warning'].info(
			title='Resultado', message="Se han creado asistencias para %s desde %s hasta %s" 
			% (self.employee_id.name_related,p_from,p_to))
	
	@api.constrains('permission_from','permission_to')
	def _check_dates(self):
		for justification in self:
			if justification.permission_to and justification.permission_from:
				if justification.permission_to < justification.permission_from:
					raise exceptions.ValidationError(_('La fecha final no puede ser menor ni igual a la fecha inicial'))

	@api.constrains('related_bool')
	def _check_bool(self):
		for justification in self:
			if justification.related_bool:
				justification.hours = 0

class HrJustification(models.Model):
	_name = 'hr.justification.type'

	name = fields.Char('Nombre')
	is_permission = fields.Boolean('Es un permiso',default=False)

	@api.model
	def create(self,vals):
		if 'name' in vals:
			for i in self.env['hr.justification.type'].search([]):
				if i.name == vals['name']:
					raise UserError('No pueden existir dos tipos de justificacion con el mismo nombre')
		return super(HrJustification,self).create(vals)

class HrJustificationWizard(models.TransientModel):
	_name = 'hr.justification.wizard'

	hours = fields.Float('Tiempo Justificado')
	date = fields.Date('Fecha de Justificacion')
	motivo = fields.Text('Motivo')
	type_just_id = fields.Many2one('hr.justification.type','Tipo de Justificacion')

	@api.multi
	def generate_justifications(self):
		for attendance_id in self._context['active_ids']:
			attendance = self.env['hr.attendance.it'].browse(attendance_id)
			t = self.env['hr.justification'].create({
					'employee_id':attendance.employee_id.id,
					'hours':self.hours,
					'date':self.date,
					'motivo':self.motivo,
					'type_just_id':self.type_just_id.id,
					'attendance_id':attendance.id,
					'state':'approved',
					'approver_user':self.env['res.users'].browse(self._uid).partner_id.id
				})
			attendance.write({'justification_id':t.id})