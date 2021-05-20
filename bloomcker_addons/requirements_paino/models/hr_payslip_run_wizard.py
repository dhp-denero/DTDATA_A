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


class hrpaysliprunwizard(models.TransientModel):
	_name = "hr.payslip.run.wizard"

	tipo = fields.Selection([('no practicante', 'Empleado'), ('practicante', 'Practicante')], required=True, index=True, default='no practicante')

	@api.multi
	def do_rebuild(self):
		payslip_run = self.env['hr.payslip.run'].search(
			[('id', '=', self.env.context['current_id'])],limit=1)
		output = io.BytesIO()
		# workbook = Workbook('planilla_plame.xls')

		planilla_ajustes = self.env['planilla.ajustes'].search([], limit=1)
		try:
			ruta = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		docname = ruta+'0601%s%s%s.rem' % (
			payslip_run.date_end[:4], payslip_run.date_end[5:7], planilla_ajustes.ruc if planilla_ajustes else '')

		f = open(docname, "w+")
		employees = []

		if self.tipo == 'practicante':
			for payslip in payslip_run.slip_ids.filtered(lambda s: s.contract_id.regimen_laboral_empresa == 'practicante'):
				if payslip.employee_id.id not in employees:
					query_vista = """
						select
						min(ptd.codigo_sunat) as tipo_doc,
						e.identification_id as dni,
						sr.cod_sunat as sunat,
						sum(hpl.total) as monto_devengado,
						sum(hpl.total) as monto_pagado
						from hr_payslip_run hpr
						inner join hr_payslip hp on hpr.id= hp.payslip_run_id
						inner join hr_payslip_line hpl on hp.id=hpl.slip_id
						inner join hr_salary_rule as sr on sr.code = hpl.code
						inner join hr_employee e on e.id = hpl.employee_id
						inner join hr_contract hc on hc.id = hp.contract_id
						inner join hr_salary_rule_category hsrc on hsrc.id = hpl.category_id
						left join planilla_tipo_documento ptd on ptd.id = e.tablas_tipo_documento_id
						where hpr.id = %d
						and e.id = %d
						and sr.cod_sunat != ''
						and hpl.appears_on_payslip = 't'
						group by sr.cod_sunat,e.identification_id
						order by sr.cod_sunat""" % (payslip_run.id,payslip.employee_id.id)
					self.env.cr.execute(query_vista)
					data = self.env.cr.dictfetchall()
					for line in data:
						f.write("%s|%s|%s|\r\n"%(
								line['tipo_doc'],
								line['dni'],
								line['monto_devengado']
								))
				employees.append(payslip.employee_id.id)
			f.close()
			f = open(docname,'rb')
			vals = {
				'output_name': '0601%s%s%s.for' % (
				payslip_run.date_end[:4], payslip_run.date_end[5:7], planilla_ajustes.ruc if planilla_ajustes else ''),
				'output_file': base64.encodestring(''.join(f.readlines())),
			}
			sfs_id = self.env['planilla.export.file'].create(vals)

			#os.remove(docname)

			return {
				"type": "ir.actions.act_window",
				"res_model": "planilla.export.file",
				"views": [[False, "form"]],
				"res_id": sfs_id.id,
				"target": "new",
			}
		else:
			for payslip in payslip_run.slip_ids.filtered(lambda s: s.contract_id.regimen_laboral_empresa != 'practicante'):
				if payslip.employee_id.id not in employees:
					query_vista = """
						select
						min(ptd.codigo_sunat) as tipo_doc,
						e.identification_id as dni,
						sr.cod_sunat as sunat,
						sum(hpl.total) as monto_devengado,
						sum(hpl.total) as monto_pagado
						from hr_payslip_run hpr
						inner join hr_payslip hp on hpr.id= hp.payslip_run_id
						inner join hr_payslip_line hpl on hp.id=hpl.slip_id
						inner join hr_salary_rule as sr on sr.code = hpl.code
						inner join hr_employee e on e.id = hpl.employee_id
						inner join hr_salary_rule_category hsrc on hsrc.id = hpl.category_id
						left join planilla_tipo_documento ptd on ptd.id = e.tablas_tipo_documento_id
						where hpr.id = %d
						and e.id = %d
						and sr.cod_sunat != ''
						and hpl.appears_on_payslip = 't'
						group by sr.cod_sunat,e.identification_id
						order by sr.cod_sunat""" % (payslip_run.id,payslip.employee_id.id)
					self.env.cr.execute(query_vista)
					data = self.env.cr.dictfetchall()
					for line in data:
						f.write("%s|%s|%s|%s|%s|\r\n"%(
								line['tipo_doc'],
								line['dni'],
								line['sunat'],
								line['monto_devengado'],
								line['monto_pagado']
								))
				employees.append(payslip.employee_id.id)
			f.close()
			f = open(docname,'rb')
			vals = {
				'output_name': '0601%s%s%s.rem' % (
				payslip_run.date_end[:4], payslip_run.date_end[5:7], planilla_ajustes.ruc if planilla_ajustes else ''),
				'output_file': base64.encodestring(''.join(f.readlines())),
			}
			sfs_id = self.env['planilla.export.file'].create(vals)

			#os.remove(docname)

			return {
				"type": "ir.actions.act_window",
				"res_model": "planilla.export.file",
				"views": [[False, "form"]],
				"res_id": sfs_id.id,
				"target": "new",
			}
