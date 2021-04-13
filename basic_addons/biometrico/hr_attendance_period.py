from odoo import api, fields, models, exceptions, tools, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from decimal import *
import math
from itertools import groupby
import requests
import logging
import base64

_logger = logging.getLogger(__name__)

class HrAttendancePeriod(models.Model):
	_name = 'hr.attendance.period'
	_rec_name = 'payslip_run_id'

	payslip_run_id = fields.Many2one('hr.payslip.run','Periodo')
	date_from = fields.Date('Fecha desde',default=datetime.now())
	date_to = fields.Date('Fecha hasta')
	everyone = fields.Boolean('Todos',default=True)

	#@api.onchange('res_user_id','everyone')
	#def _get_domain(self):
		
	#	return domain

	employee_ids = fields.Many2many('hr.employee','attendance_employee_default_rel','attendance_period_id','employee_id','Empleados',domain=lambda self:self._context.get('domain',[]))
	
	def _get_attendance_domain(self):
		usuarios_hd = self.env['res.groups'].search([('name','=','Usuario RRHH')]).users.ids
		usuarios_b = self.env['res.groups'].search([('name','=','Usuario Jefe')]).users.ids
		if self._uid in usuarios_hd:
			domain = []
			return domain
		else:
			if self._uid in usuarios_b:
				domain = [('hide_line','=',False)]
				return domain

	attendance_ids = fields.One2many('hr.attendance.period.line','attendance_period_id',domain=_get_attendance_domain)
	
	def _get_user_id(self):
		return self.env['res.users'].browse(self._uid).id

	res_user_id = fields.Many2one('res.users',default=_get_user_id)

	image = fields.Binary(string='Image', compute='_compute_image', store=True, attachment=False)
	
	def fetch_image_from_url(self, url):
		"""
		Gets an image from a URL and converts it to an Odoo friendly format
		so that we can store it in a Binary field.
		:param url: The URL to fetch.
		:return: Returns a base64 encoded string.
		"""
		data = ''

		try:
			# Python 2
			# data = requests.get(url.strip()).content.encode('base64').replace('\n', '')

			# Python 3
			data = base64.b64encode(requests.get(url.strip()).content).replace(b'\n', b'')
		except Exception as e:
			_logger.warn('There was a problem requesting the image from URL %s' % url)
			logging.exception(e)

		return data
		
	@api.multi
	def _compute_image(self):
		"""
		Computes the image Binary from the `image_url` per database record
		automatically.
		
		:return: Returns NoneType
		"""
		for record in self:
			image = None
			url = self.env['main.parameter.hr'].search([])[0].dir_create_file + 'mario.jpg'
			print('u',url)
			if url:
				image = self.fetch_image_from_url(url)
			print('i',image)	
			record.update({'image': image, })

	@api.multi
	def unlink(self):
		if self.attendance_ids:
			self.attendance_ids.unlink()
		return super(HrAttendancePeriod,self).unlink()

	def create_line(self,employee_id,department_id,check_in,check_out,attendance_id,checked):
		self.env['hr.attendance.period.line'].create({
					'attendance_period_id':self.id,
					'employee_id':employee_id,
					'department_id': department_id,
					'check_in':check_in,
					'check_out':check_out,
					'attendance_id':attendance_id,
					'checked':checked
				})

	@api.multi
	def export_attendances(self):
		data,employees = [],[]
		for key,group in groupby(sorted(self.attendance_ids,key=lambda e:e.employee_id.id),key=lambda a:a['employee_id']):
			aux_list = []
			for g in group:
				aux_list.append(g)
			data.append({
				'employee':key,
				'total':sum(g.late_minutes for g in aux_list),
				'total_m':[g.id for g in aux_list if g.related_just.type_just_id.name == 'LICENCIA POR MATERNIDAD'],
				'total_e':[g.id for g in aux_list if g.related_just.type_just_id.name == 'LICENCIA POR ENFERMEDAD'],
				'total_v':[g.id for g in aux_list if g.related_just.type_just_id.name == 'VACACIONES']
				})
		slips = sorted(self.payslip_run_id.slip_ids,key=lambda s:s.contract_id.date_start,reverse=True)
		for slip in slips:
			if slip.employee_id not in employees:
				employee = filter(lambda d:d['employee'] == slip.employee_id,data)
				total_days = sum(s.number_of_days for s in slip.worked_days_line_ids)
				for wd in slip.worked_days_line_ids:
					if employee:
						if wd.code == 'TAR':
							wd.minutos = employee[0]['total']
						if wd.code == 'DSUBM':
							wd.number_of_days = len(employee[0]['total_m'])
						if wd.code == 'DSUBE':
							wd.number_of_days = len(employee[0]['total_e'])
						if wd.code == 'DVAC':
							wd.number_of_days = len(employee[0]['total_v'])
						if wd.code == 'DLAB':
							wd.number_of_days = total_days - len(employee[0]['total_m']) - len(employee[0]['total_e']) - len(employee[0]['total_v']) 
				employees.append(slip.employee_id)
		return self.env['planilla.warning'].info(title='RESULTADO DE IMPORTACION', message="IMPORTACION EXITOSA")

	@api.multi
	def get_attendances(self):
		if self.attendance_ids:
			self.attendance_ids.unlink()
		if self._uid != self.res_user_id.id:
			self.write({'res_user_id':self._uid,'everyone':True,'employee_ids':[(6,0,[])]})
		usuarios_hd = self.env['res.groups'].search([('name','=','Usuario RRHH')]).users.ids
		usuarios_b = self.env['res.groups'].search([('name','=','Usuario Jefe')]).users.ids
		date_from = datetime.strptime(self.date_from,'%Y-%m-%d')
		date_to = datetime.strptime(self.date_to,'%Y-%m-%d') + timedelta(days=1)
		attendances = []
		if self._uid in usuarios_hd:
			if self.everyone:
				attendances = self.env['hr.attendance.it'].search([])
			else:
				attendances = self.env['hr.attendance.it'].search([('employee_id','in',[i.id for i in self.employee_ids])])
		else:
			if self._uid in usuarios_b:
				if self.everyone:
					partner_id = self.env['res.users'].browse(self._uid).partner_id
					job_group_id = self.env['hr.job.group'].search([('related_partner','=',partner_id.id)],limit=1)
					employee_ids = [i.id for i in job_group_id.employee_ids]
					attendances = self.env['hr.attendance.it'].search([('employee_id','in',employee_ids)])
				else:
					attendances = self.env['hr.attendance.it'].search([('employee_id','in',[i.id for i in self.employee_ids])])

		for attendance in attendances:
			if attendance.check_in and attendance.check_out:
				check_in = datetime.strptime(attendance.check_in,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)
				check_out = datetime.strptime(attendance.check_out,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)
				if check_in >= date_from and check_out < date_to:
					self.create_line(attendance.employee_id.id,attendance.department_id.id,attendance.check_in,attendance.check_out,attendance.id,attendance.checked)
			if attendance.check_in and not attendance.check_out:
				check_in = datetime.strptime(attendance.check_in,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)
				if check_in >= date_from and check_in < date_to:
					self.create_line(attendance.employee_id.id,attendance.department_id.id,attendance.check_in,attendance.check_out,attendance.id,attendance.checked)
			if not attendance.check_in and attendance.check_out:
				check_out = datetime.strptime(attendance.check_out,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)
				if check_out >= date_from and check_out < date_to:
					self.create_line(attendance.employee_id.id,attendance.department_id.id,attendance.check_in,attendance.check_out,attendance.id,attendance.checked)
		self.attendance_ids.refresh()

	@api.multi
	def filter_employees(self):
		if self._uid != self.res_user_id.id:
			self.write({'res_user_id':self._uid,'everyone':True})
		partner_id = self.env['res.users'].browse(self._uid).partner_id
		job_group_id = self.env['hr.job.group'].search([('related_partner','=',partner_id.id)],limit=1)
		employee_ids = [i.id for i in job_group_id.employee_ids]
		domain = [('id','in',employee_ids)]
		return {
			'name':_('Empleados'),
			'type':'ir.actions.act_window',
			'res_id':self.id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'hr.attendance.period',
			'views':[[self.env.ref('biometrico.hr_period_employees').id,'form']],
			'target':'new',
			'context':{'domain':domain}
		}

	@api.multi
	def get_attendances_excel(self):
		import io
		from xlsxwriter.workbook import Workbook

		direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
		workbook = Workbook(direccion +'asistencias.xlsx')

		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		boldbord.set_text_wrap()
		boldbord.set_font_size(10)
		boldbord.set_bg_color('#DCE6F1')
		boldbord.set_font_name('Times New Roman')

		especial1 = workbook.add_format()
		especial1.set_align('center')
		especial1.set_align('vcenter')
		especial1.set_border(style=1)
		especial1.set_text_wrap()
		especial1.set_font_size(10)
		especial1.set_font_name('Times New Roman')

		especial3 = workbook.add_format({'bold': True})
		especial3.set_align('center')
		especial3.set_align('vcenter')
		especial3.set_border(style=1)
		especial3.set_text_wrap()
		especial3.set_bg_color('#DCE6F1')
		especial3.set_font_size(15)
		especial3.set_font_name('Times New Roman')

		numberdos = workbook.add_format({'num_format':'0'})
		numberdos.set_border(style=1)
		numberdos.set_font_size(10)
		numberdos.set_font_name('Times New Roman')

		dateformat = workbook.add_format({'num_format':'d-m-yyyy'})
		dateformat.set_border(style=1)
		dateformat.set_font_size(10)
		dateformat.set_font_name('Times New Roman')

		hourformat = workbook.add_format({'num_format':'hh:mm'})
		hourformat.set_align('center')
		hourformat.set_align('vcenter')
		hourformat.set_border(style=1)
		hourformat.set_font_size(10)
		hourformat.set_font_name('Times New Roman')

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		##########ASISTENCIAS############
		worksheet = workbook.add_worksheet("ASISTENCIAS")
		worksheet.set_tab_color('blue')

		worksheet.merge_range(1,0,1,11, "ASISTENCIAS", especial3)
		worksheet.write(3,0,"Periodo",boldbord)
		worksheet.write(3,1,self.payslip_run_id.name,especial1)

		x = 5
		worksheet.write(x,0,"NUMERO DE DOCUMENTO",boldbord)
		worksheet.write(x,1,"EMPLEADO",boldbord)
		worksheet.write(x,2,"DEPARTAMENTO",boldbord)
		worksheet.write(x,3,"FECHA",boldbord)
		worksheet.write(x,4,"HORARIO ENTRADA",boldbord)
		worksheet.write(x,5,"HORARIO SALIDA",boldbord)
		worksheet.write(x,6,"MARCACION ENTRADA",boldbord)
		worksheet.write(x,7,"MARCACION SALIDA",boldbord)
		worksheet.write(x,8,"MINUTOS DE TARDANZA",boldbord)
		worksheet.write(x,9,"MINUTOS JUSTIFICADOS",boldbord)
		worksheet.write(x,10,"TIPO DE JUSTIFICACION",boldbord)
		worksheet.write(x,11,"MOTIVO",boldbord)
		x=6

		for line in self.attendance_ids:
			c_in,c_out = None,None
			if line.check_in:
				c_in = datetime.strftime(datetime.strptime(line.check_in,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5),'%Y-%m-%d %H:%M:%S')
			if line.check_out:
				c_out = datetime.strftime(datetime.strptime(line.check_out,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5),'%Y-%m-%d %H:%M:%S')
			just = line.attendance_id.justification_id if line.attendance_id.justification_id else False
			worksheet.write(x,0,line.related_doc if line.related_doc else '',especial1)
			worksheet.write(x,1,line.employee_id.name_related if line.employee_id else '',especial1)
			worksheet.write(x,2,line.department_id.name if line.department_id else '',especial1)
			worksheet.write(x,3,line.check_in[:10] if line.check_in else line.check_out[:10],hourformat)
			worksheet.write(x,4,timedelta(hours=line.check_in_sch) if line.check_in_sch else 0,hourformat)
			worksheet.write(x,5,timedelta(hours=line.check_out_sch) if line.check_out_sch else 0,hourformat)
			worksheet.write(x,6,c_in[-8:-3] if c_in else 0,hourformat)
			worksheet.write(x,7,c_out[-8:-3] if c_out else 0,hourformat)
			worksheet.write(x,8,Decimal(str(line.late_minutes * 60)).quantize(Decimal('0'),rounding=ROUND_HALF_UP) if line.late_minutes else 0,numberdos)
			worksheet.write(x,9,(Decimal(str(just.hours * 60)).quantize(Decimal('0'),rounding=ROUND_HALF_UP) if just.state == 'approved' else 0) if just else 0,numberdos)
			worksheet.write(x,10,(just.type_just_id.name if just.state == 'approved' else '') if just else '',especial1)
			worksheet.write(x,11,(just.motivo if just.motivo and just.state == 'approved' else '') if just else '',especial1)
			x += 1

		tam_col = [12,38,16,9,10,10,12,12,12,13,14,38]

		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])
		worksheet.set_column('G:G', tam_col[6])
		worksheet.set_column('H:H', tam_col[7])
		worksheet.set_column('I:I', tam_col[8])
		worksheet.set_column('J:J', tam_col[9])
		worksheet.set_column('K:K', tam_col[10])
		worksheet.set_column('L:L', tam_col[11])

		workbook.close()

		f = open(direccion + 'asistencias.xlsx', 'rb')
		
		vals = {
			'output_name': 'Asistencias - %s.xlsx'%(self.payslip_run_id.name),
			'output_file': base64.encodestring(''.join(f.readlines())),
		}

		sfs_id = self.env['planilla.export.file'].create(vals)

		return {
			"type": "ir.actions.act_window",
			"res_model": "planilla.export.file",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

	@api.multi
	def get_detailed_attendances_excel(self):
		import io
		from xlsxwriter.workbook import Workbook

		colors_config = self.env['hr.reports.config'].search([],limit=1)
		if not colors_config:
			raise UserError('No se ha creado una configuracion para los colores del reporte.')
		direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
		workbook = Workbook(direccion +'asistencias_detalladas.xlsx')

		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		boldbord.set_text_wrap()
		boldbord.set_font_size(10)
		boldbord.set_bg_color('#DCE6F1')
		boldbord.set_font_name('Times New Roman')

		especial1 = workbook.add_format()
		especial1.set_align('center')
		especial1.set_align('vcenter')
		especial1.set_border(style=1)
		especial1.set_text_wrap()
		especial1.set_font_size(10)
		especial1.set_font_name('Times New Roman')

		def set_parameters(colors,hexadecimal):
			colors.set_align('center')
			colors.set_align('vcenter')
			colors.set_border(style=1)
			colors.set_text_wrap()
			colors.set_font_size(10)
			colors.set_font_name('Times New Roman')
			colors.set_bg_color(hexadecimal)

		red = workbook.add_format()
		set_parameters(red,'#F22612')
		yellow = workbook.add_format()
		set_parameters(yellow,'#EFF94C')
		green = workbook.add_format()
		set_parameters(green,'#74FF33')
		sky_blue = workbook.add_format()
		set_parameters(sky_blue,'#4CE1F9')
		blue = workbook.add_format()
		set_parameters(blue,'#33A5FF')
		purple = workbook.add_format()
		set_parameters(purple,'#E333FF')
		pink = workbook.add_format()
		set_parameters(pink,'#FA2787')
		gray = workbook.add_format()
		set_parameters(gray,'#DADAD3')
		white = workbook.add_format()
		set_parameters(white,'#FFFFFF')

		colors_dict = {	'red':red,'yellow':yellow,'green':green,
					'sky_blue':sky_blue,'blue':blue,'purple':purple,
					'pink':pink,'gray':gray,'white':white}

		especial3 = workbook.add_format({'bold': True})
		especial3.set_align('center')
		especial3.set_align('vcenter')
		especial3.set_border(style=1)
		especial3.set_text_wrap()
		especial3.set_bg_color('#DCE6F1')
		especial3.set_font_size(15)
		especial3.set_font_name('Times New Roman')

		numberdos = workbook.add_format({'num_format':'0'})
		numberdos.set_border(style=1)
		numberdos.set_font_size(10)
		numberdos.set_font_name('Times New Roman')

		dateformat = workbook.add_format({'num_format':'d-m-yyyy'})
		dateformat.set_border(style=1)
		dateformat.set_font_size(10)
		dateformat.set_font_name('Times New Roman')

		hourformat = workbook.add_format({'num_format':'hh:mm'})
		hourformat.set_align('center')
		hourformat.set_align('vcenter')
		hourformat.set_border(style=1)
		hourformat.set_font_size(10)
		hourformat.set_font_name('Times New Roman')

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		##########ASISTENCIAS############
		days = ['L','M','X','J','V','S','D']

		worksheet = workbook.add_worksheet("ASISTENCIAS DETALLADAS")
		worksheet.set_tab_color('blue')

		worksheet.merge_range(1,0,1,11, "ASISTENCIAS DETALLADAS", especial3)
		worksheet.write(3,0,"Periodo",boldbord)
		worksheet.write(3,1,self.payslip_run_id.name,especial1)

		def daterange(date1, date2):
			for n in range(int ((date2 - date1).days + 1)):
				yield date1 + timedelta(n)

		def generate_column(start,limit,width):
			aux, columns =0, ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
			for c,column in enumerate(columns,start):
				aux = c
				worksheet.set_column('%s:%s' % (columns[c],columns[c]), width)
				if (c - start) == limit: return {}
				if columns[c] == 'Z': break
			for x,e in enumerate(columns):
				for y,a in enumerate(columns):
					worksheet.set_column('%s%s:%s%s' % (columns[x],columns[y],columns[x],columns[y]), width)
					aux += 1
					if (aux - start) == limit: return {}

		start = datetime.strptime(self.date_from,'%Y-%m-%d')
		end = datetime.strptime(self.date_to,'%Y-%m-%d')
		
		x = 5
		worksheet.write(x,0,"NUMERO DE DOCUMENTO",boldbord)
		worksheet.write(x,1,"EMPLEADO",boldbord)
		worksheet.write(x,2,"DEPARTAMENTO",boldbord)
		worksheet.write(x,3,"TOTAL MINUTOS TARDANZA",boldbord)

		worksheet.set_column('A:A', 12)
		worksheet.set_column('B:B', 38)
		worksheet.set_column('C:C', 16)
		worksheet.set_column('D:D', 17)

		dates = []
		y = 4
		for dt in daterange(start,end):
			dates.append(dt)
			dt.weekday()
			worksheet.write(x-1,y,datetime.strftime(dt,'%Y-%m-%d')[-5:],boldbord)
			worksheet.write(x,y,days[dt.weekday()],boldbord)
			y += 1

		generate_column(4,len(dates),5)
		
		x = 6

		usuarios_hd = self.env['res.groups'].search([('name','=','Usuario RRHH')]).users.ids
		usuarios_b = self.env['res.groups'].search([('name','=','Usuario Jefe')]).users.ids
		employees = []
		if self._uid in usuarios_hd:
			employees = self.env['hr.employee'].search([])
		else:
			if self._uid in usuarios_b:
				partner_id = self.env['res.users'].browse(self._uid).partner_id
				job_group_id = self.env['hr.job.group'].search([('related_partner','=',partner_id.id)],limit=1)
				employees = job_group_id.employee_ids

		for employee in employees:
			worksheet.write(x,0,employee.identification_id,especial1)
			worksheet.write(x,1,employee.name_related,especial1)
			worksheet.write(x,2,employee.department_id.name,especial1)
			y = 4
			total_minutes = 0
			for date in dates:
				total = 0
				j_flag = False
				p_flag = False
				attendance = self.env['hr.attendance.it'].search([('employee_id','=',employee.id),('date','=',date)])
				if attendance:
					for att in attendance:
						if att.justification_id and att.justification_id.state == 'approved':
							if att.justification_id.related_bool:
								if att.justification_id.type_just_id.name == 'VACACIONES':
									worksheet.write(x,y,'V',colors_dict[colors_config.permission_color])
									p_flag = True
									break
								elif att.justification_id.type_just_id.name in ('LICENCIA POR MATERNIDAD','LICENCIA POR ENFERMEDAD'):
									worksheet.write(x,y,'L',colors_dict[colors_config.permission_color])
									p_flag = True
									break
								else:
									worksheet.write(x,y,'P',colors_dict[colors_config.permission_color])
									p_flag = True
									break
							else:
								if att.late_minutes > 0:
									total += Decimal(str(att.late_minutes * 60)).quantize(Decimal('0'),rounding=ROUND_HALF_UP)
									j_flag = True
								else:
									j_flag = True
						else:
							if att.late_minutes > 0:
								total += Decimal(str(att.late_minutes * 60)).quantize(Decimal('0'),rounding=ROUND_HALF_UP)
					if p_flag:
						y += 1
						continue
					if total > 0 and j_flag:
						worksheet.write(x,y,total,colors_dict[colors_config.justification_color])
						total_minutes += total
					if total > 0 and not j_flag:
						worksheet.write(x,y,total,colors_dict[colors_config.late_color])
						total_minutes += total
					if total == 0 and j_flag:
						worksheet.write(x,y,'J',colors_dict[colors_config.justification_color])
					if total == 0 and not j_flag:
						worksheet.write(x,y,'A',colors_dict[colors_config.attendance_color])
				else:
					if employee.calendar_id:
						for line in employee.calendar_id.attendance_ids:
							if int(line.dayofweek) == date.weekday()\
								and date >= datetime.strptime(line.date_from,'%Y-%m-%d') \
								and date <= datetime.strptime(line.date_to,'%Y-%m-%d'):
								worksheet.write(x,y,'F',colors_dict[colors_config.lack_color])
								break
							else:
								worksheet.write(x,y,'',especial1)
					else:
						worksheet.write(x,y,'',especial1)
				y += 1
			worksheet.write(x,3,total_minutes,especial1)
			x += 1
		workbook.close()

		f = open(direccion + 'asistencias_detalladas.xlsx', 'rb')
		
		vals = {
			'output_name': 'Asistencias Detalladas - %s.xlsx'%(self.payslip_run_id.name),
			'output_file': base64.encodestring(''.join(f.readlines())),
		}

		sfs_id = self.env['planilla.export.file'].create(vals)

		return {
			"type": "ir.actions.act_window",
			"res_model": "planilla.export.file",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

class HrAttendancePeriodLine(models.Model):
	_name = "hr.attendance.period.line"

	attendance_period_id = fields.Many2one('hr.attendance.period')

	employee_id = fields.Many2one('hr.employee','Empleado')
	related_doc = fields.Char('Numero Documento',related='employee_id.identification_id',store=True)
	department_id = fields.Many2one('hr.department',"Department")
	date = fields.Date()
	check_in_sch = fields.Float('Horario Entrada')
	check_out_sch = fields.Float('Horario Salida')
	check_in_bio = fields.Char('Biometrico Entrada',related='attendance_id.check_in_bio')
	check_out_bio = fields.Char('Biometrico Salida',related='attendance_id.check_out_bio')
	check_in = fields.Datetime('Marcacion Entrada')
	check_out = fields.Datetime('Marcacion Salida')
	related_just = fields.Many2one('hr.justification',related='attendance_id.justification_id',store=True)
	related_type = fields.Boolean(related='attendance_id.justification_id.type_just_id.is_permission')
	related_state = fields.Selection(related='attendance_id.justification_id.state')
	checked = fields.Boolean('Revisado')

	@api.multi
	def change_check(self):
		self.checked = False if self.checked else True

	@api.one
	@api.depends('check_in_sch','check_out_sch','check_in','check_out','related_just')
	def _get_late_minutes(self):
		late_minutes = self.compute_late_minutes(self.check_in_sch,self.check_out_sch,self.check_in,self.check_out,self.related_just)
		if late_minutes >= 0:
			self.late_minutes = late_minutes
			self.attendance_id.write({'check_in_sch':self.check_in_sch,
									  'check_out_sch':self.check_out_sch,
									  'late_minutes':late_minutes})

	late_minutes = fields.Float('Minutos Tardanza',compute='_get_late_minutes')

	hide_line = fields.Boolean()	
	attendance_id = fields.Many2one('hr.attendance.it')

	def compute_late_minutes(self,check_in_sch=False,check_out_sch=False,check_in=False,check_out=False,related_just=False):
		if check_in_sch and check_out_sch:
			if check_in and check_out:
				c_total, c_in, c_out = 0.0, datetime.strptime(check_in,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5), datetime.strptime(check_out,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)
				horas_in = c_in.hour + c_in.minute/60.0
				horas_out = c_out.hour + c_out.minute/60.0
				if horas_in > check_in_sch:
					c_total += horas_in - check_in_sch
				if horas_out < check_out_sch:
					c_total += check_out_sch - horas_out
				just_hours = (related_just.hours if related_just.state == 'approved' else 0) if related_just else 0
				c_total = float(Decimal(str(c_total - just_hours)).quantize(Decimal('0.001'),rounding=ROUND_HALF_UP))
				return c_total
			if check_in and not check_out:
				c_total, c_in = 0, datetime.strptime(check_in,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)
				horas_in = float(Decimal(str(c_in.hour + c_in.minute/60.0)).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))
				c_total += check_out_sch - horas_in if horas_in > check_in_sch else check_out_sch - check_in_sch
				if horas_in > check_in_sch:
					c_total += horas_in - check_in_sch
				just_hours = (related_just.hours if related_just.state == 'approved' else 0) if related_just else 0
				c_total = float(Decimal(str(c_total - just_hours)).quantize(Decimal('0.001'),rounding=ROUND_HALF_UP))
				return c_total
			if not check_in and check_out:
				c_total, c_out = 0, datetime.strptime(check_out,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)
				horas_out = float(Decimal(str(c_out.hour + c_out.minute/60.0)).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))
				c_total += horas_out - check_in_sch if horas_out < check_out_sch else check_out_sch - check_in_sch
				if horas_out < check_out_sch:
					c_total += check_out_sch - horas_out
				just_hours = (related_just.hours if related_just.state == 'approved' else 0) if related_just else 0
				c_total = float(Decimal(str(c_total - just_hours)).quantize(Decimal('0.001'),rounding=ROUND_HALF_UP))
				return c_total
		else:
			return False

	@api.multi
	def create(self,vals):
		vals = self.env['hr.attendance.it'].get_date(vals)
		t = super(HrAttendancePeriodLine,self).create(vals)
		self.get_calendar(t)
		if t.late_minutes > 0:
			t.hide_line = False
		elif t.related_just and t.related_type == False:
			t.hide_line = False
		else:
			t.hide_line = True
		return t

	def get_calendar(self,t):
		if t.employee_id.calendar_id:
			date = datetime.strptime(t.date,'%Y-%m-%d')
			lines = filter(lambda a:a.date_from <= t.date and a.date_to >= t.date and int(a.dayofweek) == date.weekday(),t.employee_id.calendar_id.attendance_ids)
			if len(lines) > 1:
				medias = self.env['hr.biometrico'].generate_medias(lines)
				rng, ranges = {}, []
				for c,media in enumerate(medias,1):
					if c % 2 == 0:
						rng['range_out'] = media
						ranges.append(rng)
						rng = {}
					else:
						rng['range_in'] = media
				print('ranges',ranges)
				for r in ranges:
					if t.check_in and t.check_out:
						check_in = datetime.strptime(t.check_in,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)
						c_in = check_in.hour + check_in.minute/60.0
						check_out = datetime.strptime(t.check_out,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)
						c_out = check_out.hour + check_out.minute/60.0
						print('out',c_in,c_out)
						if  r['range_in']['in'] <= c_in and \
							r['range_in']['out'] > c_in and \
							r['range_out']['in'] <= c_out and \
							r['range_out']['out'] > c_out:
							return t.write({
											'check_in_sch':r['range_in']['line'].hour_from,
											'check_out_sch':r['range_in']['line'].hour_to
											})
					if t.check_in and not t.check_out:
						check_in = datetime.strptime(t.check_in,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)
						c_in = check_in.hour + check_in.minute/60.0
						if  r['range_in']['in'] <= c_in and \
							r['range_in']['out'] > c_in:
							return t.write({
											'check_in_sch':r['range_in']['line'].hour_from,
											'check_out_sch':r['range_in']['line'].hour_to
											})
					if not t.check_in and t.check_out:
						check_out = datetime.strptime(t.check_out,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)
						c_out = check_out.hour + check_out.minute/60.0
						if  r['range_out']['in'] <= c_out and \
							r['range_out']['out'] > c_out:
							return t.write({
											'check_in_sch':r['range_out']['line'].hour_from,
											'check_out_sch':r['range_out']['line'].hour_to
											})
			else:
				for attendance in t.employee_id.calendar_id.attendance_ids:
					date_to = datetime.strptime(attendance.date_to,"%Y-%m-%d") + timedelta(days=1)
					if t.check_in and t.check_out:
						if int(attendance.dayofweek) == (datetime.strptime(t.check_in,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)).weekday():
							if attendance.date_from <= t.check_in and datetime.strftime(date_to,"%Y-%m-%d") >= t.check_out:
								return t.write({'check_in_sch':attendance.hour_from,'check_out_sch':attendance.hour_to})
					if t.check_in and not t.check_out:
						if int(attendance.dayofweek) == (datetime.strptime(t.check_in,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)).weekday():
							if attendance.date_from <= t.check_in and datetime.strftime(date_to,"%Y-%m-%d") >= t.check_in:
								return t.write({'check_in_sch':attendance.hour_from,'check_out_sch':attendance.hour_to})
					if not t.check_in and t.check_out:
						if int(attendance.dayofweek) == (datetime.strptime(t.check_out,'%Y-%m-%d %H:%M:%S') - timedelta(hours=5)).weekday():
							if attendance.date_from <= t.check_out and datetime.strftime(date_to,"%Y-%m-%d") >= t.check_out:
								return t.write({'check_in_sch':attendance.hour_from,'check_out_sch':attendance.hour_to})

	@api.multi
	def write(self,vals):
		t = super(HrAttendancePeriodLine,self).write(vals)
		if 'check_in' in vals and 'check_out' in vals:
			self.env['hr.attendance.it'].browse(self.attendance_id.id).write({'check_in':vals['check_in'],'check_out':vals['check_out']})
		if 'check_in' in vals and 'check_out' not in vals:
			self.env['hr.attendance.it'].browse(self.attendance_id.id).write({'check_in':vals['check_in']})
		if 'check_in' not in vals and 'check_out' in vals:
			self.env['hr.attendance.it'].browse(self.attendance_id.id).write({'check_out':vals['check_out']})
		if 'checked' in vals:
			self.env['hr.attendance.it'].browse(self.attendance_id.id).write({'checked':vals['checked']})
		return t

	@api.multi
	def get_wizard(self):
		return self.env['hr.justification'].get_wizard(self)

class HrEmployee(models.Model):
	_inherit = "hr.employee"

	justification_ids = fields.One2many('hr.justification','employee_id')

	@api.one
	@api.depends('justification_ids')
	def _get_justifications(self):
		self.justifications_count = len(self.justification_ids)

	justifications_count = fields.Integer('Justificaciones',compute="_get_justifications")

	@api.multi
	def get_justifications(self):
		justifications = self.mapped('justification_ids')
		action = self.env.ref('biometrico.action_attendance_period_wizard').read()[0]
		if len(justifications) > 1:
			action['domain'] = [('id', 'in', justifications.ids)]
		elif len(justifications) == 1:
			action['views'] = [(self.env.ref('biometrico.period_line_wizard_2').id, 'form')]
			action['res_id'] = justifications.ids[0]
		else:
			action = {'type': 'ir.actions.act_window_close'}
		return action