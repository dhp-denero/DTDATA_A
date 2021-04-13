from odoo import api, fields, models, exceptions, tools, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import *
import time
from zk import ZK, const
from decimal import *

class HrBiometrico(models.Model):
	_name = 'hr.biometrico'

	name = fields.Char('Nombre')
	ip = fields.Char('Direccion IP')
	puerto = fields.Integer('Puerto')
	marcaciones_ids = fields.One2many('hr.marcaciones','biometrico_id')
	date = fields.Date('Fecha de Regularizacion',default=lambda self:date.today() - timedelta(days=1))
	active = fields.Boolean(string='Activo',default=False)
	responsable = fields.Many2one('hr.employee','Responsable')

	def test_connection(self):
		try:
			conn = None
			# create ZK instance
			zk = ZK(self.ip, port=self.puerto, timeout=5, password=0, force_udp=False, ommit_ping=False)
			conn = zk.connect()
			if conn:
				attendances = conn.get_attendance()
				if not attendances:
					conn.disconnect()
					return self.env['planilla.warning'].info(title='RESPUESTA', message="NO SE ENCONTRARON ASISTENCIAS PARA ESTE BIOMETRICO")
				conn.disconnect()
				return self.env['planilla.warning'].info(title='RESPUESTA', message="CONEXION EXITOSA")
		except Exception as e:
			raise UserError("Error in %s: %s"% (self.ip,e)) 
		finally:
			if conn:
				conn.disconnect()

	def test_cron_job(self):
		print(datetime.now())
		print('Testeando XD')

	@api.constrains('date')
	def _days_rule(self):
		for i in self:
			if datetime.strptime(i.date,'%Y-%m-%d').day >= (datetime.now()).day:
				raise UserError('La fecha de Regularizacion no puede ser mayor ni igual a la fecha actual')

	def daily_zk_get_data(self):
		self._get_attendances_subfunction()

	def daily_zk_get_data_by_day(self):
		self._get_attendances_subfunction(self.date)

	@api.multi
	def get_wizard(self):
		wizard = self.env['hr.biometrico.wizard'].create({'name':'Asistencias por Rango de Fechas'})
		return {
			'type':'ir.actions.act_window',
			'res_id':wizard.id,
			'view_mode':'form',
			'res_model':'hr.biometrico.wizard',
			'views':[[self.env.ref('biometrico.hr_biometrico_wizard_form_view').id,'form']],
			'target':'new'
		}

	def generate_medias(self,lines):
		hours, medias, aux, media, aux_line = [], [], 0, {}, None
		for line in sorted(lines,key=lambda l:l.hour_from):
			hours.append({'hour':line.hour_from,'line':line})
			hours.append({'hour':line.hour_to,'line':line})
		for c,h in enumerate(hours):
			if c == 0:
				media['in'] = 0.0
				aux = h['hour']
				aux_line = h['line']
			else:
				media['out'] = float(Decimal(str((aux + h['hour'])/2)).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))
				media['marcaciones'] = []
				media['line'] = aux_line
				aux_line = h['line']
				medias.append(media)
				media = {}
				media['in'] = float(Decimal(str((aux + h['hour'])/2)).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))
				aux = h['hour']
		media['out'] = 23.99
		media['marcaciones'] = []
		media['line'] = aux_line
		medias.append(media)
		return medias

	def _get_attendances_subfunction(self,param_day=False,emp_param=False):
		def create_att(employee,check_in_obj,check_out_obj,line=None):
			self.env['hr.attendance.it'].create({'employee_id':employee.id,
												'check_in_bio':check_in_obj.biometrico_name if check_in_obj else '',
												'check_out_bio':check_out_obj.biometrico_name if check_out_obj else '',
												'check_in':check_in_obj.date if check_in_obj else None,
												'check_out':check_out_obj.date if check_out_obj else None,
												'check_in_sch':line.hour_from if line else 0.0,
												'check_out_sch':line.hour_to if line else 0.0})
		try_flag = True
		biometricos = self.env['hr.biometrico'].search([('active','=',True)])
		yesteday = None
		try:
			for biometrico in biometricos:
				conn = None
				# create ZK instance
				zk = ZK(biometrico.ip, port=biometrico.puerto, timeout=5, password=0, force_udp=False, ommit_ping=False)
				conn = zk.connect()
				# disable device, this method ensures no activity on the device while the process is run
				conn.disable_device()
				attendances = conn.get_attendance()
				now = datetime.now()
				if param_day:
					diference = now - datetime.strptime(param_day,'%Y-%m-%d')
					yesterday = now.replace(hour=0, minute=0, second=0) - timedelta(days=diference.days)
					limit = now.replace(hour=23, minute=59, second=59) - timedelta(days=diference.days)
				else:
					yesterday = now.replace(hour=0, minute=0, second=0) - timedelta(days=1)
					limit = now.replace(hour=23, minute=59, second=59) - timedelta(days=1)
				for line in attendances:
					if line.timestamp > yesterday and line.timestamp < limit:
						if emp_param:
							employee = self.env['hr.employee'].search([('identification_id','=',line.user_id),('id','=',emp_param.id)])
						else:
							employee = self.env['hr.employee'].search([('identification_id','=',line.user_id)])
						if employee:
							self.env['hr.marcaciones'].create({
								'employee_id':employee.id,
								'date':line.timestamp + timedelta(hours=5),
								'biometrico_name':biometrico.name,
								'biometrico_id':biometrico.id})
				conn.enable_device()
		except Exception as e:
			try_flag = False
			if biometrico.responsable:
				email_data = {
							'subject': 'Error en Biometrico %s con ip %s el %s'%(biometrico.name,biometrico.ip,datetime.now()),
							'body_html':'Estimado (a) %s,<br/>'
										'Ocurrio el siguiente error: "%s", proceda a revisar las asistencias de ayer para poder regularizarlas'%(biometrico.responsable.name_related,e),
							'email_to': biometrico.responsable.work_email
							}
				email = self.env['mail.mail'].create(email_data)

				s = email.send()
			else:
				print("Error in %s: %s") % (biometrico.ip,e)
		finally:
			if conn:
				conn.disconnect()
		if try_flag:
			employees = []
			if emp_param:
				employees.append(emp_param)
			else:
				employees = self.env['hr.employee'].search([])
			for employee in employees:
				if employee.calendar_id:
					marcaciones = self.env['hr.marcaciones'].search([('employee_id','=',employee.id),
						('date','>',datetime.strftime(yesterday + timedelta(hours=5),'%Y-%m-%d %H:%M:%S')),
						('date','<',datetime.strftime(limit + timedelta(hours=5),'%Y-%m-%d %H:%M:%S'))])
					media_date = datetime(yesterday.year,yesterday.month,yesterday.day)
					lines = filter(lambda a: int(a.dayofweek) == yesterday.weekday() \
											and datetime.strptime(a.date_from,"%Y-%m-%d") <= media_date \
											and (datetime.strptime(a.date_to,"%Y-%m-%d") + timedelta(days=1)) > media_date,
											employee.calendar_id.attendance_ids)
					if len(lines) > 1:
						medias = self.generate_medias(lines)
					if len(marcaciones) > 0:
						entradas, salidas = [], []
						flag = False
						for marcacion in marcaciones:
							if len(lines) > 1:
								m_date = datetime.strptime(marcacion.date,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)
								hour = m_date.hour
								minute = m_date.minute/60.0
								hour = hour + minute
								for m in medias:
									if hour >= m['in'] and hour < m['out']:
										m['marcaciones'].append(marcacion)
								flag = True
							else:
								for line in employee.calendar_id.attendance_ids:
									if int(line.dayofweek) == yesterday.weekday():
										date_to = datetime.strptime(line.date_to,"%Y-%m-%d") + timedelta(days=1)
										date_from = datetime.strptime(line.date_from,"%Y-%m-%d")
										m_date = datetime.strptime(marcacion.date,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)
										if date_from <= m_date and date_to > m_date:
											media = float(Decimal(str((line.hour_to + line.hour_from)/2.0)).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))
											hour = m_date.hour
											minute = m_date.minute/60.0
											hour = hour + minute
											if hour <= media:
												entradas.append(marcacion)
											else:
												salidas.append(marcacion)
						
						if flag:
							check_in_obj = None
							check_out_obj = None
							for d,m in enumerate(medias,1):
								if d % 2 == 0:
									check_out_obj = max(m['marcaciones'],key=lambda x:x['date']) if len(m['marcaciones']) > 0 else False
									if check_in_obj or check_out_obj:
										if check_in_obj and check_out_obj:
											if (datetime.strptime(check_in_obj.date,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)).day == (datetime.strptime(check_out_obj.date,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)).day:
												create_att(employee,check_in_obj,check_out_obj,m['line'])
											else:
												create_att(employee,check_in_obj,None,m['line'])
												create_att(employee,None,check_out_obj,m['line'])
										else:
											create_att(employee,check_in_obj,check_out_obj,m['line'])
									check_in_obj = None
									check_out_obj = None
								else:
									check_in_obj = min(m['marcaciones'],key=lambda x:x['date']) if len(m['marcaciones']) > 0 else False
						else:
							check_in_obj = min(entradas,key=lambda x:x['date']) if len(entradas) > 0 else False
							check_out_obj = max(salidas,key=lambda x:x['date']) if len(salidas) > 0 else False
							if check_in_obj or check_out_obj:
								if check_in_obj and check_out_obj:
									if (datetime.strptime(check_in_obj.date,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)).day == (datetime.strptime(check_out_obj.date,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)).day:
										create_att(employee,check_in_obj,check_out_obj)
									else:
										create_att(employee,check_in_obj,None)
										create_att(employee,None,check_out_obj)
								else:
									create_att(employee,check_in_obj,check_out_obj)

