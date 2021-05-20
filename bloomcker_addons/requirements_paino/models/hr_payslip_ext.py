import time
from datetime import datetime, timedelta
from dateutil import relativedelta
from xml.etree.ElementTree import ElementTree
import babel

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from decimal import *
from math import modf
import logging
_logger = logging.getLogger(__name__)


class HrPayslipExtend(models.Model):
	_inherit = 'hr.payslip'
	_description = 'Pay Slip Extend'

	@api.multi
	def imprimir_boleta_xml(self):
		_logger.info('imprimir_xml')
		self.ensure_one()
		dias_no_laborados,dias_laborados,first,second,dias_faltas = 0,0,0,0,0
		payslips = self.env['hr.payslip'].search([('payslip_run_id','=',self.payslip_run_id.id),('employee_id','=',self.employee_id.id)])
		planilla_ajustes = self.env['planilla.ajustes'].search([], limit=1)
		try:
			ruta = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		archivo_pdf = SimpleDocTemplate(
			ruta+"planilla_tmp.xml", pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20)

		elements = []
		company = self.env['res.company'].search([], limit=1)
		categories = self.env['hr.salary.rule.category'].search(
			[('aparece_en_nomina', '=', True)], order="secuencia")

		for payslip in payslips:
			dias_no_laborados += int(payslip.worked_days_line_ids.search([('code', '=', planilla_ajustes.cod_dias_no_laborados.codigo if planilla_ajustes else ''),
																		('payslip_id', '=', payslip.id)], limit=1).number_of_days)
		for payslip in payslips:
			if not payslip.contract_id.hourly_worker:
				dias_laborados += int(payslip.worked_days_line_ids.search([('code', '=', planilla_ajustes.cod_dias_laborados.codigo if len(planilla_ajustes) > 0 else ''),
																	('payslip_id', '=', payslip.id)], limit=1).number_of_days)
		dias_laborados=dias_laborados-self.feriados if dias_laborados > 0 else 0
		if not planilla_ajustes.cod_dias_subsidiados:
			raise UserError('Falta configurar codigos de dias subsidiados en Parametros de Boleta.')
		wd_codes = planilla_ajustes.cod_dias_subsidiados.mapped('codigo')
		dias_subsidiados = 0
		for payslip in payslips:
			wds = filter(lambda l:l.code in wd_codes and l.payslip_id == payslip,payslip.worked_days_line_ids)
			dias_subsidiados += sum([int(i.number_of_days) for i in wds])

		query_horas_sobretiempo = '''
		select sum(number_of_days) as dias ,sum(number_of_hours) as horas ,sum(minutos) as minutos from hr_payslip_worked_days
		where (code = 'HE25' OR code = 'HE35' or code = 'HE100')
		and payslip_id in (%s)
		''' % (','.join(str(i) for i in payslips.mapped('id')))

		self.env.cr.execute(query_horas_sobretiempo)
		# str(int(self.env.cr.dictfetchone()['horas']))
		total_sobretiempo = self.env.cr.dictfetchone()
		for payslip in payslips:
			dias_faltas += self.env['hr.payslip.worked_days'].search([('code', '=', planilla_ajustes.cod_dias_no_laborados.codigo if planilla_ajustes else ''),
																	('payslip_id', '=', payslip.id)], limit=1).number_of_days
		if self.employee_id.calendar_id:
			total = self.employee_id.calendar_id.average_hours if self.employee_id.calendar_id.average_hours > 0 else 8
		else:
			total = 8
			#raise UserError(u'Este empleado no tiene un Horario establecido.')
		total_horas_jornada_ordinaria = 0
		for payslip in payslips:
			if payslip.contract_id.hourly_worker:
				total_horas_jornada_ordinaria += sum(payslip.worked_days_line_ids.filtered(lambda l:l.code == planilla_ajustes.cod_dias_laborados.codigo).mapped('number_of_hours'))

		if self.employee_id.calendar_id:
			total = self.employee_id.calendar_id.average_hours if self.employee_id.calendar_id.average_hours > 0 else 8
		else:
			total = 8
		# formula para los dias laborados segun sunat
		total_horas_minutos = modf(int(dias_laborados-dias_faltas)*total) if total_horas_jornada_ordinaria == 0 else total_horas_jornada_ordinaria
		total_horas_jornada_ordinaria = total_horas_minutos[1]
		total_minutos_jornada_ordinaria = Decimal(str(total_horas_minutos[0] * 60)).quantize(Decimal('1.'), rounding=ROUND_HALF_UP)
		# busco cualquier campo ya que lo unico que quiero es usar la funcionalidad de la generacion de la boleta
		payslip_run = self.env['hr.payslip.run']

		payslip_run.genera_boleta_empleado(self.date_from, self.date_to, payslips, str(dias_no_laborados), str(int(dias_laborados - dias_faltas)), str(total_horas_jornada_ordinaria), str(total_minutos_jornada_ordinaria), (total_sobretiempo), str(dias_subsidiados), elements,
										   company, categories, planilla_ajustes)


		template_values = []
		content = self.env.ref('requirements_paino.account_invoice_facturx_export').render(template_values)
		content = b"<?xml version='1.0' encoding='UTF-8'?>" + content

		import os
		cwd = os.getcwd()
		dir_path = os.path.dirname(os.path.realpath(__file__))
		_logger.info(cwd)
		_logger.info(dir_path)
		tree = ElementTree()
		tree.parse("/mnt/extra-addons2/requirements_paino/data/planilla_tmp.xml")

		_logger.info(tree)
		_logger.info('paso tree')
		# tree.write('output.xml')
		# archivo_pdf.build(content)

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		import os
		vals = {
			'output_name': 'output.xml',
			'output_file': open("/mnt/extra-addons2/requirements_paino/data/planilla_tmp.xml", "rb").read().encode("base64"),
		}
		sfs_id = self.env['planilla.export.file'].create(vals)
		return {
			"type": "ir.actions.act_window",
			"res_model": "planilla.export.file",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}
