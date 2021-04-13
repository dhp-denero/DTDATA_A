from odoo import api, fields, models, exceptions, tools, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class HrLackPeriod(models.Model):
	_name = 'hr.lack.period'

	payslip_run_id = fields.Many2one('hr.payslip.run','Periodo')
	line_ids = fields.One2many('hr.lack.period.line','period_lack_id')
	date_from = fields.Date('Fecha desde',default=datetime.now())
	date_to = fields.Date('Fecha hasta')
	everyone = fields.Boolean('Todos',default=True)

	def _get_user_id(self):
		return self.env['res.users'].browse(self._uid).id

	res_user_id = fields.Many2one('res.users',default=_get_user_id)

	@api.onchange('res_user_id')
	def _get_domain(self):
		usuarios_hd = self.env['res.groups'].search([('name','=','Usuario RRHH')]).users.ids
		usuarios_b = self.env['res.groups'].search([('name','=','Usuario Jefe')]).users.ids
		if self._uid in usuarios_hd:
			domain = [('id','in',self.env['hr.employee'].search([]).ids)]
			return domain
		else:
			if self._uid in usuarios_b:
				partner_id = self.env['res.users'].browse(self._uid).partner_id
				job_group_id = self.env['hr.job.group'].search([('related_partner','=',partner_id.id)],limit=1)
				employee_ids = [i.id for i in job_group_id.employee_ids]
				domain = [('id','in',employee_ids)]
				return domain

	employee_ids = fields.Many2many('hr.employee','lack_employee_default_rel','lack_period_id','employee_id','Empleados',domain=_get_domain)

	@api.multi
	def get_lacks(self):
		self.line_ids.unlink()
		def daterange(date1, date2):
			for n in range(int ((date2 - date1).days + 1)):
				yield date1 + timedelta(n)
		if self._uid != self.res_user_id.id:
			self.write({'res_user_id':self._uid,'everyone':True,'employee_ids':[(6,0,[])]})
		usuarios_hd = self.env['res.groups'].search([('name','=','Usuario RRHH')]).users.ids
		usuarios_b = self.env['res.groups'].search([('name','=','Usuario Jefe')]).users.ids
		if self._uid in usuarios_hd:
			if self.everyone:
				employees = self.env['hr.employee'].search([])
			else:
				employees = self.employee_ids
		else:
			if self._uid in usuarios_b:
				if self.everyone:
					partner_id = self.env['res.users'].browse(self._uid).partner_id
					job_group_id = self.env['hr.job.group'].search([('related_partner','=',partner_id.id)],limit=1)
					employees = [i.id for i in job_group_id.employee_ids]
				else:
					employees = self.employee_ids

		start = datetime.strptime(self.date_from,'%Y-%m-%d')
		end = datetime.strptime(self.date_to,'%Y-%m-%d')
		dates=[]
		for dt in daterange(start,end):
			dates.append(dt)
		for employee in employees:
			attendances = self.env['hr.attendance.it'].search([('date','>=',self.date_from),('date','<=',self.date_to),('employee_id','=',employee.id)])
			att_dates = map(lambda a:datetime.strptime(a.date,'%Y-%m-%d'),attendances)
			for date in dates:
				if date not in att_dates and date.weekday() != 6:
					if employee.calendar_id:
						flag = False
						for line in employee.calendar_id.attendance_ids:
							if int(line.dayofweek) == date.weekday() \
								and date >= datetime.strptime(line.date_from,'%Y-%m-%d') \
								and date <= datetime.strptime(line.date_to,'%Y-%m-%d'):
								flag = True
						if flag:
							self.env['hr.lack.period.line'].create({'employee_id':employee.id,'date':date,'period_lack_id':self.id})
		return {}

	@api.multi
	def filter_employees(self):
		if self._uid != self.res_user_id.id:
			self.write({'res_user_id':self._uid,'everyone':True})
		return {
			'name':_('Empleados'),
			'type':'ir.actions.act_window',
			'res_id':self.id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'hr.lack.period',
			'views':[[self.env.ref('biometrico.hr_lack_period_employees').id,'form']],
			'target':'new'
		}

class HrLackPeriodLine(models.Model):
	_name = 'hr.lack.period.line'

	period_lack_id = fields.Many2one('hr.lack.period')
	employee_id = fields.Many2one('hr.employee','Empleado')
	date = fields.Date('Fecha')

	@api.multi
	def get_wizard(self):
		weekday = datetime.strptime(self.date,'%Y-%m-%d').weekday()
		calendar = self.employee_id.calendar_id
		if calendar:
			line = next(iter(filter(lambda c:int(c.dayofweek) == weekday and self.date >= c.date_from and self.date <= c.date_to,calendar.attendance_ids)),None)
		wizard = self.env['hr.lack.period.line.wizard'].create({
			'name':'Justificaion de Ausencias',
			'employee_id':self.employee_id.id,
			'date':self.date,
			'hours':line.hour_to - line.hour_from if line else 0,
			'line_id':self.id
			})
		return {
			'type':'ir.actions.act_window',
			'res_id':wizard.id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'hr.lack.period.line.wizard',
			'views':[[self.env.ref('biometrico.hr_lack_period_line_wizard').id,'form']],
			'target':'new'
		}

class HrLackPeriodLineWizard(models.TransientModel):
	_name = 'hr.lack.period.line.wizard'

	type_just_id = fields.Many2one('hr.justification.type','Tipo de Justificacion')
	motivo = fields.Text('Motivo')
	employee_id = fields.Many2one('hr.employee')
	date = fields.Date()
	hours = fields.Float()
	line_id = fields.Many2one('hr.lack.period.line')

	@api.multi
	def create_just(self):
		att = self.env['hr.attendance.it'].create({
					'employee_id':self.employee_id.id,
					'check_in':datetime.strptime(self.date,'%Y-%m-%d').replace(hour=0, minute=0, second=0) + timedelta(hours=5),
					'check_out':datetime.strptime(self.date,'%Y-%m-%d').replace(hour=23, minute=59, second=59) + timedelta(hours=5)
				})
		
		t = self.env['hr.justification'].create({
					'employee_id':self.employee_id.id,
					'hours':self.hours,
					'date':self.date,
					'motivo':self.motivo,
					'type_just_id':self.type_just_id.id,
					'attendance_id':att.id,
					'state':'approved',
					'approver_user':self.env['res.users'].browse(self._uid).partner_id.id,
					'is_lack':True
				})
		att.write({'justification_id':t.id})
		pl_id = self.line_id.period_lack_id.id
		self.line_id.unlink()
		return {
            'res_id':pl_id,
            'view_type':'form',
            'view_mode':'form',
            'res_model':'hr.lack.period',
            'views':[[self.env.ref('biometrico.hr_lack_period_form').id,'form']],
            'type':'ir.actions.act_window',
        }