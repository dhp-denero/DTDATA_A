# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from copy import copy
import babel
import base64

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

class HrControlVacaciones(models.Model):

	_name = 'hr.control.vacaciones'

	name = fields.Char("Nombre")
	state = fields.Selection([('generated','Generada'),('closed','Cerrada')],'Estado',default='generated')
	vacaciones_line = fields.One2many('hr.control.vacaciones.line','control_vacaciones_id','Detalle Vacaciones')

	@api.model
	def create(self,vals):
		if len(self.env['hr.control.vacaciones'].search([])) > 0:
			raise UserError('No se puede crear mas de un Control de Vacaciones')
		else:
			return super(HrControlVacaciones,self).create(vals)

	@api.one
	def cerrar(self):
		self.state = 'closed'

	@api.one
	def reabrir(self):
		self.state = 'generated'

	@api.multi
	def unlink(self):
		for i in self.ids:
			self.env['hr.control.vacaciones.line'].search([('control_vacaciones_id','=',i)]).unlink()
		return super(HrControlVacaciones,self).unlink()

	@api.multi
	def calcular_vacaciones(self):
		if self.vacaciones_line:
			self.vacaciones_line.unlink()
		employees = self.env['hr.employee'].search([('id','!=','1')])
		for employee in employees:
			saldo, aux_year = 30, 0
			devengues = self.env['hr.devengue'].search([('employee_id','=',employee.id)])
			devengues = devengues.sorted(key=lambda devengue:devengue.periodo_devengue.date_start)
			for devengue in devengues:
				try:
					year = self.env['account.fiscalyear'].search([('name','=',str(datetime.strptime(devengue.periodo_devengue.date_start,'%Y-%m-%d').year))],limit=1)
					if year != aux_year:
						saldo = 30
					aux_year = year
					if devengue.dias > 0:
						self.env['hr.control.vacaciones.line'].create({
							'fiscalyear_id':year.id,
							'dni':employee.identification_id,
							'employee_id':employee.id,
							'periodo_planilla':devengue.slip_id.payslip_run_id.id,
							'periodo_devengue':devengue.periodo_devengue.id,
							'saldo_vacaciones':saldo,
							'dias_gozados': devengue.dias,
							'total':saldo - devengue.dias,
							'control_vacaciones_id':self.id
						})
						saldo = saldo - devengue.dias
				except:
					pass
			if saldo == 30:
				self.env['hr.control.vacaciones.line'].create({
						'fiscalyear_id':0,
						'dni':employee.identification_id,
						'employee_id':employee.id,
						'periodo_planilla':0,
						'periodo_devengue':0,
						'saldo_vacaciones':saldo,
						'dias_gozados':0,
						'total':saldo,
						'control_vacaciones_id':self.id
					})
		return self.env['planilla.warning'].info(title='Resultado', message="Se actualizo correctamente")

	@api.multi
	def get_vacaciones_excel(self):
		import io
		from xlsxwriter.workbook import Workbook

		try:
			direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		workbook = Workbook(direccion +'control_vacaciones.xlsx')
		worksheet = workbook.add_worksheet("Vacaciones")
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

		numberdos = workbook.add_format({'num_format':'0.00'})
		numberdos.set_border(style=1)
		numberdos.set_font_size(10)
		numberdos.set_font_name('Times New Roman')
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		worksheet.merge_range(1,0,1,7, "CONTROL DE VACACIONES", especial3)

		worksheet.write(4,0,u"AÑO",boldbord)
		worksheet.write(4,1,"DNI",boldbord)
		worksheet.write(4,2,"APELLIDOS Y NOMBRES",boldbord)
		worksheet.write(4,3,"PERIODO PLANILLA",boldbord)
		worksheet.write(4,4,"PERIODO DEVENGUE",boldbord)
		worksheet.write(4,5,"SALDO VACACIONES",boldbord)
		worksheet.write(4,6,"DIAS GOZADOS",boldbord)
		worksheet.write(4,7,"TOTAL",boldbord)

		x=5

		for line in self.vacaciones_line:
			worksheet.write(x,0,line.fiscalyear_id.name if line.fiscalyear_id else '',especial1)
			worksheet.write(x,1,line.dni if line.dni else '',especial1)
			worksheet.write(x,2,(line.employee_id.a_paterno if line.employee_id.a_paterno else '')+' '+(line.employee_id.a_materno if line.employee_id.a_materno else '')+' '+(line.employee_id.nombres if line.employee_id.a_paterno else ''),especial1)
			worksheet.write(x,3,line.periodo_planilla.name if line.periodo_planilla else '',especial1)
			worksheet.write(x,4,line.periodo_devengue.name if line.periodo_devengue else '',especial1)
			worksheet.write(x,5,line.saldo_vacaciones if line.saldo_vacaciones else 0,numberdos)
			worksheet.write(x,6,line.dias_gozados if line.dias_gozados else 0,numberdos)
			worksheet.write(x,7,line.total if line.total else 0,numberdos)
			x += 1

		tam_col = [5,10,38,13,13,13,11,11]

		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])
		worksheet.set_column('G:G', tam_col[6])
		worksheet.set_column('H:H', tam_col[7])

		workbook.close()

		f = open(direccion + 'control_vacaciones.xlsx', 'rb')

		vals = {
			'output_name': 'Control_Vacaciones.xlsx',
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

class HrControlVacacionesLine(models.Model):
	_name = 'hr.control.vacaciones.line'

	dni = fields.Char('DNI')
	employee_id = fields.Many2one('hr.employee','Apellidos y Nombres')
	periodo_planilla = fields.Many2one('hr.payslip.run','Periodo Planilla')
	periodo_devengue = fields.Many2one('hr.payslip.run','Periodo Devengue')
	dias_gozados = fields.Integer('Dias Gozados')
	saldo_vacaciones = fields.Integer('Saldo Vacaciones')
	total = fields.Integer('Total')
	control_vacaciones_id = fields.Many2one('hr.control.vacaciones')
	fiscalyear_id = fields.Many2one('account.fiscalyear',u'Año')

class HrUltimaVacacion(models.Model):
	_name = 'hr.ultima.vacacion'

	ultima_vacacion = fields.Date('Fecha Ultima Vacacion',default=datetime.now())
	employee_ids = fields.One2many('hr.employee','ultima_vacacion_id')

	@api.model
	def get_wizard(self,ids):
		return {
			'name':_('Asignar Ultima Vacacion'),
			'res_id':self.id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'hr.ultima.vacacion',
			'views':[[self.env.ref('planilla.view_ultima_vacacion_wizard_form').id,'form']],
			'type':'ir.actions.act_window',
			'target':'new',
			'context':{
					'default_employee_ids':[(6,0,ids)]
				}
			}

	@api.multi
	def set_date(self):
		return [i.write({'fecha_vacacion':self.ultima_vacacion}) for i in self.employee_ids]

class HrRolVacaciones(models.Model):
	_name = 'hr.rol.vacaciones'

	name = fields.Char('Nombre')
	fiscalyear_id = fields.Many2one('account.fiscalyear',u'Año Fiscal')
	rol_line = fields.One2many('hr.rol.vacaciones.line','rol_id')

	@api.model
	def create(self,vals):
		if vals['fiscalyear_id'] not in [rol.fiscalyear_id.id for rol in self.env['hr.rol.vacaciones'].search([])]:
			return super(HrRolVacaciones,self).create(vals)
		else:
			raise UserError('No puede existir dos procesos de vacaciones con el mismo año fiscal')

	@api.multi
	def unlink(self):
		for i in self.ids:
			self.env['hr.rol.vacaciones.line'].search([('rol_id','=',i)]).unlink()
		return super(HrRolVacaciones,self).unlink()

	def is_leap(self, year):
		if year % 4 == 0 and year % 100 == 0 and year % 400 == 0:
			return True
		else:
			return False

	def get_employee_last_vacation(self,employees,year,lines=False):
		for employee in employees:
			worked_days = 0
			faltas = 0
			dates = [i.date_start for i in employee.contract_ids if i.situacion_id.codigo == '1']
			if len(dates) > 0:
				fecha_ing = min(dates)
				jornada = employee.contract_id.jornada
				if lines:
					for i in lines:
						if employee.id == i.employee_id.id:
							fecha_ult_vac = i.fecha_real
				else:
					fecha_ult_vac = employee.fecha_vacacion if employee.fecha_vacacion else False
				payslips = self.env['hr.payslip'].search([('employee_id','=',employee.id)])
				days_ult = 366 if self.is_leap(datetime.strptime(fecha_ult_vac,'%Y-%m-%d').year) else 365
				days_ing = 366 if self.is_leap(datetime.strptime(fecha_ing,'%Y-%m-%d').year) else 365
				aux = datetime.strptime(fecha_ult_vac,'%Y-%m-%d') if fecha_ult_vac else datetime.strptime(fecha_ing,'%Y-%m-%d')
				payslips = filter(lambda payslip:datetime.strptime(payslip.date_to,'%Y-%m-%d') >= aux and datetime.strptime(payslip.date_from,'%Y-%m-%d') < aux+timedelta(days=days_ult) ,payslips)
				for payslip in payslips:
					worked_days += self.env['hr.payslip.worked_days'].search([('payslip_id','=',payslip.id),('code','=','DLAB')]).number_of_days
					worked_days += self.env['hr.payslip.worked_days'].search([('payslip_id','=',payslip.id),('code','=','DVAC')]).number_of_days
					faltas += self.env['hr.payslip.worked_days'].search([('payslip_id','=',payslip.id),('name','=','FALTAS')]).number_of_days
				dias_efect = worked_days

				if employee.fecha_vacacion or lines:
					if jornada == 'six':
						fecha_vac = datetime.strptime(fecha_ult_vac,'%Y-%m-%d') + timedelta(days=days_ult) if dias_efect >= 260 else datetime.strptime(fecha_ult_vac,'%Y-%m-%d') + timedelta(days=days_ult + (260 - dias_efect))
					else:
						fecha_vac = datetime.strptime(fecha_ult_vac,'%Y-%m-%d') + timedelta(days=days_ult) if dias_efect >= 210 else datetime.strptime(fecha_ult_vac,'%Y-%m-%d') + timedelta(days=days_ult + (210 - dias_efect))
				else:
					if jornada == 'six':
						fecha_vac = datetime.strptime(fecha_ing,'%Y-%m-%d') + timedelta(days=days_ing) if dias_efect >= 260 else datetime.strptime(fecha_ing,'%Y-%m-%d') + timedelta(days=days_ing + (260 - dias_efect))
					else:
						fecha_vac = datetime.strptime(fecha_ing,'%Y-%m-%d') + timedelta(days=days_ing) if dias_efect >= 210 else datetime.strptime(fecha_ing,'%Y-%m-%d') + timedelta(days=days_ing + (210 - dias_efect))
				aux_dias_efect = copy(dias_efect)
				self.env['hr.rol.vacaciones.line'].create({
						'rol_id':self.id,
						'fiscalyear_id':self.fiscalyear_id.id,
						'employee_id':employee.id,
						'jornada':6 if jornada == 'six' else 5,
						'fecha_ing':fecha_ing,
						'fecha_ult_vac':fecha_ult_vac,
						'fecha_vac':fecha_vac,
						'faltas':faltas,
						'dias_efect':dias_efect,
						'aux_dias_efect':aux_dias_efect,
						'fecha_real':fecha_vac if fecha_vac.year == year else False
					})
			else:
				raise UserError('El empleado '+str(employee.name_related)+' no tiene contratos vigentes')

	@api.multi
	def calcular_rol_vacaciones(self):
		if self.rol_line:
			self.env['hr.rol.vacaciones.line'].search([('rol_id','=',self.id)]).unlink()
		employees = self.env['hr.employee'].search([])
		for employee in employees:
			dates = [i.date_start for i in employee.contract_ids if i.situacion_id.codigo == '1']
			if len(dates) > 0:
				fecha_ing = min(dates)
				self.env['hr.rol.vacaciones.line'].create({
					'rol_id':self.id,
					'employee_id':employee.id,
					'fecha_ing':fecha_ing,
					'fecha_ult_vac':fecha_ing
				})

		return self.env['planilla.warning'].info(title='Resultado', message="Se genero de manera correcta")
		"""
		year, roles, old_employees, rol = datetime.strptime(self.fiscalyear_id.name,'%Y').year, self.env['hr.rol.vacaciones'].search([]), [], False
		if filter(lambda rol:datetime.strptime(rol.fiscalyear_id.name,'%Y').year<year,roles):
			past_year = datetime.strptime(self.fiscalyear_id.name,'%Y') - relativedelta(years=1)
			past_year = self.env['account.fiscalyear'].search([('name','=',past_year.year)])
			rol = self.env['hr.rol.vacaciones'].search([('fiscalyear_id','=',past_year.id)])
		if rol:
			old_employees = [line.employee_id for line in rol.rol_line if line.fecha_real]
		if self.rol_line:
			self.env['hr.rol.vacaciones.line'].search([('rol_id','=',self.id)]).unlink()
		employees = self.env['hr.employee'].search([('id','!=',1)])
		employees = [i for i in employees]
		aux_employees = copy(employees)
		if len(old_employees) > 0:
			for employee in employees:
				if employee in old_employees:
					aux_employees.remove(employee)
			self.get_employee_last_vacation(old_employees,year,rol.rol_line)
		self.get_employee_last_vacation(aux_employees,year)
		"""

	@api.multi
	def actualizar_dias_laborados(self):
		employees = self.env['hr.employee'].search([('id','!=',1)])
		for employee in employees:
			worked_days = 0
			faltas = 0
			dates = [i.date_start for i in employee.contract_ids if i.situacion_id.codigo == '1']
			if len(dates) > 0:
				fecha_ing = min(dates)
				jornada = employee.contract_id.jornada
				fecha_ult_vac = employee.fecha_vacacion if employee.fecha_vacacion else False
				days_ult = 366 if self.is_leap(datetime.strptime(fecha_ult_vac,'%Y-%m-%d').year) else 365
				days_ing = 366 if self.is_leap(datetime.strptime(fecha_ing,'%Y-%m-%d').year) else 365
				payslips = self.env['hr.payslip'].search([('employee_id','=',employee.id)])
				aux = datetime.strptime(fecha_ult_vac,'%Y-%m-%d') if fecha_ult_vac else datetime.strptime(fecha_ing,'%Y-%m-%d')
				payslips = filter(lambda payslip:datetime.strptime(payslip.date_to,'%Y-%m-%d') >= aux and datetime.strptime(payslip.date_from,'%Y-%m-%d') < aux+timedelta(days=days_ult) ,payslips)
				for payslip in payslips:
					worked_days += self.env['hr.payslip.worked_days'].search([('payslip_id','=',payslip.id),('code','=','DLAB')]).number_of_days
					worked_days += self.env['hr.payslip.worked_days'].search([('payslip_id','=',payslip.id),('code','=','DVAC')]).number_of_days
					faltas += self.env['hr.payslip.worked_days'].search([('payslip_id','=',payslip.id),('name','=','FALTAS')]).number_of_days
				dias_efect = worked_days
				if employee.fecha_vacacion:
					if jornada == 'six':
						fecha_vac = datetime.strptime(fecha_ult_vac,'%Y-%m-%d') + timedelta(days=days_ult) if dias_efect >= 260 else datetime.strptime(fecha_ult_vac,'%Y-%m-%d') + timedelta(days=days_ult + (260 - dias_efect))
					else:
						fecha_vac = datetime.strptime(fecha_ult_vac,'%Y-%m-%d') + timedelta(days=days_ult) if dias_efect >= 210 else datetime.strptime(fecha_ult_vac,'%Y-%m-%d') + timedelta(days=days_ult + (210 - dias_efect))
				else:
					if jornada == 'six':
						fecha_vac = datetime.strptime(fecha_ing,'%Y-%m-%d') + timedelta(days=days_ing) if dias_efect >= 260 else datetime.strptime(fecha_ing,'%Y-%m-%d') + timedelta(days=days_ing + (260 - dias_efect))
					else:
						fecha_vac = datetime.strptime(fecha_ing,'%Y-%m-%d') + timedelta(days=days_ing) if dias_efect >= 210 else datetime.strptime(fecha_ing,'%Y-%m-%d') + timedelta(days=days_ing + (210 - dias_efect))
				linea = self.env['hr.rol.vacaciones.line'].search([('employee_id','=',employee.id),('rol_id','=',self.id)])
				diferencia = linea.diferencia
				aux_dias_efect = copy(dias_efect)
				linea.write({
						'fecha_ing':fecha_ing,
						'fecha_ult_vac':fecha_ult_vac,
						'fecha_vac':fecha_vac,
						'faltas':faltas,
						'dias_efect':dias_efect,
						'diferencia':diferencia,
						'aux_dias_efect':aux_dias_efect
					})
			else:
				raise UserError('El empleado '+str(employee.name_related)+' no tiene contratos vigentes')
		self.rol_line.refresh()
		return self.env['planilla.warning'].info(title='Resultado', message="Se actualizo de manera correcta")

	@api.multi
	def add_employee(self):
		employees = [line.employee_id.id for line in self.rol_line]
		employees.append(1)
		employees = self.env['hr.employee'].search([('id','not in',employees)])
		return self.env['add.employee'].get_wizard(employees,self.fiscalyear_id)

	@api.multi
	def csv_export(self):
		ruta = self.env['main.parameter.hr'].search([("id","=","1")])[0].dir_create_file
		f = open(ruta+'rol_diferencias.txt', "w+")
		for line in self.rol_line:
			f.write(str(line.dni)+"|"+str(line.diferencia)+"\r\n")
		f.close()
		f = open(ruta+'rol_diferencias.txt','rb')
		vals = {
			'output_name': 'Diferencias_Rol'+(self.fiscalyear_id.name if self.fiscalyear_id else '')+'.txt',
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
	def get_rol_vacaciones_excel(self):
		import io
		from xlsxwriter.workbook import Workbook

		direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
		workbook = Workbook(direccion +'rol_vacaciones'+(self.fiscalyear_id.name if self.fiscalyear_id else '')+'.xlsx')
		worksheet = workbook.add_worksheet("Rol Vacaciones "+self.fiscalyear_id.name if self.fiscalyear_id else '')
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

		numberdos = workbook.add_format({'num_format':'0.00'})
		numberdos.set_border(style=1)
		numberdos.set_font_size(10)
		numberdos.set_font_name('Times New Roman')

		dateformat = workbook.add_format({'num_format':'d-m-yyyy'})
		dateformat.set_border(style=1)
		dateformat.set_font_size(10)
		dateformat.set_font_name('Times New Roman')

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		worksheet.merge_range(1,0,1,3,"ROL DE VACACIONES "+self.fiscalyear_id.name, especial3)

		#worksheet.write(4,0,u"AÑO",boldbord)
		worksheet.write(4,0,"EMPLEADO",boldbord)
		#worksheet.write(4,2,"JORNADA SEMANAL",boldbord)
		worksheet.write(4,1,"FECHA INGRESO",boldbord)
		worksheet.write(4,2,"FECHA ULTIMA VACACION",boldbord)
		worksheet.write(4,3,"FECHA VACACIONES",boldbord)
		#worksheet.write(4,6,"TOTAL FALTAS",boldbord)
		#worksheet.write(4,7,"DIAS EFECTIVOS",boldbord)
		#worksheet.write(4,8,"FECHA REAL",boldbord)
		#worksheet.write(4,9,"DIFERENCIA",boldbord)

		x=5

		for line in self.rol_line:
			#worksheet.write(x,0,line.fiscalyear_id.name if line.fiscalyear_id else '',especial1)
			worksheet.write(x,0,(line.employee_id.a_paterno if line.employee_id.a_paterno else '')+' '+(line.employee_id.a_materno if line.employee_id.a_materno else '')+' '+(line.employee_id.nombres if line.employee_id.a_paterno else ''),especial1)
			#worksheet.write(x,2,line.jornada if line.jornada else '',especial1)
			worksheet.write(x,1,line.fecha_ing if line.fecha_ing else '',dateformat)
			worksheet.write(x,2,line.fecha_ult_vac if line.fecha_ult_vac else '',dateformat)
			worksheet.write(x,3,line.fecha_vac if line.fecha_vac else '',dateformat)
			#worksheet.write(x,6,line.faltas if line.faltas else 0,numberdos)
			#worksheet.write(x,7,line.dias_efect if line.dias_efect else 0,numberdos)
			#worksheet.write(x,8,line.fecha_real if line.fecha_real else '',dateformat)
			#worksheet.write(x,9,line.diferencia if line.diferencia else 0,numberdos)
			x += 1

		tam_col = [38,13,13,13,11,11,11,11]

		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])
		worksheet.set_column('G:G', tam_col[6])
		worksheet.set_column('H:H', tam_col[7])

		workbook.close()

		f = open(direccion + 'rol_vacaciones'+(self.fiscalyear_id.name if self.fiscalyear_id else '')+'.xlsx', 'rb')

		vals = {
			'output_name': 'Rol_Vacaciones'+(self.fiscalyear_id.name if self.fiscalyear_id else '')+'.xlsx',
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
	def get_wizard(self):
		return self.env['import.difference'].get_wizard()

class HrRolVacacionesLine(models.Model):
	_name = 'hr.rol.vacaciones.line'

	rol_id = fields.Many2one('hr.rol.vacaciones')
	#fiscalyear_id = fields.Many2one('account.fiscalyear',u'Año')
	employee_id = fields.Many2one('hr.employee','Empleado')
	dni = fields.Char('DNI',related="employee_id.identification_id",store=True)
	#jornada = fields.Integer('Jornada Semanal',help="Jornada Semanal")
	fecha_ing = fields.Date('Fecha Ingreso')
	fecha_ult_vac = fields.Date('Fecha Ultima Vacacion')

	@api.depends('fecha_ult_vac')
	def _get_vac(self):
		fecha_ult_vac = datetime.strptime(self.fecha_ult_vac,'%Y-%m-%d')
		self.fecha_vac = date(fecha_ult_vac.year + 1, fecha_ult_vac.month, fecha_ult_vac.day)

	fecha_vac = fields.Date('Fecha Vacaciones',compute="_get_vac",store=True)

	#faltas = fields.Integer('Total Faltas')
	#dias_efect = fields.Integer('Dias Efectivos')
	#aux_dias_efect = fields.Integer()
	#fecha_real = fields.Date('Fecha Real')
	#diferencia = fields.Integer('Diferencia',default=0)
	"""
	@api.multi
	def write(self,vals):
		vals['dias_efect'] = self.aux_dias_efect - vals['diferencia']
		return super(HrRolVacacionesLine,self).write(vals)

	@api.model
	@api.onchange('diferencia')
	def get_diference(self):
		self.dias_efect = self.aux_dias_efect - self.diferencia
	"""

	@api.multi
	def detalle_faltas(self):
		self.env['detalle.faltas'].search([]).unlink()
		employees = self.env['hr.employee'].search([('id','=',self.employee_id.id)])
		for employee in employees:
			worked_days = 0
			faltas = 0
			dates = [i.date_start for i in employee.contract_ids if i.situacion_id.codigo == '1']
			if len(dates) > 0:
				fecha_ing = min(dates)
				jornada = employee.contract_id.jornada
				fecha_ult_vac = employee.fecha_vacacion if employee.fecha_vacacion else False
				payslips = self.env['hr.payslip'].search([('employee_id','=',employee.id)])
				days_ult = 366 if self.is_leap(datetime.strptime(fecha_ult_vac,'%Y-%m-%d').year) else 365
				aux = datetime.strptime(fecha_ult_vac,'%Y-%m-%d') if fecha_ult_vac else datetime.strptime(fecha_ing,'%Y-%m-%d')
				payslips = filter(lambda payslip:datetime.strptime(payslip.date_to,'%Y-%m-%d') >= aux and datetime.strptime(payslip.date_from,'%Y-%m-%d') < aux+timedelta(days=days_ult) ,payslips)
				for payslip in payslips:
					dias_f = self.env['hr.payslip.worked_days'].search([('payslip_id','=',payslip.id),('name','=','FALTAS')]).number_of_days
					faltas += dias_f
					if dias_f > 0:
						self.env['detalle.faltas'].create({'payslip_run_id':payslip.payslip_run_id.id,
															'faltas':dias_f})
			else:
				raise UserError('El empleado '+str(employee.name_related)+' no tiene contratos vigentes')
		return self.env['detalle.faltas'].get_wizard()

class WizardDetalleFaltas(models.TransientModel):
	_name = 'detalle.faltas'

	payslip_run_id = fields.Many2one('hr.payslip.run','Procesamiento de Nomina')
	faltas = fields.Integer('Faltas')

	@api.multi
	def get_wizard(self):
		return {
			'name':_('Detalle de Faltas'),
			'type':'ir.actions.act_window',
			'res_id':self.id,
			'view_type':'form',
			'view_mode':'tree,form',
			'res_model':'detalle.faltas',
			'views':[[self.env.ref('planilla.detalle_faltas_wizard').id,'tree']],
			'target':'new'
		}

class WizardImportDifference(models.TransientModel):
	_name = 'import.difference'

	file_fees = fields.Binary('Archivo Importacion',required=True)
	file_name = fields.Char()
	separator = fields.Char("Separador",default="|",size=1)

	@api.multi
	def get_wizard(self):
		return {
			'name':_('Importacion Diferencia'),
			'res_id':self.id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'import.difference',
			'views':[[self.env.ref('planilla.wizard_difference_view').id,'form']],
			'type':'ir.actions.act_window',
			'target':'new'
		}

	@api.multi
	def csv_import(self):
		data = base64.b64decode(self.file_fees)
		data = data.strip().split("\n")
		for c,line in enumerate(data,1):
			line = line.split(self.separator)
			if len(line) != 2:
				raise UserError('El archivo solo debe tener 2 columnas por linea, la linea '+str(c)+' no cumple este requisito')
			vals = {
					'diferencia':int(line[1])
				}
			rol = self.env['hr.rol.vacaciones'].browse(self._context['active_id'])
			rol_line = self.env['hr.rol.vacaciones.line'].search([('dni','=',line[0]),('fiscalyear_id','=',rol.fiscalyear_id.id)],limit=1)
			if len(rol_line) < 1:
				raise UserError(u"No se encontró el empleado con DNI "+str(line[0])+" en las lineas del rol de vacaciones, verifique que dicho empleado se encuentre en alguna de las lineas.")
			try:
				rol_line.write(vals)
			except:
				raise UserError("Hay un error en la linea "+str(c))
			#self.env['account.prestamo'].browse(self._context['active_id']).prestamo_line.refresh()
		return self.env['planilla.warning'].info(title='Resultado de importacion', message="Se importo de manera exitosa.")

class WizardAddEmployee(models.Model):
	_name="add.employee"

	employee_ids = fields.Many2many('hr.employee','employee_ids_many2many',string="Empleados")
	fiscalyear_id = fields.Many2one('account.fiscalyear')

	@api.multi
	def get_wizard(self,employees,fiscalyear_id):
		employees = [i.id for i in employees]
		return {
			'name':_(u'Añadir Empleado'),
			'res_id':self.id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'add.employee',
			'views':[[self.env.ref('planilla.wizard_add_employee').id,'form']],
			'type':'ir.actions.act_window',
			'target':'new',
			'context':{
				'default_employee_ids':[(6,0,employees)],
				'default_fiscalyear_id':fiscalyear_id.id
				},
		}

	@api.multi
	def add_employee(self):
		if len(self.employee_ids) == 0:
			raise UserError('No hay empleados para añadir')
		else:
			for employee in self.employee_ids:
				dates = [i.date_start for i in employee.contract_ids if i.situacion_id.codigo == '1']
				if len(dates) > 0:
					fecha_ing = min(dates)
					self.env['hr.rol.vacaciones.line'].create({
						'rol_id':self._context['active_id'],
						'employee_id':employee.id,
						'fecha_ing':fecha_ing,
						'fecha_ult_vac':fecha_ing
					})
				else:
					raise UserError('El empleado '+employee.name_related+' no tiene contratos vigentes.')
			#self.env['hr.rol.vacaciones'].browse(self._context['active_id']).get_employee_last_vacation(self.employee_ids,datetime.strptime(self.fiscalyear_id.name,'%Y').year)
			return self.env['planilla.warning'].info(title='Resultado', message="Se agrego el empleado de manera exitosa.")