class HrMarcaciones(models.Model):
	_name = 'hr.marcaciones'

	biometrico_id = fields.Many2one('hr.biometrico','Biometrico')
	employee_id = fields.Many2one('hr.employee','Empleado')
	date = fields.Datetime('Fecha')
	biometrico_name = fields.Char()

	@api.multi
	def get_wizard_generate(self):
		wizard = self.env['hr.employee.wizard'].create({'name':'Generar Horarios'})
		return{
			'name':'Generar Horarios',
			'type':'ir.actions.act_window',
			'res_id':wizard.id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'hr.employee.wizard',
			'views':[[self.env.ref('biometrico.view_hr_employee_wizard_form').id,'form']],
			'target':'new',
			'context':self._context
		}

class HrBiometricoWizard(models.TransientModel):
	_name = 'hr.biometrico.wizard'

	date_from = fields.Date(string='Fecha Desde',default=lambda self:date.today() - timedelta(days=2))
	date_to = fields.Date(string='Fecha Hasta',default=lambda self:date.today() - timedelta(days=1))
	employee_id = fields.Many2one('hr.employee',string='Empleado')

	@api.constrains('date_from','date_to')
	def _days_rule(self):
		for i in self:
			day = date.today()
			if datetime.strptime(i.date_from,'%Y-%m-%d').date() >= day or datetime.strptime(i.date_to,'%Y-%m-%d').date() >= day:
				raise UserError('Las fechas de Regularizacion no pueden ser mayores ni iguales a la fecha actual')

	@api.constrains('date_from','date_to')
	def _compare_dates(self):
		for i in self:
			if i.date_to < i.date_from:
				raise UserError('La fecha inicial no puede ser mayor a la final')

	def zk_get_date_by_range(self):
		def daterange(date1, date2):
			for n in range(int ((date2 - date1).days + 1)):
				yield date1 + timedelta(n)
		start = datetime.strptime(self.date_from,'%Y-%m-%d')
		end = datetime.strptime(self.date_to,'%Y-%m-%d')
		for dt in daterange(start,end):
			dt = datetime.strftime(dt,'%Y-%m-%d')
			print('employee_id',self.employee_id)
			if self.employee_id:
				attendances = self.env['hr.attendance.it'].search([('date','=',dt),('employee_id','=',self.employee_id.id)],limit=1)
			else:
				attendances = self.env['hr.attendance.it'].search([('date','=',dt),('flag','=',False)])

			if len(attendances) > 0:
				continue
			else:
				if self.employee_id:
					self.env['hr.biometrico']._get_attendances_subfunction(dt,self.employee_id)
				else:
					self.env['hr.biometrico']._get_attendances_subfunction(dt)