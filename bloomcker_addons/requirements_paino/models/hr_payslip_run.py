# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from datetime import date, datetime
from odoo.exceptions import ValidationError, UserError
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red, black, blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, Table, PageBreak
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import simpleSplit
from cgi import escape
import base64
import io
from xlsxwriter.workbook import Workbook
import sys
reload(sys)
sys.setdefaultencoding('iso-8859-1')
import os
import copy
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import StringIO
import time
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

import calendar
from datetime import date, datetime
from openerp.osv import osv
from math import modf
from decimal import *
import logging
_logger = logging.getLogger(__name__)


class EmployeeExt(models.Model):
	_inherit = 'hr.payslip.run'

	def update_employees(self):
		payslips = self.env['hr.payslip']
		from_date = self.date_start
		to_date = self.date_end
		query = """
		select hc.id
		from hr_contract hc
		inner join hr_employee he on hc.employee_id = he.id
		where
		(date_end >= '%s' and date_end <= '%s') or
		(date_start <= '%s' and date_start >='%s'   ) or
		(
			date_start <='%s' and (date_end is null or date_end >= '%s' )
		)
		""" % (from_date, to_date,
			   to_date, from_date,
			   from_date, to_date
			   )
		self.env.cr.execute(query)
		employee_aux_ids = self.env.cr.dictfetchall()
		employees = []

		for slip in self.slip_ids:
			employees.append(slip.employee_id.id)

		for contract in self.env['hr.contract'].browse([row['id'] for row in employee_aux_ids]):
			if contract.employee_id.id not in employees:
				slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, contract.employee_id.id, contract.id)
				number = self.env['ir.sequence'].next_by_code('salary.slip')
				res = {
					'employee_id': contract.employee_id.id,
					'number':number,
					'name': slip_data['value'].get('name'),
					'struct_id': slip_data['value'].get('struct_id'),
					'contract_id': contract.id,
					'payslip_run_id': self.id,
					'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
					'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
					'date_from': from_date,
					'date_to': to_date,
					'credit_note': self.credit_note,
					'company_id': contract.employee_id.company_id.id,
				}
				payslip = self.env['hr.payslip'].create(res)
				payslip.load_entradas_tareos()
				payslips += payslip

	@api.multi
	def _wizard_hr_payslip_run(self):
		if len(self.ids) > 1:
			raise UserError(
				'Solo se puede mostrar una planilla a la vez, seleccione solo una nómina')

		vals = {
			'tipo': 'no practicante',
		}

		sfs_id = self.env['hr.payslip.run.wizard'].create(vals)

		return {
			'name': 'Exportar Plames a Excel según tipo de trabajador',
			"type": "ir.actions.act_window",
			"res_model": "hr.payslip.run.wizard",
			'view_type': 'form',
			'view_mode': 'form',
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
			'context': {'current_id': self.id}
		}


	@api.multi
	def exportar_plame_horas(self):
		if len(self.ids) > 1:
			raise UserError('Solo se puede mostrar una planilla a la vez, seleccione solo una nómina')

		output = io.BytesIO()

		# workbook = Workbook('planilla_plame.xls')
		planilla_ajustes = self.env['planilla.ajustes'].search([], limit=1)
		try:
			ruta = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		docname = ruta+'0601%s%s%s.jor' % (self.date_end[:4], self.date_end[5:7], planilla_ajustes.ruc if planilla_ajustes else '')

		f = open(docname, "w+")
		for payslip_run in self.browse(self.ids):
			employees = []
			for payslip in payslip_run.slip_ids.filtered(lambda s: s.contract_id.regimen_laboral_empresa != 'practicante'):
				if payslip.employee_id.id not in employees:
					sql = """
						select
						coalesce(ptd.codigo_sunat,'') as code,
						he.identification_id as dni,
						sum(case when hpwd.code = '%s' then hpwd.number_of_days else 0 end) as dlab,
						sum(case when hpwd.code = '%s' then hpwd.number_of_days else 0 end) as fal,
						sum(case when hpwd.code = 'H25' then hpwd.number_of_hours else 0 end) as h25,
						sum(case when hpwd.code = 'H35' then hpwd.number_of_hours else 0 end) as h35,
						sum(case when hpwd.code = 'H100' then hpwd.number_of_hours else 0 end) as h100
						from hr_payslip hp
						inner join hr_employee he on he.id = hp.employee_id
						inner join planilla_tipo_documento ptd on ptd.id = he.tablas_tipo_documento_id
						inner join hr_payslip_worked_days hpwd on hpwd.payslip_id = hp.id
						inner join hr_contract hc on hc.id = hp.contract_id
						where hp.payslip_run_id = %d
						and hp.employee_id = %d
						and hc.regimen_laboral_empresa not in ('practicante')
						and hpwd.code in ('%s','%s','HE25','HE35','HE100')
						group by ptd.codigo_sunat,he.identification_id
					"""%(planilla_ajustes.cod_dias_laborados.codigo,
						planilla_ajustes.cod_dias_no_laborados.codigo,
						payslip_run.id,
						payslip.employee_id.id,
						planilla_ajustes.cod_dias_laborados.codigo,
						planilla_ajustes.cod_dias_no_laborados.codigo
						)
					self.env.cr.execute(sql)
					data = self.env.cr.dictfetchone()
					_logger.info(data)
					dias_laborados=int(data['dlab'])-int(payslip.feriados) if not payslip.contract_id.hourly_worker else 0
					if payslip.employee_id.calendar_id.id:
						total = payslip.employee_id.calendar_id.average_hours if payslip.employee_id.calendar_id.average_hours > 0 else 8
					else:
						total = 8
					# formula para los dias laborados segun sunat
					if not payslip.contract_id.hourly_worker:
						total_horas_jornada_ordinaria = (dias_laborados-int(data['fal']))*int(total)
					else:
						total_horas_jornada_ordinaria = sum(payslip.worked_days_line_ids.filtered(lambda l:l.code == planilla_ajustes.cod_dias_laborados.codigo).mapped('number_of_hours'))
					horas_extra = int(data['h25']) + int(data['h35']) + int(data['h100'])
					f.write(str(data['code'])+'|'+str(data['dni'])+'|'+str(total_horas_jornada_ordinaria)+'|0|'+str(horas_extra)+"|0|\r\n")
					employees.append(payslip.employee_id.id)
		f.close()
		f = open(docname,'rb')
		vals = {
			'output_name': '0601%s%s%s.jor' % (
			self.date_end[:4], self.date_end[5:7], planilla_ajustes.ruc if planilla_ajustes else ''),
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
	def exportar_plame_subsidios(self):
		if len(self.ids) > 1:
			raise UserError(
				'Solo se puede mostrar una planilla a la vez, seleccione solo una nómina')

		output = io.BytesIO()

		# workbook = Workbook('planilla_plame.xls')
		planilla_ajustes = self.env['planilla.ajustes'].search([], limit=1)
		try:
			ruta = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		file_name = '0601%s%s%s.snl' % (self.date_end[:4], self.date_end[5:7], planilla_ajustes.ruc if planilla_ajustes else '')
		docname = ruta+file_name

		f = open(docname, "w+")

		for payslip_run in self.browse(self.ids):
			employees = []
			for payslip in payslip_run.slip_ids:
				if payslip.employee_id.id not in employees:
					if payslip.contract_id.regimen_laboral_empresa != 'practicante':
						sql = """
						select
						max(he.identification_id) as dni,
						max(ptd.codigo_sunat) as sunat_code,
						pts.codigo as code,
						sum(hls.nro_dias) as dias
						from hr_payslip hp
						inner join hr_employee he on he.id = hp.employee_id
						inner join hr_contract hc on hc.id = hp.contract_id
						inner join planilla_tipo_documento ptd on ptd.id = he.tablas_tipo_documento_id
						inner join hr_labor_suspension hls on hls.suspension_id = hc.id
						inner join planilla_tipo_suspension pts on pts.id = hls.tipo_suspension_id
						where hp.payslip_run_id = %d
						and hp.employee_id = %d
						and hc.regimen_laboral_empresa not in ('practicante')
						and hls.periodos = %d
						group by hp.employee_id,pts.codigo
						"""%(payslip_run.id,payslip.employee_id.id,payslip_run.id)
						self.env.cr.execute(sql)
						data = self.env.cr.dictfetchall()
						for i in data:
							f.write(str(i['sunat_code'])+'|'+str(i['dni'])+'|'+str(i['code'])+'|'+str(i['dias'])+"|\r\n")
						employees.append(payslip.employee_id.id)

		f.close()
		f = open(docname,'rb')
		vals = {
			'output_name': file_name,
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
	def exportar_plame_tasas(self):
		if len(self.ids) > 1:
			raise UserError(
				'Solo se puede mostrar una planilla a la vez, seleccione solo una nómina')

		output = io.BytesIO()

		# workbook = Workbook('planilla_plame.xls')
		planilla_ajustes = self.env['planilla.ajustes'].search([], limit=1)
		try:
			ruta = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		file_name = '0601%s%s%s.tas' % (self.date_end[:4], self.date_end[5:7], planilla_ajustes.ruc if planilla_ajustes else '')
		docname = ruta+file_name

		f = open(docname, "w+")

		for payslip_run in self.browse(self.ids):
			employees = []
			for payslip in payslip_run.slip_ids:
				if payslip.employee_id.id not in employees:
					if payslip.contract_id.regimen_laboral_empresa != 'practicante':
						payslips = self.env['hr.payslip'].search([('employee_id','=',payslip.employee_id.id)])
						if len(payslips) > 1:
							last_contract = max(payslips.mapped('contract_id'),key=lambda c:c['date_start'])
							sctr = last_contract.sctr if last_contract.sctr else False
						else:
							sctr = payslip.contract_id.sctr if payslip.contract_id.sctr else False
						if sctr:
							cod_sunat = payslip.employee_id.tablas_tipo_documento_id.codigo_sunat if payslip.employee_id.tablas_tipo_documento_id else ''
							dni = payslip.employee_id.identification_id
							f.write(str(cod_sunat)+'|'+str(dni)+'|'+str(sctr.code)+'|'+str(sctr.porcentaje)+"|\r\n")
							employees.append(payslip.employee_id.id)

		f.close()
		f = open(docname,'rb')
		vals = {
			'output_name': file_name,
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

	def make_excel_sbank_xlsm(self):
		ctx = dict(self._context or {})
		defa = self.env['hr.sbank.export.config'].search([])[0]
		ctx.update({
				'default_name':defa.id,
				# 'default_paydate':datetime.now().date,
				'default_type_export':'payslip_run',
				'default_payslip_run_id':self.id,
			})


		return {
			'type': 'ir.actions.act_window',
			'res_model': 'hr.sbank.export.xlsm.wizard',
			'view_type': 'form',
			'view_mode': 'form',
			'target': 'new',
			'context':ctx,
		}



class hr_sbank_export_xlsm_wizard(models.TransientModel):
	_name='hr.sbank.export.xlsm.wizard'

	name=fields.Many2one('hr.sbank.export.config','Plantilla de configuración')
	pay_date = fields.Date('Fecha de pago')
	type_export = fields.Selection([('payslip_run','Planilla'),('gratif','Gratificaciones'),('cts','CTS')],'Tipo de exportación')
	payslip_run_id = fields.Many2one('hr.payslip.run','Planilla a exportar')
	type_employee = fields.Selection([('practicante','Practicante'),('empleado','Empleado')],'Tipo de trabajador',default='empleado',required=True)


	def make_excel_pla_export_xlsm(self):
		_logger.info('make_excel_pla_export_xlsm')
		if self.type_export!='payslip_run':
			raise UserError('El formato seleccionado aun está en desarrollo')

		self.env['planilla.planilla.tabular.wizard'].reconstruye_tabla(self.payslip_run_id.date_start,self.payslip_run_id.date_end)

		try:
			direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		workbook = Workbook(direccion+'planilla_exportar.xlsm')
		worksheet = workbook.add_worksheet('PLANILLAS')
		workbook.set_vba_name('planilla_exportar')
		worksheet.set_landscape()  # Horizontal
		worksheet.set_paper(9)  # A-4
		worksheet.set_margins(left=0.75, right=0.75, top=1, bottom=1)
		worksheet.fit_to_pages(1, 0)  # Ajustar por Columna

		fontSize = 8
		bold = workbook.add_format(
			{'bold': True, 'font_name': 'Arial', 'font_size': fontSize})
		normal = workbook.add_format()
		formatop = workbook.add_format()
		boldbord = workbook.add_format({'bold': True, 'font_name': 'Arial'})
		# boldbord.set_border(style=1)
		boldbord.set_align('center')
		boldbord.set_align('bottom')
		boldbord.set_text_wrap()
		boldbord.set_font_size(fontSize)
		boldbord.set_bg_color('#99CCFF')
		numberdos = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'right'})
		formatLeft = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'font_size': fontSize})
		formatRight = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'right', 'font_size': fontSize})
		formatLeftColor = workbook.add_format(
			{'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'center', 'bg_color': '#FF0000', 'font_size': fontSize,'font_color': 'white'})
		styleFooterSum = workbook.add_format(
			{'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'right', 'font_size': fontSize, 'top': 1, 'bottom': 2})
		styleFooterSum.set_bottom(6)
		formatLeftColor.set_align('vcenter')
		formatLeftColor.set_text_wrap()
		formatop.set_border_color('#FFFFFF')
		numberdos.set_font_size(fontSize)
		bord = workbook.add_format()
		bord.set_border(style=1)
		bord.set_text_wrap()
		# numberdos.set_border(style=1)
		worksheet.set_row(0, 10,formatop)
		worksheet.set_row(1, 10,formatop)
		worksheet.set_row(2, 10,formatop)
		worksheet.set_row(3, 10,formatop)
		worksheet.set_row(4, 10,formatop)
		worksheet.set_row(5, 10,formatop)
		title = workbook.add_format({'bold': True, 'font_name': 'Arial'})
		title.set_align('center')
		title.set_align('vcenter')

		workbook.add_vba_project('/mnt/extra-addons2/requirements_paino/data/vbaProject.bin')
		# title.set_text_wrap()
		worksheet.insert_button('F3', {'macro':   'Generar_txt',
                               'caption': 'Convertir a txt',
                               'width':   200,
                               'height':  30})

		# worksheet.insert_button('M5', {'macro':   'Ayuda_Macro',
        #                        'caption': 'Ayuda',
        #                        'width':   200,
        #                        'height':  30})
		title.set_font_size(18)
		company = self.env['res.company'].search([], limit=1)[0]

		x = 0

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		worksheet.merge_range(
			'A1:J1', u"PLANILLA DE SUELDOS Y SALARIOS EXPORTAR", title)
		worksheet.set_row(x, 29)
		x = x+2

		worksheet.write(x, 0, u"Empresa:", bold)
		worksheet.write(x, 1, company.name, formatLeft)
		worksheet.set_row(6, 30)
		worksheet.set_column(0, 0, 10)
		worksheet.set_column(1, 1, 30)
		worksheet.set_column(2, 2, 10)
		worksheet.set_column(3, 3, 10)
		worksheet.set_column(4, 4, 10)
		worksheet.set_column(5, 5, 10)
		worksheet.set_column(6, 6, 10)
		worksheet.set_column(7, 7, 10)
		worksheet.set_column(8, 8, 10)
		worksheet.set_column(9, 9, 10)
		worksheet.set_column(10, 10, 30)
		x = x+4

		header_planilla_tabular = self.env['ir.model.fields'].search(
			[('name', 'like', 'x_%'), ('model', '=', 'planilla.tabular')], order="create_date")
		worksheet.write(x, 0, 'CODIGO EMPLEADO', formatLeftColor)
		worksheet.write(x, 1, 'NOMBRE DEL EMPLEADO', formatLeftColor)
		worksheet.write(x, 2, 'CONCEPTO', formatLeftColor)
		worksheet.write(x, 3, 'FECHA DE PAGO', formatLeftColor)
		worksheet.write(x, 4, 'MONTO A PAGAR', formatLeftColor)
		worksheet.write(x, 5, 'FORMA DE PAGO', formatLeftColor)
		worksheet.write(x, 6, 'CODIGO OFICINA', formatLeftColor)
		worksheet.write(x, 7, 'CODIGO CUENTA', formatLeftColor)
		worksheet.write(x, 8, 'IFT?', formatLeftColor)
		worksheet.write(x, 9, 'DOCUMENTO DE INDENTIDAD', formatLeftColor)
		worksheet.write(x, 10, 'CCI', formatLeftColor)
		x=x+1

		if self.type_employee == 'empleado':
			for l in self.payslip_run_id.slip_ids.filtered(lambda p: p.contract_id.regimen_laboral_empresa != 'practicante'):
				if not l.employee_id.bank_account_id.acc_number:
					continue
				valor = 0
				a=False
				a = l.line_ids.filtered(lambda p: p.salary_rule_id.id == self.name.salary_rule_id.id)
				if a:
					valor = a.total
				metodopago = '3'
				cci=''
				codofi=''
				codcta=''
				desde=int(self.name.cod_ofi_pos[0:1])
				hasta=int(self.name.cod_ofi_pos[2:])
				if self.name.bank_id.id!=l.employee_id.bank_account_id.bank_id.id:
					metodopago='4'
					cci=l.employee_id.bank_account_id.acc_icc_number
				else:
					codofi=l.employee_id.bank_account_id.acc_number[desde-1:hasta]
					codcta=l.employee_id.bank_account_id.acc_number[hasta+1:]

				nombresc=l.employee_id.nombres.strip()+' '+l.employee_id.a_paterno.strip()+' '+l.employee_id.a_materno.strip()

				worksheet.write(x,0,l.employee_id.identification_id[0:8],formatLeft)
				worksheet.write(x,1,nombresc[0:30],formatLeft)
				worksheet.write(x,2,self.name.text_concep,formatLeft)
				worksheet.write(x,3,self.pay_date,formatLeft)
				worksheet.write(x,4,valor,formatRight)
				worksheet.write(x,5,metodopago)
				worksheet.write(x,6,codofi,formatLeft)
				worksheet.write(x,7,codcta,formatLeft)
				worksheet.write(x,8,'',formatLeft)
				worksheet.write(x,9,l.employee_id.identification_id[0:8],formatLeft)
				worksheet.write(x,10,cci,formatLeft)
				x=x+1
		else:
			for l in self.payslip_run_id.slip_ids.filtered(lambda p: p.contract_id.regimen_laboral_empresa == 'practicante'):
				if not l.employee_id.bank_account_id.acc_number:
					continue
				valor = 0
				a=False
				a = l.line_ids.filtered(lambda p: p.salary_rule_id.id == self.name.salary_rule_id.id)
				if a:
					valor = a.total
				metodopago = '3'
				cci=''
				codofi=''
				codcta=''
				desde=int(self.name.cod_ofi_pos[0:1])
				hasta=int(self.name.cod_ofi_pos[2:])
				if self.name.bank_id.id!=l.employee_id.bank_account_id.bank_id.id:
					metodopago='4'
					cci=l.employee_id.bank_account_id.acc_icc_number
				else:
					codofi=l.employee_id.bank_account_id.acc_number[desde-1:hasta]
					codcta=l.employee_id.bank_account_id.acc_number[hasta+1:]

				nombresc=l.employee_id.nombres.strip()+' '+l.employee_id.a_paterno.strip()+' '+l.employee_id.a_materno.strip()

				worksheet.write(x,0,l.employee_id.identification_id,formatLeft)
				worksheet.write(x,1,nombresc,formatLeft)
				worksheet.write(x,2,self.name.text_concep,formatLeft)
				worksheet.write(x,3,self.pay_date,formatLeft)
				worksheet.write(x,4,valor,formatRight)
				worksheet.write(x,5,metodopago)
				worksheet.write(x,6,codofi,formatLeft)
				worksheet.write(x,7,codcta,formatLeft)
				worksheet.write(x,8,'',formatLeft)
				worksheet.write(x,9,l.employee_id.identification_id,formatLeft)
				worksheet.write(x,10,cci,formatLeft)
				x=x+1

		workbook.close()

		f = open(direccion+'planilla_exportar.xlsm', 'rb')

		vals = {
			'output_name': 'planilla_exportar.xlsm',
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
