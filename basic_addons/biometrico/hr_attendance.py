from odoo import api, fields, models, exceptions, tools, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class HrAttendanceIt(models.Model):
	_name = 'hr.attendance.it'

	employee_id = fields.Many2one('hr.employee','Empleado',required="1")
	department_id = fields.Many2one('hr.department','Department', related='employee_id.department_id',readonly=True)
	date = fields.Date()
	check_in_sch = fields.Float('Horario Entrada')
	check_out_sch = fields.Float('Horario Salida')
	check_in_bio = fields.Char('Biometrico Entrada')
	check_out_bio = fields.Char('Biometrico Salida')
	check_in = fields.Datetime('Entrada',required=False,default=False)
	check_out = fields.Datetime('Salida',required=False,default=False)
	late_minutes = fields.Float('Tiempo de Tardanza')
	attendance_period_id = fields.Many2one('hr.attendance.period')
	justification_id = fields.Many2one('hr.justification','Justificacion')
	related_type = fields.Many2one(related='justification_id.type_just_id',store=True)
	checked = fields.Boolean('Revisado')
	flag = fields.Boolean(default=False)

	@api.multi
	def get_tree_view(self):
		usuarios_hd = self.env['res.groups'].search([('name','=','Usuario RRHH')]).users.ids
		usuarios_b = self.env['res.groups'].search([('name','=','Usuario Jefe')]).users.ids
		if self._uid in usuarios_hd:
			return {
				'name':_('Mis Asistencias'),
				'type':'ir.actions.act_window',
				'view_type':'form',
				'view_mode':'tree,form,calendar',
				'res_model':'hr.attendance.it',
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
				'view_mode':'tree,form,calendar',
				'res_model':'hr.attendance.it',
				'context':{'search_default_group_by_employee':1},
				'domain':[('employee_id','in',employee_ids)]
			}
		else:
			return {
				'name':_('Mis Asistencias'),
				'type':'ir.actions.act_window',
				'view_type':'form',
				'view_mode':'tree,form,calendar',
				'res_model':'hr.attendance.it',
				'domain':[('employee_id.address_home_id.id','=',self.env['res.users'].browse(self._uid).partner_id.id)]
			}

	@api.multi
	def get_wizard(self):
		self.late_minutes = self.env['hr.attendance.period.line'].compute_late_minutes(self.check_in_sch,self.check_out_sch,self.check_in,self.check_out,self.justification_id)
		return self.env['hr.justification'].get_wizard(self,True)
	
	def get_date(self,vals):
		#if 'check_in' in vals and 'check_out' in vals:
		if vals['check_in'] and vals['check_out']:
			if type(vals['check_in']) is datetime:
				vals['date'] = datetime.strftime(vals['check_in'] - timedelta(hours=5),'%Y-%m-%d %H:%M:%S')[:10]
			else:
				date = datetime.strptime(vals['check_in'],'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)
				vals['date'] = datetime.strftime(date,'%Y-%m-%d %H:%M:%S')[:10]
		if vals['check_in'] and not vals['check_out']:
			if type(vals['check_in']) is datetime:
				vals['date'] = datetime.strftime(vals['check_in'] - timedelta(hours=5),'%Y-%m-%d %H:%M:%S')[:10]
			else:
				date = datetime.strptime(vals['check_in'],'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)
				vals['date'] = datetime.strftime(date,'%Y-%m-%d %H:%M:%S')[:10]
		if not vals['check_in'] and vals['check_out']:
			if type(vals['check_out']) is datetime:
				vals['date'] = datetime.strftime(vals['check_out'] - timedelta(hours=5),'%Y-%m-%d %H:%M:%S')[:10]
			else:
				date = datetime.strptime(vals['check_out'],'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)
				vals['date'] = datetime.strftime(date,'%Y-%m-%d %H:%M:%S')[:10]
		return vals

	@api.model
	def create(self,vals):
		vals = self.get_date(vals)
		t = super(HrAttendanceIt,self).create(vals)
		self.env['hr.attendance.period.line'].get_calendar(t)
		return t

	@api.multi
	def name_get(self):
		result = []
		for attendance in self:
			if not attendance.check_in and attendance.check_out:
				result.append((attendance.id, _("%(empl_name)s to %(check_out)s") % {
					'empl_name': attendance.employee_id.name_related,
					'check_out': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_out))),
				}))
			elif not attendance.check_out and attendance.check_in:
				result.append((attendance.id, _("%(empl_name)s from %(check_in)s") % {
					'empl_name': attendance.employee_id.name_related,
					'check_in': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_in))),
				}))
			elif not attendance.check_in and not attendance.check_out:
				result.append((attendance.id, _("%(empl_name)s") % {
					'empl_name': attendance.employee_id.name_related
				}))
			else:
				result.append((attendance.id, _("%(empl_name)s from %(check_in)s to %(check_out)s") % {
					'empl_name': attendance.employee_id.name_related,
					'check_in': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_in))),
					'check_out': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_out))),
				}))
		return result

	@api.constrains('check_in', 'check_out')
	def _check_validity_check_in_check_out(self):
		""" verifies if check_in is earlier than check_out. """
		for attendance in self:
			if attendance.check_in and attendance.check_out:
				if attendance.check_out < attendance.check_in:
					raise exceptions.ValidationError(_('"Check Out" time cannot be earlier than "Check In" time.'))

	@api.constrains('check_in','check_out')
	def _check_fields(self):
		for attendance in self:
			if not attendance.check_in and not attendance.check_out:
				raise exceptions.ValidationError(_('No se puede crear una asistencia sin marcaciones'))

	@api.multi
	def get_justification_wizard(self):
		usuarios_hd = self.env['res.groups'].search([('name','=','Usuario RRHH')]).users.ids
		usuarios_b = self.env['res.groups'].search([('name','=','Usuario Jefe')]).users.ids
		if self._uid in usuarios_hd or self._uid in usuarios_b:
			wizard = self.env['hr.justification.wizard'].create({'name':'Generar Justificaciones'})
			return{
				'name':'Generar Justificaciones',
				'type':'ir.actions.act_window',
				'res_id':wizard.id,
				'view_type':'form',
				'view_mode':'form',
				'res_model':'hr.justification.wizard',
				'views':[[self.env.ref('biometrico.view_hr_justification_wizard_form').id,'form']],
				'target':'new',
				'context':self._context
			}
		else:
			raise UserError('Lo sentimos usted no cuenta con permisos para realizar esta accion.')