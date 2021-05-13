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

class HrPayslipRunExt(models.Model):

	_inherit = ['hr.payslip.run']

	def deleted_sheet(self):
		for record in self.slip_ids:
			self._cr.execute("DELETE FROM hr_payslip_line WHERE slip_id=%s", (record.id,))
		return True

	def recompute_sheet_lotes(self):
		for record in self.slip_ids:
			self._cr.execute("DELETE FROM hr_payslip_line WHERE slip_id=%s", (record.id,))
			breaks = self.env['breaks.line.bl'].search([('employee_id', '=', record.employee_id.id), ('period', '=', record.payslip_run_id.id), ('type', '=', 'break')])
			breaks_mother = self.env['breaks.line.bl'].search([('employee_id', '=', record.employee_id.id), ('period', '=', record.payslip_run_id.id), ('type', '=', 'break_mother')])
			subsidy = self.env['breaks.line.bl'].search([('employee_id', '=', record.employee_id.id), ('period', '=', record.payslip_run_id.id), ('type', '=', 'subsidy')])
			mother_days = self.env['hr.payslip.worked_days'].search([('payslip_id', '=', record.id), ('code', '=', 'DSUBM')], limit=1)
			date_c = datetime.strptime(record.contract_id.date_start, "%Y-%m-%d")
			date_n = datetime.strptime(record.date_from, "%Y-%m-%d")
			days_exit = abs(date_c - date_n).days
			num_days_m = 30

			if days_exit < 29 and str(date_c)[5:7] == str(date_n)[5:7]:
				num_days_m = 30 - days_exit

			if mother_days:
				days_mother = mother_days.number_of_days
			else:
				days_mother = 0

			days_total = 0
			days_break = 0
			days_break_mother = 0
			days_subsidy = 0
			days_faults = 0

			for i in breaks:
				days_break += i.days_total

			for i in breaks_mother:
				days_break_mother += i.days_total

			for i in subsidy:
				days_subsidy += i.days_total

			for i in record.periodos_devengue:
				days_total += i.dias

			for i in record.fault_ids:
				days_faults += i.days

			for days_line in record.worked_days_line_ids:
				if days_line.code == "DVAC":
					days_line.number_of_days = days_total
				elif days_line.code == "DESC":
					days_line.number_of_days = days_break
				elif days_line.code == "DSUBM":
					days_line.number_of_days = days_break_mother
				elif days_line.code == "DSUBE":
					days_line.number_of_days = days_subsidy
				elif days_line.code == "FAL":
					days_line.number_of_days = days_faults
				elif days_line.code == "DLAB":
					days_line.number_of_days = num_days_m - days_total - days_break - days_faults - days_break_mother - days_subsidy

			for payslip in record:
				number = payslip.number
				contract_ids = payslip.contract_id.ids
				lines = [(0, 0, line) for line in record.get_payslip_lines(contract_ids, payslip.id)]
				payslip.write({'line_ids': lines, 'number': number})

        	return True


	@api.multi
	def genera_boleta_empleado(self, date_start, date_end, payslips, dias_no_laborados, dias_laborados, total_horas_jornada_ordinaria, total_minutos_jornada_ordinaria, total_sobretiempo, dias_subsidiados, elements, company, categories, planilla_ajustes):
		try:
			ruta = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		_logger.info('genera_boleta_empleado')
		style_title = ParagraphStyle(
			name='Center', alignment=TA_LEFT, fontSize=14, fontName="times-roman")
		style_form = ParagraphStyle(
			name='Justify', alignment=TA_JUSTIFY, fontSize=10, fontName="times-roman")
		style_cell = ParagraphStyle(
			name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		style_cell_right = ParagraphStyle(
			name='Right', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_cell_left = ParagraphStyle(
			name='Left', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		style_cell_bold = ParagraphStyle(
			name='centerBold', alignment=TA_CENTER, fontSize=8, fontName="Times-Bold")

		colorHeader = colors.Color(
			red=(219/255.0), green=(229/255.0), blue=(241/255.0))
		try:
			logo = open(ruta+"logo.jpg","rb")
			print(logo)
			c = Image(logo,2*inch,0.5*inch)
		except Exception as e:
			c = ''
			print("No se encontro el logo en la ruta "+ str(ruta) +" Inserte una imagen del logo en la ruta especificada con el nombre 'logo.jpg'")
		finally:
			data = [[c,'','','','','','','']]

			t = Table(data, style=[
				('ALIGN', (0, 0), (-1, -1), 'CENTER')
			],hAlign='LEFT')
			t._argW[0] = 1.5*inch
			elements.append(t)

		texto = "Trabajador – Datos de boleta de pago"
		elements.append(Paragraph(texto, style_title))
		elements.append(Spacer(1, 10))

		colorTitle = colors.Color(
			red=(197/255.0), green=(217/255.0), blue=(241/255.0))

		data = [
			[Paragraph('RUC: ' + (planilla_ajustes.ruc if planilla_ajustes.ruc else ''), style_cell_left),'', '', '' , Paragraph('Empleador: ' + str(company.name),style_cell_left), '', '',''],
			[Paragraph('Periodo: ' + date_start + ' - ' + date_end,style_cell_left), '', '', '', '', '', '', '']
		]

		t = Table(data, style=[
			# ('SPAN', (1, 0), (4, 0)),  # cabecera

			('BACKGROUND', (0, 0), (-1, -1), colorTitle),  # fin linea 3
			('SPAN', (0, 0), (3, 0)),
			('SPAN', (4, 0), (7, 0)),
			('SPAN', (0, 1), (7, 1)),
			('SPAN', (0, 2), (7, 2)),

			('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
			('BOX', (0, 0), (-1, -1), 0.1, colors.black),
			('LEFTPADDING', (0, 0), (-1, -1), 1),
			('RIGHTPADDING', (0, 0), (-1, -1), 1),
			('BOTTOMPADDING', (0, 0), (-1, -1), 1),
			('TOPPADDING', (0, 0), (-1, -1), 1),

		])
		t._argW[3] = 1.0*inch
		elements.append(t)

		elements.append(Spacer(1, 10))

		empleado = payslips[0].employee_id
		contracts = filter(lambda c:c.situacion_id.codigo != '0',empleado.contract_ids)
		first_contract = min(contracts,key=lambda c:c['date_start']) if contracts else False
		contract_employee = payslips[0].contract_id

		#if len(contract_employee) > 1:
		#	raise UserError('El empleado '+empleado.name_related +
		#					u' tiene más de un contrato activo(Contrato->%s->Informacion->Duracion->date_end)' % empleado.name_related)

		row_empleado = [Paragraph(empleado.tablas_tipo_documento_id.descripcion_abrev if empleado.tablas_tipo_documento_id.descripcion_abrev else '', style_cell), Paragraph(empleado.identification_id if empleado.identification_id else '', style_cell), Paragraph(
			empleado.name_total.strip().title(), style_cell), '', '', '', Paragraph(contract_employee.situacion_id.descripcion_abrev if contract_employee.situacion_id.descripcion_abrev else '', style_cell), '']

		row_empleado_line_4 = [Paragraph(first_contract.date_start if first_contract else '', style_cell),
			Paragraph(contract_employee.tipo_trabajador_id.descripcion_abrev.title() if contract_employee.tipo_trabajador_id.descripcion_abrev else '', style_cell),
			Paragraph((contract_employee.employee_id.job_id.name if contract_employee.employee_id.job_id else '') if contract_employee.employee_id else '',style_cell), '',
			Paragraph(contract_employee.afiliacion_id.entidad if contract_employee.afiliacion_id.entidad else '', style_cell), '',
			Paragraph(contract_employee.cuspp if contract_employee.cuspp else '', style_cell), '']

		horas_sobretiempo = int(
			total_sobretiempo['horas']) if total_sobretiempo['horas'] else 0
		minutos_sobretiempo = int(
			total_sobretiempo['minutos']) if total_sobretiempo['minutos'] else 0
		row_empleado_line_5 = [Paragraph(dias_laborados, style_cell), Paragraph(dias_no_laborados, style_cell), Paragraph(dias_subsidiados, style_cell), Paragraph(
			dict(empleado._fields['condicion'].selection).get(empleado.condicion), style_cell), Paragraph(total_horas_jornada_ordinaria, style_cell), Paragraph(total_minutos_jornada_ordinaria, style_cell), Paragraph(str(horas_sobretiempo), style_cell), Paragraph(str(minutos_sobretiempo), style_cell)]

		id_periodo = self.env['hr.payslip.run'].search([('date_start','=',date_start)]).id
		row_empleado_line_6 = ''
		aux = []
		for i in contract_employee.suspension_laboral:
			if i.periodos.id == id_periodo:
				row_empleado_line_6 = [Paragraph(i.tipo_suspension_id.codigo if i.tipo_suspension_id else '', style_cell), Paragraph(i.motivo if i.motivo else '', style_cell), '', '', '',
									Paragraph(str(i.nro_dias) if i.nro_dias else '', style_cell), Paragraph(contract_employee.otros_5ta_categoria.strip() if contract_employee.otros_5ta_categoria else '', style_cell), '']
				aux.append(row_empleado_line_6)
			else:
				row_empleado_line_6 = [Paragraph('', style_cell), Paragraph('', style_cell), '', '', '',
									Paragraph('', style_cell), Paragraph(contract_employee.otros_5ta_categoria.strip() if contract_employee.otros_5ta_categoria else '', style_cell), '']
		data = [[Paragraph('Documento de identidad', style_cell), '', Paragraph('Apellidos y Nombres', style_cell), '', '', '', Paragraph(u'Situación', style_cell), ''],
				[Paragraph('Tipo', style_cell), Paragraph(
					'Numero', style_cell), '', '', '', '', '', ''],
				row_empleado,
				[Paragraph('Fecha de ingreso', style_cell), Paragraph('Tipo de trabajador', style_cell), Paragraph('Cargo', style_cell),  '', Paragraph(
					u'Régimen Pensionario', style_cell), '', Paragraph('CUSPP', style_cell), ''],
				row_empleado_line_4,
				[Paragraph(u'Días\nlaborados', style_cell), Paragraph(u'Días\nno laborados', style_cell), Paragraph(u'Días\nSubsidiados', style_cell), Paragraph(
					u'Condición', style_cell), Paragraph('Jornada Ordinaria', style_cell), '', Paragraph('Sobretiempo', style_cell), ''],
				['1', '2', '3', '4', Paragraph('Horas', style_cell), Paragraph(
					'Minutos', style_cell), Paragraph('Horas', style_cell), Paragraph('Minutos', style_cell)],
				row_empleado_line_5,
				[Paragraph('Motivo de suspensión', style_cell), '', '', '', '', '', Paragraph(
					'Otros empleadores por\nrentas de 5ta categoría', style_cell), ''],
				[Paragraph('Tipo', style_cell), Paragraph('Motivo', style_cell),
				 '', '', '', Paragraph('Nº Días', style_cell), '', ''],
				]
		table_style = TableStyle([
			('SPAN', (0, 0), (1, 0)),  # cabecera
			('SPAN', (2, 0), (5, 1)),  # cabecera
			('SPAN', (6, 0), (7, 1)),  # cabecera
			('BACKGROUND', (0, 0), (7, 0), colorHeader),  # fin linea 1
			('SPAN', (2, 2), (5, 2)),  # empleado
			('SPAN', (6, 2), (7, 2)),  # empleado
			('BACKGROUND', (0, 1), (7, 1), colorHeader),  # fin linea 2
			#('SPAN', (0, 3), (1, 3)),  # linea 3
			('SPAN', (2, 3), (3, 3)),
			('SPAN', (4, 3), (5, 3)),
			('SPAN', (6, 3), (7, 3)),
			('BACKGROUND', (0, 3), (7, 3), colorHeader),  # fin linea 3
			#('SPAN', (0, 4), (1, 4)),  # linea 4
			('SPAN', (2, 4), (3, 4)),
			('SPAN', (4, 4), (5, 4)),
			('SPAN', (6, 4), (7, 4)),  # fin linea 4
			# linea 5 y 6 horas y sobretiempos
			('SPAN', (0, 5), (0, 6)),
			('SPAN', (1, 5), (1, 6)),
			('SPAN', (2, 5), (2, 6)),
			('SPAN', (3, 5), (3, 6)),
			('SPAN', (4, 5), (5, 5)),
			('SPAN', (6, 5), (7, 5)),
			('BACKGROUND', (0, 5), (7, 6), colorHeader),  # fin linea 6
			('SPAN', (0, 8), (5, 8)),  # linea 8 y 9 horas y sobretiempos
			('SPAN', (1, 9), (4, 9)),
			('SPAN', (6, 8), (7, 9)),
			('BACKGROUND', (0, 8), (7, 9), colorHeader),  # fin linea 9
			#('SPAN', (1, 10), (4, 10)),  # linea 10
			#('SPAN', (6, 10), (7, 10)),  # fin linea 10
			('LEFTPADDING', (0, 0), (-1, -1), 1),
			('RIGHTPADDING', (0, 0), (-1, -1), 1),
			('BOTTOMPADDING', (0, 0), (-1, -1), 1),
			('TOPPADDING', (0, 0), (-1, -1), 1),

			('ALIGN', (0, 0), (-1, -1), 'LEFT'),
			('VALIGN', (0, 0), (7, 0), 'BOTTOM'),
			('GRID', (0, 0), (-1, -1), 0.5, colors.black),
		])
		x=10
		for i in aux:
			data.append(i)
			table_style.add('SPAN', (1, x), (4, x))
			table_style.add('SPAN', (6, x), (7, x))
			x += 1

		t = Table(data)
		t.setStyle(table_style)

		t._argW[3] = 1*inch

		elements.append(t)
		elements.append(Spacer(1, 10))

		detalle_trabajador = []
		positions_in_tables = []
		i = 1
		ids = []
		training_payslip = filter(lambda p:p.contract_id.regimen_laboral_empresa == 'practicante',payslips)
		for j in range(len(categories)-1):
			category = categories[j]
			if category.code == 'APOR_TRA' and training_payslip:
				ids = [tp.contract_id.id for tp in training_payslip]

			st = ','.join(str(payslip) for payslip in payslips.mapped('contract_id.id') if payslip not in ids)
			if len(st) < 1:
				final_st=','.join(str(i) for i in ids)
			else:
				final_st=st
			reglas_salariales_empleado = """
			select min(related_name) as name_related,
			min(dni) as identification_id,
			min(seq) as sequence,
			sum(total) as total,
			t.code as code,
			min(name) as name,
			min(t.cod_sunat) as cod_sunat,
			min(t.is_ing_or_desc) as is_ing_or_desc
			from (
				select e.name_related as related_name,
				e.identification_id as dni,
				hpl.sequence as seq,
				hpl.total as total,
				case when hc.regimen_laboral_empresa = 'practicante' and hpl.code = 'BAS' then 'SUBE' else hpl.code end as code,
				case when hc.regimen_laboral_empresa = 'practicante' and hpl.code = 'BAS' then 'Subencion Economica' else hpl.name end as name,
				sr.cod_sunat as cod_sunat,
				hsrc.is_ing_or_desc as is_ing_or_desc
				from hr_payslip hp
				inner join hr_payslip_line hpl on hp.id=hpl.slip_id
				inner join hr_salary_rule as sr on sr.code = hpl.code
				inner join hr_employee e on e.id = hpl.employee_id
				inner join hr_contract hc on hc.id = hp.contract_id
				inner join hr_salary_rule_category hsrc on hsrc.id = hpl.category_id
				where date_from ='%s' and  date_to='%s' and e.identification_id='%s'
					and hpl.appears_on_payslip='t' and sr.appears_on_payslip='t'  and hpl.category_id=%d  and  hpl.total>0
					and hpl.contract_id in (%s)
				order by e.id,hpl.sequence)t
			group by t.code
			""" % (date_start, date_end, empleado.identification_id, category.id,final_st)


			self.env.cr.execute(reglas_salariales_empleado)
			reglas_salariales_list = self.env.cr.dictfetchall()

			# if len(reglas_salariales_list) > 0:
			detalle_trabajador.append(
				[Paragraph(category.name.title(), style_cell_left), '', '', '', '', '', '', ''])
			positions_in_tables.append(('SPAN', (0, i), (7, i)))
			positions_in_tables.append(
				('BACKGROUND', (0, i), (7, i), colorHeader))
			i = i+1

			for regla_salarial in reglas_salariales_list:
				_logger.info(regla_salarial)
				cod_sunat = Paragraph(regla_salarial['cod_sunat'] if regla_salarial['cod_sunat'] else '', style_cell_left)
				namee = Paragraph(regla_salarial['name'] if regla_salarial['name'] else '', style_cell_left)
				total = Paragraph('{0:.2f}'.format(regla_salarial['total'] if regla_salarial['total'] else ''), style_cell_right)
				detalle_trabajador.append([cod_sunat, namee, '', '', '', total, '', ''] if regla_salarial['is_ing_or_desc'] == 'ingreso' else [cod_sunat, namee, '', '', '', '', total, ''])
				positions_in_tables.append(('SPAN', (1, i), (4, i)))
				i = i+1

		query_neto_pagar = """
		select
		min(e.name_related) as name_related,
		min(e.identification_id) as identification_id,
		hpl.sequence as sequence,
		sum(hpl.total) as total,
		hpl.code as code,
		min(hpl.name) as name,
		min(sr.cod_sunat) as cod_sunat,
		min(hsrc.is_ing_or_desc) as is_ing_or_desc
		from hr_payslip hp
		inner join hr_payslip_line hpl on hp.id=hpl.slip_id
		inner join hr_salary_rule as sr on sr.code = hpl.code
		inner join hr_employee e on e.id = hpl.employee_id
		inner join hr_salary_rule_category hsrc on hsrc.id = hpl.category_id
		where date_from ='%s'
			and  date_to='%s'
			and e.identification_id='%s'
			and hpl.code='%s'
			and hpl.contract_id in (%s)
		group by e.id,hpl.sequence,hpl.code
		order by e.id,hpl.sequence
		""" % (date_start, date_end, empleado.identification_id,
				planilla_ajustes.cod_neto_pagar.code if planilla_ajustes else '',
				','.join(str(payslip) for payslip in payslips.mapped('contract_id.id'))
				)

		self.env.cr.execute(query_neto_pagar)
		neto_pagar = self.env.cr.dictfetchone()

		detalle_trabajador.append([Paragraph(neto_pagar['name'].title() if neto_pagar else '', style_cell_left), '', '', '', '', '', '', Paragraph('{0:.2f}'.format(neto_pagar['total']) if neto_pagar else '', style_cell_right)])

		positions_in_tables.append(('SPAN', (0, i), (6, i)))
		positions_in_tables.append(('BACKGROUND', (0, i), (7, i), colorHeader))
		i = i+1

		data = [
			[Paragraph('Código', style_cell), Paragraph('Conceptos', style_cell), '', '', '', Paragraph(
				'Ingresos S/.', style_cell), Paragraph('Descuentos S/.', style_cell), Paragraph('Neto S/.', style_cell)],
		]+detalle_trabajador  # +[['1', '2', '3', '4', '5', '6', '7', '8']]

		t = Table(data, style=[
			('SPAN', (1, 0), (4, 0)),  # cabecera

			('BACKGROUND', (0, 0), (7, 0), colorHeader),  # fin linea 3

			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (7, 0), 'BOTTOM'),
			('GRID', (0, 0), (7, 0), 0.5, colors.black),
			('BOX', (0, 0), (-1, -1), 0.5, colors.black),
			('LEFTPADDING', (0, 0), (-1, -1), 1),
			('RIGHTPADDING', (0, 0), (-1, -1), 1),
			('BOTTOMPADDING', (0, 0), (-1, -1), 1),
			('TOPPADDING', (0, 0), (-1, -1), 1),
		]+positions_in_tables)
		t._argW[3] = 1.5*inch
		elements.append(t)
		elements.append(Spacer(1, 10))

		i = 0

		detalle_trabajador = []
		positions_in_tables = []
		category = categories[len(categories)-1]
		reglas_salariales_empleado = """
		select
		max(e.name_related) as name_related,
		max(e.identification_id) as identification_id,
		max(hpl.sequence) as sequence,
		sum(hpl.total) as total,
		max(hpl.code) as code,
		max(hpl.name) as name,
		max(sr.cod_sunat) as cod_sunat,
		max(hsrc.is_ing_or_desc) as is_ing_or_desc
		from hr_payslip hp
		inner join hr_payslip_line hpl on hp.id=hpl.slip_id
		inner join hr_salary_rule as sr on sr.code = hpl.code
		inner join hr_employee e on e.id = hpl.employee_id
		inner join hr_salary_rule_category hsrc
		on hsrc.id = hpl.category_id
		where date_from ='%s' and  date_to='%s' and e.identification_id='%s'
		and hpl.appears_on_payslip='t' and sr.appears_on_payslip='t' and hpl.category_id=%d  and  hpl.total>0
		and hpl.contract_id in (%s)
		group by e.id,hpl.sequence
		order by e.id,hpl.sequence
		""" % (date_start, date_end, empleado.identification_id, category.id,
			','.join(str(payslip) for payslip in payslips.mapped('contract_id.id')))


		self.env.cr.execute(reglas_salariales_empleado)
		reglas_salariales_list = self.env.cr.dictfetchall()

		# if len(reglas_salariales_list) > 0:
		detalle_trabajador.append([Paragraph(category.name.title(), style_cell_left), '', '', '', '', '', '', ''])
		positions_in_tables.append(('SPAN', (0, i), (7, i)))
		positions_in_tables.append(
			('BACKGROUND', (0, i), (7, i), colorHeader))
		i = i+1

		for regla_salarial in reglas_salariales_list:
			if regla_salarial['code'] != 'ESSALUD':
				cod_sunat = Paragraph(regla_salarial['cod_sunat'] if regla_salarial['cod_sunat'] else '', style_cell_left)
				namee = Paragraph(regla_salarial['name'] if regla_salarial['name'] else '', style_cell_left)
				total = Paragraph('{0:.2f}'.format(regla_salarial['total'] if regla_salarial['total'] else ''), style_cell_right)
				detalle_trabajador.append([cod_sunat, namee, '', '', '', total, '', ''] if regla_salarial['is_ing_or_desc'] == 'ingreso' else [cod_sunat, namee, '', '', '', '', '', total])
				positions_in_tables.append(('SPAN', (1, i), (4, i)))
				i = i+1

		essalud = 0
		for payslip in payslips:
			essalud += payslip.essalud
		if essalud > 0:
			detalle_trabajador.append(['',Paragraph('Aportes ESSALUD',style_cell_left),'','','','','',Paragraph('{0:.2f}'.format(essalud), style_cell_right)])
			positions_in_tables.append(('SPAN', (1, i), (4, i)))

		descansos_ids = self.env['breaks.line.bl'].search([('employee_id', '=', payslips[0].employee_id.id), ('period', '=', payslips[0].payslip_run_id.id)])
		if payslips[0].periodos_devengue or descansos_ids or payslips[0].fault_ids:
			detalle_vacaciones = []
			elements.append(Table([[Paragraph("Vacaciones, Descansos y Faltas", style_cell_bold)]], style=[
				('BACKGROUND', (0, 0), (7, 0), colorHeader),
				('BOX', (0, 0), (-1, -1), 0.5, colors.black),
				('ALIGN', (0, 0), (-1, -1), 'CENTER')
			],hAlign='LEFT'))

			detalle_vacaciones.append([Paragraph("Tipo", style_cell_left), Paragraph("Fecha de Inicio", style_cell_right), Paragraph("Fecha de Fin", style_cell_right), Paragraph("Días", style_cell_right),])
			for i in payslips[0].periodos_devengue:
				tipo = Paragraph("Vacaciones", style_cell_left)
				date_start = Paragraph(str(i.date_start), style_cell_right)
				date_end = Paragraph(str(i.date_end), style_cell_right)
				dias = Paragraph(str(i.dias), style_cell_right)
				detalle_vacaciones.append([tipo, date_start, date_end, dias,])

			for i in descansos_ids:
				tipo = Paragraph(dict(i._fields['type'].selection).get(i.type), style_cell_left)
				date_start = Paragraph(str(i.date_start), style_cell_right)
				date_end = Paragraph(str(i.date_end), style_cell_right)
				dias = Paragraph(str(i.days_total), style_cell_right)
				detalle_vacaciones.append([tipo, date_start, date_end, dias,])

			for i in payslips[0].fault_ids:
				tipo = Paragraph("Faltas", style_cell_left)
				date_start = Paragraph(str(i.date_start), style_cell_right)
				date_end = Paragraph(str(i.date_end), style_cell_right)
				dias = Paragraph(str(i.days), style_cell_right)
				detalle_vacaciones.append([tipo, date_start, date_end, dias,])

			t = Table(detalle_vacaciones, style=[
				('BACKGROUND', (0, 0), (7, 0), colorHeader),
				('BOX', (0, 0), (-1, -1), 0.5, colors.black),
				('GRID', (0, 0), (7, 0), 0.5, colors.black),
				('ALIGN', (0, 0), (-1, -1), 'CENTER')
			],hAlign='LEFT')
			elements.append(t)
			elements.append(Spacer(1, 10))

		data = detalle_trabajador

		t = Table(data, style=[
			('SPAN', (1, 0), (4, 0)),  # cabecera
			('BACKGROUND', (0, 0), (7, 0), colorHeader),  # fin linea 3
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (7, 0), 'BOTTOM'),
			('BOX', (0, 0), (-1, -1), 0.5, colors.black),
			('GRID', (0, 0), (7, 0), 0.5, colors.black),
			('LEFTPADDING', (0, 0), (-1, -1), 1),
			('RIGHTPADDING', (0, 0), (-1, -1), 1),
			('BOTTOMPADDING', (0, 0), (-1, -1), 1),
			('TOPPADDING', (0, 0), (-1, -1), 1),
		]+positions_in_tables)
		t._argW[3] = 1.5*inch
		elements.append(t)
		try:
			firma_digital = open(ruta+"firma.jpg","rb")
			c = Image(firma_digital,2*inch,1*inch)
		except Exception as e:
			c = ''
			print("No se encontro la firma en la ruta "+ ruta +" Inserte una imagen de la firma en la ruta especificada con el nombre 'firma.jpg'")
		finally:
			data = [
				[' ', ' ',  ' ', ' ', ' ', ' ', ' ', c , ' '],
				['  ', 'FIRMA TRABAJADOR', ' ', '  ', ' ',
				 ' ', '  ', 'FIRMA EMPLEADOR', '  ']
			]

			t = Table(data, style=[
				('ALIGN', (0, 0), (-1, -1), 'CENTER'),
				('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),

				('LINEABOVE', (0, -1), (2, -1), 1, colors.black),
				('LINEABOVE', (6, -1), (8, -1), 1, colors.black),
			])
			t._argW[3] = 1.5*inch
			elements.append(t)

			elements.append(PageBreak())
			return elements
