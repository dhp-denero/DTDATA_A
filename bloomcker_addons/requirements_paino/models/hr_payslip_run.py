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
				res = {
					'employee_id': contract.employee_id.id,
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
