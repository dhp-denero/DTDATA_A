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


class WizardPlanilla(models.TransientModel):
	_name = "wizard.form.planilla"
	_description = "Current Planilla Report"

	tipo = fields.Selection([('no practicante', 'no practicante'), ('practicante', 'practicante')], required=True, index=True, default='practicante')


	@api.multi
	def do_rebuild(self,default):
		payslip = self.env['hr.payslip.run'].browse(int(default.get('default_planilla')))
		self.env['planilla.planilla.tabular.wizard'].reconstruye_tabla(payslip.date_start,payslip.date_end)
		try:
			direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		workbook = Workbook(direccion+'planilla_tabular.xls')
		worksheet = workbook.add_worksheet(
			str(payslip.id)+'-'+payslip.date_start+'-'+payslip.date_end)
		worksheet.set_landscape()  # Horizontal
		worksheet.set_paper(9)  # A-4
		worksheet.set_margins(left=0.75, right=0.75, top=1, bottom=1)
		worksheet.fit_to_pages(1, 0)  # Ajustar por Columna

		fontSize = 8
		bold = workbook.add_format(
			{'bold': True, 'font_name': 'Arial', 'font_size': fontSize})
		normal = workbook.add_format()
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
		formatLeftColor = workbook.add_format(
			{'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'bg_color': '#99CCFF', 'font_size': fontSize})
		styleFooterSum = workbook.add_format(
			{'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'right', 'font_size': fontSize, 'top': 1, 'bottom': 2})
		styleFooterSum.set_bottom(6)
		numberdos.set_font_size(fontSize)
		bord = workbook.add_format()
		bord.set_border(style=1)
		bord.set_text_wrap()
		# numberdos.set_border(style=1)

		title = workbook.add_format({'bold': True, 'font_name': 'Arial'})
		title.set_align('center')
		title.set_align('vcenter')
		# title.set_text_wrap()
		title.set_font_size(18)
		company = self.env['res.company'].search([], limit=1)[0]

		x = 0

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		worksheet.merge_range(
			'D1:O1', u"PLANILLA DE SUELDOS Y SALARIOS", title)
		worksheet.set_row(x, 29)
		x = x+2

		worksheet.write(x, 0, u"Empresa:", bold)
		worksheet.write(x, 1, company.name, formatLeft)

		x = x+1
		worksheet.write(x, 0, u"Mes:", bold)
		worksheet.write(
			x, 1, payslip.get_mes(int(payslip.date_end[5:7]) if payslip.date_end else 0).upper()+"-"+payslip.date_end[:4], formatLeft)


		worksheet.write(x+1, 0, u"Tipo:", bold)
		worksheet.write(x+1, 1, self.tipo, formatLeft)

		x = x+3

		worksheet.set_row(x, 50)

		if self.tipo == 'practicante':
			array_payslip = payslip.slip_ids.filtered(lambda t: t.contract_id.regimen_laboral_empresa == 'practicante')
		else:
			array_payslip = payslip.slip_ids.filtered(lambda t: t.contract_id.regimen_laboral_empresa not in 'practicante')

		worksheet.write(x,0, u"EMPLEADO", boldbord)
		worksheet.write(x,1, u"DNI", boldbord)
		worksheet.write(x,2, u"AFILIACION", boldbord)
		worksheet.write(x,5,u"CTA. ANALÍTICA",boldbord)

		for k in range(len(array_payslip[0].line_ids)):
			worksheet.write(x,int(k+6), array_payslip[0].line_ids[k].name, boldbord)

		x = x+1
		i = 7
		array_sum =[]
		array_sum = [0 for r in range(len(array_payslip[0].line_ids))]

		for slip in array_payslip:
			worksheet.write(i,0,slip.employee_id.name_total,formatLeft)
			worksheet.write(i,1,slip.employee_id.identification_id,formatLeft)
			worksheet.write(i,2,slip.contract_id.afiliacion_id.entidad,formatLeft)
			worksheet.write(i,5,slip.employee_id.department_id.name if slip.employee_id.department_id.name else '',formatLeft)

			for j in range(len(slip.line_ids)):
				array_sum[j] += slip.line_ids[j].total
				worksheet.write(i,int(j+6),slip.line_ids[j].total,formatLeft)


			# suma1+=slip.line_ids[1].total
			i+=1

		i+=1
		for a in range(len(array_payslip[0].line_ids)):
			worksheet.write(i,int(a+6), array_sum[a], styleFooterSum)


		# range_row = len(datos_planila[0] if len(datos_planilla) > 0 else 0)
		# total_essalud = 0
		# for i in range(len(datos_planilla)):
		# 	for j in range(range_row):
		# 		if j not in (3,4):
		# 			if j == 0 or j == 1:
		# 				worksheet.write(x, j, datos_planilla[i][j] if datos_planilla[i][j] else '0.00', formatLeft)
		# 			else:
		# 				worksheet.write(x, j, datos_planilla[i][j] if datos_planilla[i][j] else '0.00', numberdos)
		# 	essalud = self.env['hr.payslip'].browse(datos_planilla[i][4]).essalud
		# 	worksheet.write(x,j+1,essalud,formatLeft)
		# 	total_essalud += essalud
		# 	x = x+1
		# x = x + 1
		# datos_planilla_transpuesta = zip(*datos_planilla)
		#
		# for j in range(5, len(datos_planilla_transpuesta)):
		# 	worksheet.write(x, j, sum([float(d) for d in datos_planilla_transpuesta[j]]), styleFooterSum)
		#
		# worksheet.write(x,j+1,total_essalud,styleFooterSum)

		# seteando tamaño de columnas
		worksheet.set_column(0, 0, 30)
		worksheet.set_column(1, 1, 20)
		worksheet.set_column(2, 2, 30)
		worksheet.set_column(5, 5, 30)
		# for i in range(2, len(col_widths)):
		# 	worksheet.set_column(i, i, col_widths[i])

		worksheet.set_column('D:D',None,None,{'hidden':True})
		worksheet.set_column('E:E',None,None,{'hidden':True})

		workbook.close()

		f = open(direccion+'planilla_tabular.xls', 'rb')

		vals = {
			'output_name': 'planilla_tabular.xls',
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
