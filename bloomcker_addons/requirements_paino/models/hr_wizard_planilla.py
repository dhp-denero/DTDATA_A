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

		header_planilla_tabular = self.env['ir.model.fields'].search(
			[('name', 'like', 'x_%'), ('model', '=', 'planilla.tabular')], order="create_date")
		worksheet.write(x, 0, header_planilla_tabular[0].field_description, formatLeftColor)
		for i in range(1, len(header_planilla_tabular)):
			if i not in (3,4):
				worksheet.write(x, i, header_planilla_tabular[i].field_description, boldbord)
		worksheet.write(x,i+1,'Aportes ESSALUD',boldbord)
		worksheet.set_row(x, 50)

		fields = ['\"'+column.name+'\"' for column in header_planilla_tabular]
		x = x+1

		if self.tipo == 'practicante':
			array_payslip = payslip.slip_ids.filtered(lambda t: t.contract_id.regimen_laboral_empresa == 'practicante')
		else:
			array_payslip = payslip.slip_ids.filtered(lambda t: t.contract_id.regimen_laboral_empresa not in 'practicante')

		i = 7
		suma1=0
		suma2=0
		suma3=0
		suma4=0
		suma5=0
		suma6=0
		suma7=0
		suma8=0
		suma9=0
		suma10=0
		suma11=0
		suma12=0
		suma13=0
		suma14=0
		suma15=0
		suma16=0
		suma17=0
		suma18=0
		suma19=0
		suma20=0
		suma21=0
		suma22=0
		suma23=0
		suma24=0
		suma25=0
		suma26=0
		suma27=0
		suma28=0
		suma29=0
		suma30=0
		suma31=0
		suma32=0
		suma33=0
		suma34=0
		suma35=0
		suma36=0
		suma37=0
		suma38=0
		suma39=0
		suma40=0
		suma41=0
		suma42=0
		suma43=0
		suma44=0
		suma45=0
		suma46=0
		suma47=0
		suma48=0
		suma49=0
		suma50=0
		suma51=0
		suma52=0
		suma53=0
		suma54=0
		suma55=0
		suma56=0
		suma57=0
		suma58=0
		suma59=0
		suma60=0
		suma61=0
		suma62=0
		suma63=0
		suma64=0
		suma65=0
		suma66=0
		suma67=0
		suma68=0
		suma69=0
		suma70=0


		for slip in array_payslip:
			worksheet.write(i,0,slip.employee_id.name_total,formatLeft)
			worksheet.write(i,1,slip.employee_id.identification_id,formatLeft)
			worksheet.write(i,2,slip.contract_id.afiliacion_id.entidad,formatLeft)
			worksheet.write(i,5,slip.employee_id.department_id.name if slip.employee_id.department_id.name else '',formatLeft)

			worksheet.write(i,6,slip.line_ids[1].total,formatLeft)
			worksheet.write(i,7,slip.line_ids[2].total,formatLeft)
			worksheet.write(i,8,slip.line_ids[3].total,formatLeft)
			worksheet.write(i,9,slip.line_ids[4].total,formatLeft)
			worksheet.write(i,10,slip.line_ids[5].total,formatLeft)
			worksheet.write(i,11,slip.line_ids[6].total,formatLeft)
			worksheet.write(i,12,slip.line_ids[7].total,formatLeft)
			worksheet.write(i,13,slip.line_ids[9].total,formatLeft)
			worksheet.write(i,14,slip.line_ids[10].total,formatLeft)
			worksheet.write(i,15,slip.line_ids[11].total,formatLeft)
			worksheet.write(i,16,slip.line_ids[12].total,formatLeft)
			worksheet.write(i,17,slip.line_ids[13].total,formatLeft)
			worksheet.write(i,18,slip.line_ids[14].total,formatLeft)
			worksheet.write(i,19,slip.line_ids[15].total,formatLeft)
			worksheet.write(i,20,slip.line_ids[16].total,formatLeft)
			worksheet.write(i,21,slip.line_ids[17].total,formatLeft)
			worksheet.write(i,22,slip.line_ids[18].total,formatLeft)
			worksheet.write(i,23,slip.line_ids[19].total,formatLeft)
			worksheet.write(i,24,slip.line_ids[20].total,formatLeft)
			worksheet.write(i,25,slip.line_ids[21].total,formatLeft)
			worksheet.write(i,26,slip.line_ids[22].total,formatLeft)
			worksheet.write(i,27,slip.line_ids[23].total,formatLeft)
			worksheet.write(i,28,slip.line_ids[24].total,formatLeft)
			worksheet.write(i,29,slip.line_ids[25].total,formatLeft)
			worksheet.write(i,30,slip.line_ids[26].total,formatLeft)
			worksheet.write(i,31,slip.line_ids[27].total,formatLeft)
			worksheet.write(i,32,slip.line_ids[28].total,formatLeft)
			worksheet.write(i,33,slip.line_ids[29].total,formatLeft)
			worksheet.write(i,34,slip.line_ids[30].total,formatLeft)
			worksheet.write(i,35,slip.line_ids[31].total,formatLeft)
			worksheet.write(i,36,slip.line_ids[32].total,formatLeft)
			worksheet.write(i,37,slip.line_ids[35].total,formatLeft)
			worksheet.write(i,38,slip.line_ids[36].total,formatLeft)
			worksheet.write(i,39,slip.line_ids[37].total,formatLeft)
			worksheet.write(i,40,slip.line_ids[38].total,formatLeft)
			worksheet.write(i,41,slip.line_ids[39].total,formatLeft)
			worksheet.write(i,42,slip.line_ids[42].total,formatLeft)
			worksheet.write(i,43,slip.line_ids[43].total,formatLeft)
			worksheet.write(i,44,slip.line_ids[44].total,formatLeft)
			worksheet.write(i,45,slip.line_ids[45].total,formatLeft)
			worksheet.write(i,46,slip.line_ids[46].total,formatLeft)
			worksheet.write(i,47,slip.line_ids[47].total,formatLeft)
			worksheet.write(i,48,slip.line_ids[48].total,formatLeft)
			worksheet.write(i,49,slip.line_ids[49].total,formatLeft)
			worksheet.write(i,50,slip.line_ids[50].total,formatLeft)
			worksheet.write(i,51,slip.line_ids[51].total,formatLeft)
			worksheet.write(i,52,slip.line_ids[53].total,formatLeft)
			worksheet.write(i,53,slip.line_ids[54].total,formatLeft)
			worksheet.write(i,54,slip.line_ids[55].total,formatLeft)
			worksheet.write(i,55,slip.line_ids[56].total,formatLeft)
			worksheet.write(i,56,slip.line_ids[57].total,formatLeft)
			worksheet.write(i,57,slip.line_ids[58].total,formatLeft)
			worksheet.write(i,58,slip.line_ids[59].total,formatLeft)
			worksheet.write(i,59,slip.line_ids[60].total,formatLeft)
			worksheet.write(i,60,slip.line_ids[61].total,formatLeft)
			worksheet.write(i,61,slip.line_ids[62].total,formatLeft)
			worksheet.write(i,62,slip.line_ids[63].total,formatLeft)
			worksheet.write(i,63,slip.line_ids[64].total,formatLeft)
			worksheet.write(i,64,slip.line_ids[65].total,formatLeft)
			worksheet.write(i,65,slip.line_ids[66].total,formatLeft)
			worksheet.write(i,66,slip.line_ids[67].total,formatLeft)
			worksheet.write(i,67,slip.line_ids[68].total,formatLeft)
			worksheet.write(i,68,slip.line_ids[69].total,formatLeft)
			worksheet.write(i,69,slip.line_ids[70].total,formatLeft)
			worksheet.write(i,70,slip.line_ids[71].total,formatLeft)
			worksheet.write(i,71,slip.line_ids[73].total,formatLeft)
			worksheet.write(i,72,slip.line_ids[74].total,formatLeft)
			worksheet.write(i,73,slip.line_ids[75].total,formatLeft)
			worksheet.write(i,74,slip.line_ids[76].total,formatLeft)

			suma1+=slip.line_ids[1].total
			suma2+=slip.line_ids[2].total
			suma3+=slip.line_ids[3].total
			suma4+=slip.line_ids[4].total
			suma5+=slip.line_ids[5].total
			suma6+=slip.line_ids[6].total
			suma7+=slip.line_ids[7].total
			suma8+=slip.line_ids[9].total
			suma9+=slip.line_ids[10].total
			suma10+=slip.line_ids[11].total
			suma11+=slip.line_ids[12].total
			suma12+=slip.line_ids[13].total
			suma13+=slip.line_ids[14].total
			suma14+=slip.line_ids[15].total
			suma15+=slip.line_ids[16].total
			suma16+=slip.line_ids[17].total
			suma17+=slip.line_ids[18].total
			suma18+=slip.line_ids[19].total
			suma19+=slip.line_ids[20].total
			suma20+=slip.line_ids[21].total
			suma21+=slip.line_ids[22].total
			suma22+=slip.line_ids[23].total
			suma23+=slip.line_ids[24].total
			suma24+=slip.line_ids[25].total
			suma25+=slip.line_ids[26].total
			suma26+=slip.line_ids[27].total
			suma27+=slip.line_ids[28].total
			suma28+=slip.line_ids[29].total
			suma29+=slip.line_ids[30].total
			suma30+=slip.line_ids[31].total
			suma31+=slip.line_ids[32].total
			suma32+=slip.line_ids[35].total
			suma33+=slip.line_ids[36].total
			suma34+=slip.line_ids[37].total
			suma35+=slip.line_ids[38].total
			suma36+=slip.line_ids[39].total
			suma37+=slip.line_ids[42].total
			suma38+=slip.line_ids[43].total
			suma39+=slip.line_ids[44].total
			suma40+=slip.line_ids[45].total
			suma41+=slip.line_ids[46].total
			suma42+=slip.line_ids[47].total
			suma43+=slip.line_ids[48].total
			suma44+=slip.line_ids[49].total
			suma45+=slip.line_ids[50].total
			suma46+=slip.line_ids[51].total
			suma47+=slip.line_ids[53].total
			suma48+=slip.line_ids[54].total
			suma49+=slip.line_ids[55].total
			suma50+=slip.line_ids[56].total
			suma51+=slip.line_ids[57].total
			suma52+=slip.line_ids[58].total
			suma53+=slip.line_ids[59].total
			suma54+=slip.line_ids[60].total
			suma55+=slip.line_ids[61].total
			suma56+=slip.line_ids[62].total
			suma57+=slip.line_ids[63].total
			suma58+=slip.line_ids[64].total
			suma59+=slip.line_ids[65].total
			suma60+=slip.line_ids[66].total
			suma61+=slip.line_ids[67].total
			suma62+=slip.line_ids[68].total
			suma63+=slip.line_ids[69].total
			suma64+=slip.line_ids[70].total
			suma65+=slip.line_ids[71].total
			suma66+=slip.line_ids[73].total
			suma67+=slip.line_ids[74].total
			suma68+=slip.line_ids[75].total
			suma69+=slip.line_ids[76].total
			i+=1

		i+=1
		worksheet.write(i,6,suma1,styleFooterSum)
		worksheet.write(i,7,suma2,styleFooterSum)
		worksheet.write(i,8,suma3,styleFooterSum)
		worksheet.write(i,9,suma4,styleFooterSum)
		worksheet.write(i,10,suma5,styleFooterSum)
		worksheet.write(i,11,suma6,styleFooterSum)
		worksheet.write(i,12,suma7,styleFooterSum)
		worksheet.write(i,13,suma8,styleFooterSum)
		worksheet.write(i,14,suma9,styleFooterSum)
		worksheet.write(i,15,suma10,styleFooterSum)
		worksheet.write(i,16,suma11,styleFooterSum)
		worksheet.write(i,17,suma12,styleFooterSum)
		worksheet.write(i,18,suma13,styleFooterSum)
		worksheet.write(i,19,suma14,styleFooterSum)
		worksheet.write(i,20,suma15,styleFooterSum)
		worksheet.write(i,21,suma16,styleFooterSum)
		worksheet.write(i,22,suma17,styleFooterSum)
		worksheet.write(i,23,suma18,styleFooterSum)
		worksheet.write(i,24,suma19,styleFooterSum)
		worksheet.write(i,25,suma20,styleFooterSum)
		worksheet.write(i,26,suma21,styleFooterSum)
		worksheet.write(i,27,suma22,styleFooterSum)
		worksheet.write(i,28,suma23,styleFooterSum)
		worksheet.write(i,29,suma24,styleFooterSum)
		worksheet.write(i,30,suma25,styleFooterSum)
		worksheet.write(i,31,suma26,styleFooterSum)
		worksheet.write(i,32,suma27,styleFooterSum)
		worksheet.write(i,33,suma28,styleFooterSum)
		worksheet.write(i,34,suma29,styleFooterSum)
		worksheet.write(i,35,suma30,styleFooterSum)
		worksheet.write(i,36,suma31,styleFooterSum)
		worksheet.write(i,37,suma32,styleFooterSum)
		worksheet.write(i,38,suma33,styleFooterSum)
		worksheet.write(i,39,suma34,styleFooterSum)
		worksheet.write(i,40,suma35,styleFooterSum)
		worksheet.write(i,41,suma36,styleFooterSum)
		worksheet.write(i,42,suma37,styleFooterSum)
		worksheet.write(i,43,suma38,styleFooterSum)
		worksheet.write(i,44,suma39,styleFooterSum)
		worksheet.write(i,45,suma40,styleFooterSum)
		worksheet.write(i,46,suma41,styleFooterSum)
		worksheet.write(i,47,suma42,styleFooterSum)
		worksheet.write(i,48,suma43,styleFooterSum)
		worksheet.write(i,49,suma44,styleFooterSum)
		worksheet.write(i,50,suma45,styleFooterSum)
		worksheet.write(i,51,suma46,styleFooterSum)
		worksheet.write(i,52,suma47,styleFooterSum)
		worksheet.write(i,53,suma48,styleFooterSum)
		worksheet.write(i,54,suma49,styleFooterSum)
		worksheet.write(i,55,suma50,styleFooterSum)
		worksheet.write(i,56,suma51,styleFooterSum)
		worksheet.write(i,57,suma52,styleFooterSum)
		worksheet.write(i,58,suma53,styleFooterSum)
		worksheet.write(i,59,suma54,styleFooterSum)
		worksheet.write(i,60,suma55,styleFooterSum)
		worksheet.write(i,61,suma56,styleFooterSum)
		worksheet.write(i,62,suma57,styleFooterSum)
		worksheet.write(i,63,suma58,styleFooterSum)
		worksheet.write(i,64,suma59,styleFooterSum)
		worksheet.write(i,65,suma60,styleFooterSum)
		worksheet.write(i,66,suma61,styleFooterSum)
		worksheet.write(i,67,suma62,styleFooterSum)
		worksheet.write(i,68,suma63,styleFooterSum)
		worksheet.write(i,69,suma64,styleFooterSum)
		worksheet.write(i,70,suma65,styleFooterSum)
		worksheet.write(i,71,suma66,styleFooterSum)
		worksheet.write(i,72,suma67,styleFooterSum)
		worksheet.write(i,73,suma68,styleFooterSum)
		worksheet.write(i,74,suma69,styleFooterSum)
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
		worksheet.write(6,5,u"CTA. ANALÍTICA",boldbord)
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
