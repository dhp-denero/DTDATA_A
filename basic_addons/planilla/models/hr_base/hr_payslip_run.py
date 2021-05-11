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


class HrPayslipRun(models.Model):

	_inherit = ['hr.payslip.run']
	_description = 'Genera planillas para todos los empleados'

	feriados = fields.Integer("Feriados y Domingos")
	dias_calendarios = fields.Integer(
		'Dias Calendarios', compute='_calcula_dias_calendarios')

	asiento_contable_id = fields.Many2one('account.move',
		string=u'Asiento Contable', ondelete='set null')

	state = fields.Selection([
		('draft', 'Draft'),
		('generado', 'Asiento Generado'),
		('close', 'Close'),
	], string='Status', readonly=True, copy=False, default='draft')
	bool_field = fields.Boolean(default=False)
	flag = fields.Boolean(default=False)
	cts_flag = fields.Boolean(default=False)
	grati_flag = fields.Boolean(default=False)
	liqui_flag = fields.Boolean(default=False)

	#FIXME: deprecado
	@api.depends('date_start', 'date_end')
	def _calcula_dias_calendarios(self):
		end = self.date_end
		self.dias_calendarios = calendar.monthrange(
			int(end[:4]), int(end[5:7]))[1]

	@api.multi
	def _wizard_generar_asiento_contable(self):

		query_vista = """
			select * from (
				select
				a6.date_end as fecha_fin,
				'ASIENTO DISTRIBUIDO DE LA PLANILLA DEL MES':: TEXT as concepto,
				a7.id as cuenta_debe,
				a10.id::integer as cuenta_analitica_id,
				round(sum(a1.amount*(a9.porcentaje/100))::numeric,2) as debe,
				0 as haber,
				''::text as nro_documento,
				0 as partner_id
				from hr_payslip_line a1
				left join hr_payslip a2 on a2.id=a1.slip_id
				left join hr_contract a3 on a3.id=a1.contract_id
				left join hr_employee a4 on a4.id=a1.employee_id
				left join hr_salary_rule a5 on a5.id=a1.salary_rule_id
				left join hr_payslip_run a6 on a6.id=a2.payslip_run_id
				left join account_account a7 on a7.id=a5.account_debit
				left join planilla_distribucion_analitica a8 on a8.id=a3.distribucion_analitica_id
				left join planilla_distribucion_analitica_lines a9 on a9.distribucion_analitica_id=a8.id
				left join account_analytic_account a10 on a10.id=a9.cuenta_analitica_id
				where a7.code is not null and a1.amount<>0 and a6.date_start='%s' and a6.date_end='%s'
				group by a6.date_end,a7.id,a10.id
				order by a7.code)tt
			union all
			select * from (
				select
				a6.date_end as fecha_fin,
				a5.name as concepto,
				a7.id as cuenta_haber,
				0::integer as cuenta_analitica_id,
				0 as debe,
				round(sum((a1.amount))::numeric,2) as haber,
				''::text as nro_documento,
				0 as partner_id
				from hr_payslip_line a1
				left join hr_payslip a2 on a2.id=a1.slip_id
				left join hr_contract a3 on a3.id=a1.contract_id
				left join hr_employee a4 on a4.id=a1.employee_id
				left join hr_salary_rule a5 on a5.id=a1.salary_rule_id
				left join hr_payslip_run a6 on a6.id=a2.payslip_run_id
				left join account_account a7 on a7.id=a5.account_credit
				where a7.code is not null and a6.date_start='%s' and a6.date_end='%s'
					and a1.code not in ('COMFI','COMMIX','SEGI','A_JUB')
					and a7.code not like '%s'
				group by a6.date_end,a6.name,a5.name,a7.id,a7.code
				having sum(a1.amount)<>0
				order by a7.code)tt
			union all
			select * from (
				select
				hpr.date_end as fecha_fin,
				pa.entidad||' - '||hpl.code as concepto,
				pa.account_id as cuenta_haber,
				0::integer as cuenta_analitica_id,
				0 as debe,
				round(sum((hpl.amount))::numeric,2) as haber,
				''::text as nro_documento,
				0 as partner_id
				from hr_payslip_line hpl
				inner join hr_payslip hp on hp.id = hpl.slip_id
				inner join hr_contract hc on hc.id = hp.contract_id
				inner join planilla_afiliacion pa on pa.id = hc.afiliacion_id
				inner join hr_payslip_run hpr on hpr.id = hp.payslip_run_id
				inner join hr_salary_rule hsr on hsr.id = hpl.salary_rule_id
				where pa.account_id is not null and hpr.date_start='%s' and hpr.date_end='%s'
					and hpl.code in ('COMFI','COMMIX','SEGI','A_JUB')
				group by hpr.date_end,hpr.name,pa.entidad,pa.account_id,hpl.code
				having sum(hpl.amount)<>0
			)ttt
			union all
			select * from (
				select
				min(a6.date_end) as fecha_fin,
				min(a5.name) as concepto,
				min(a7.id) as cuenta_haber,
				0::integer as cuenta_analitica_id,
				0 as debe,
				round(sum((a1.amount))::numeric,2) as haber,
				coalesce(rp.nro_documento,'')::text as nro_documento,
				coalesce(rp.id,0) as partner_id
				from hr_payslip_line a1
				left join hr_payslip a2 on a2.id=a1.slip_id
				left join hr_contract a3 on a3.id=a1.contract_id
				left join hr_employee a4 on a4.id=a1.employee_id
				left join res_partner rp on rp.id = a4.address_home_id
				left join hr_salary_rule a5 on a5.id=a1.salary_rule_id
				left join hr_payslip_run a6 on a6.id=a2.payslip_run_id
				left join account_account a7 on a7.id=a5.account_credit
				where a7.code is not null and a6.date_start= '%s' and a6.date_end= '%s'
					and a1.code not in ('COMFI','COMMIX','SEGI','A_JUB')
					and a7.code like '%s'
				group by rp.id,rp.nro_documento,a7.code
				having sum(a1.amount)<>0
				order by a7.code)tt
					""" % (self.date_start, self.date_end,
						self.date_start, self.date_end, '41%',
						self.date_start, self.date_end,
						self.date_start, self.date_end, '41%')
		self.env.cr.execute(query_vista)

		res = self.env.cr.dictfetchall()

		total_debe = 0
		total_haber = 0
		for x in res:
			try:
				total_debe += x['debe']
			except:
				total_debe += 0
		for x in res:
			try:
				total_haber += x['haber']
			except:
				total_haber += 0
		var = total_debe-total_haber

		vals = {
			'total_debe': total_debe,
			'total_haber': total_haber,
			'diferencia': var
		}

		sfs_id = self.env['planilla.asiento.contable'].create(vals)

		return {
			'name': 'Asiento Contable',
			"type": "ir.actions.act_window",
			"res_model": "planilla.asiento.contable",
			'view_type': 'form',
			'view_mode': 'form',
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
			'context': {'current_id': self.id, 'account_move_lines': res}
		}

	def buscar_empleado_en_tabla(self, tabla, employee_id):
		for line in tabla:

			if line.employee_id.id == employee_id.id:
				return line

	@api.multi
	def importar_beneficios_sociales(self):
		planilla_parametros_liq = self.env['planilla.parametros.liquidacion'].get_parametros_liquidacion()
		parametros_gratificacion = self.env['planilla.gratificacion'].get_parametros_gratificacion()
		# buscar gratificacion
		gratificaciones = self.env['planilla.gratificacion'].search(
			[('date_start', '=', self.date_start), ('date_end', '=', self.date_end)])
		if gratificaciones:

			gratificaciones_lines = gratificaciones.planilla_gratificacion_lines
			for gratificacion_empleado in gratificaciones_lines:
				payslip = self.buscar_empleado_en_tabla(
					self.slip_ids, gratificacion_empleado.employee_id)
				if payslip:
					gratificacion = payslip.input_line_ids.search(
						[('payslip_id', '=', payslip.id), ('code', '=', planilla_parametros_liq.cod_gratificacion.codigo)])
					gratificacion.amount = gratificacion_empleado.total_gratificacion
					bon9 = payslip.input_line_ids.search([('payslip_id', '=', payslip.id), (
						'code', '=', parametros_gratificacion.cod_bonificacion_9.code)])
					if bon9:
						bon9.amount = gratificacion_empleado.plus_9

		# buscar cts
		cts = self.env['planilla.cts'].search(
			[('date_start', '=', self.date_start), ('date_end', '=', self.date_end)])

		if cts:
			cts_lines = cts.planilla_cts_lines
			for cts_empleado in cts_lines:
				payslip = self.buscar_empleado_en_tabla(
					self.slip_ids, cts_empleado.employee_id)
				if payslip:
					entrada_cts = payslip.input_line_ids.search(
						[('payslip_id', '=', payslip.id), ('code', '=', planilla_parametros_liq.cod_cts.codigo)])
					entrada_cts.amount = cts_empleado.cts_a_pagar

		# buscar liquidacion
		liquidaciones = self.env['planilla.liquidacion'].search(
			[('date_start', '=', self.date_start), ('date_end', '=', self.date_end)])

		if liquidaciones:
			planilla_gratificacion_lines = liquidaciones.planilla_gratificacion_lines
			planilla_cts_lines = liquidaciones.planilla_cts_lines
			planilla_vacaciones_lines = liquidaciones.planilla_vacaciones_lines
			planilla_indemnizacion_lines = liquidaciones.planilla_indemnizacion_lines

			for gratificacion_trunca_emp in planilla_gratificacion_lines:
				payslip = self.buscar_empleado_en_tabla(
					self.slip_ids, gratificacion_trunca_emp.employee_id)
				if payslip:
					gratificacion_trunca = payslip.input_line_ids.search(
						[('payslip_id', '=', payslip.id), ('code', '=', planilla_parametros_liq.cod_gratificacion_trunca.codigo)])
					gratificacion_trunca.amount = gratificacion_trunca_emp.total_gratificacion
					bon9 = payslip.input_line_ids.search([('payslip_id', '=', payslip.id), (
						'code', '=', planilla_parametros_liq.cod_bonificacion_9.codigo)])
					if bon9:
						bon9.amount = gratificacion_trunca_emp.plus_9

			for cts_trunca_emp in planilla_cts_lines:
				payslip = self.buscar_empleado_en_tabla(
					self.slip_ids, cts_trunca_emp.employee_id)
				if payslip:
					cts_trunca = payslip.input_line_ids.search(
						[('payslip_id', '=', payslip.id), ('code', '=', planilla_parametros_liq.cod_cts_trunca.codigo)])
					cts_trunca.amount = cts_trunca_emp.cts_a_pagar

			for vacaciones_truncas_emp in planilla_vacaciones_lines:
				payslip = self.buscar_empleado_en_tabla(
					self.slip_ids, vacaciones_truncas_emp.employee_id)
				if payslip:
					vacacion_devengada = payslip.input_line_ids.search(
						[('payslip_id', '=', payslip.id), ('code', '=', planilla_parametros_liq.cod_vacacion_devengada.codigo)])
					vacacion_devengada.amount = vacaciones_truncas_emp.vacaciones_devengadas
					vacacion_trunca = payslip.input_line_ids.search(
						[('payslip_id', '=', payslip.id), ('code', '=', planilla_parametros_liq.cod_vacacion_trunca.codigo)])
					vacacion_trunca.amount = vacaciones_truncas_emp.vacaciones_truncas
			for imdenizacion_line in planilla_indemnizacion_lines:
				payslip = self.buscar_empleado_en_tabla(
					self.slip_ids, imdenizacion_line.employee_id)
				if payslip:
					indemnizacion = payslip.input_line_ids.search(
						[('payslip_id', '=', payslip.id), ('code', '=', planilla_parametros_liq.cod_indemnizacion.codigo)])
					indemnizacion.amount = imdenizacion_line.monto


		# buscar quita categoria

		return self.env['planilla.warning'].info(title='Resultado de importacion', message="LOS BENEFICIOS SOCIALES SE IMPORTARON DE MANEARON DE MANERA EXITOSA!")


	@api.multi
	def importar_quinta_categoria(self):
		parametro_quinta_categoria = self.env['planilla.quinta.categoria'].search([],limit=1)

		periodo= self.env['account.period'].search([('date_start','=',self.date_start),('date_stop','=',self.date_end)])

		quintas_categorias = self.env['quinta.categoria'].search([('periodo','=',periodo.id)])

		for row in  quintas_categorias.detalle:
			payslip = self.buscar_empleado_en_tabla(
					self.slip_ids, row.empleado)

			if payslip:
				entrada_quinta = payslip.input_line_ids.search(
					[('payslip_id', '=', payslip.id), ('code', '=', parametro_quinta_categoria.ingreso_predeterminado.codigo)])
				entrada_quinta.amount = row.renta_total

		return self.env['planilla.warning'].info(title='Resultado de importacion', message="SE IMPORTO QUINTA CATEGORIA DE MANERA EXITOSA!")

	@api.multi
	def import_advances(self):
		def _process_data(advances,benefits=False):
			for advance in advances:
				payslips = self.env['hr.payslip'].search([('employee_id','=',advance.employee_id.id),
												('date_from','=',self.date_start),
												('date_to','=',self.date_end)])
				if payslips:
					payslip = max(payslips,key=lambda p:p.contract_id.date_start)
					if payslip:
						input_line = next(iter(filter(lambda inp:inp.code == advance.advance_type_id.input_id.codigo,payslip.input_line_ids)),None)
						if input_line:
							input_line.amount = advance.amount
							advance.state = 'paid out'

		advances = self.env['hr.advance'].search([('date','>=',self.date_start),('date','<=',self.date_end)])
		_process_data(advances)
		date_start,date_end = datetime.strptime(self.date_start,'%Y-%m-%d'),datetime.strptime(self.date_end,'%Y-%m-%d')
		if (date_start.month == 7 and date_end.month == 7) or (date_start.month == 12 and date_end.month == 12):
			advances = self.env['hr.advance'].search([('advance_type_id.discount_type','in',('07','12')),('state','=','not payed')])
			_process_data(advances,True)

		return self.env['planilla.warning'].info(title='Resultado de importacion', message="SE IMPORTO ADELANTOS DE MANERA EXITOSA!")

	@api.multi
	def import_loans(self):
		loans = self.env['hr.loan.line'].search([('date','>=',self.date_start),('date','<=',self.date_end)])
		for loan in loans:
			payslips = self.env['hr.payslip'].search([('employee_id','=',loan.employee_id.id),
											('date_from','=',self.date_start),
											('date_to','=',self.date_end)])
			if payslips:
				payslip = max(payslips,key=lambda p:p.contract_id.date_start)
				if payslip:
					input_line = next(iter(filter(lambda inp:inp.code == loan.input_id.codigo,payslip.input_line_ids)),None)
					if input_line:
						input_line.amount = loan.amount
						loan.validation = 'paid out'

		return self.env['planilla.warning'].info(title='Resultado de importacion', message="SE IMPORTO PRESTAMOS DE MANERA EXITOSA!")

	@api.multi
	def regulariza_dias_laborados(self):
		planilla_ajustes = self.env['planilla.ajustes'].get_parametros_ajustes()
		DLAB = planilla_ajustes.cod_dias_laborados
		self.ensure_one()

		for payslip in self.slip_ids:
			dias_laborados = payslip.worked_days_line_ids.search(
				[('payslip_id', '=', payslip.id), ('code', '=', planilla_ajustes.cod_dias_laborados.codigo)])

			if payslip.contract_id.date_start > self.date_start and payslip.contract_id.date_end < self.date_end:
				fecha_ini = fields.Date.from_string(payslip.contract_id.date_start)
				fecha_fin = fields.Date.from_string(payslip.contract_id.date_end)
				if fecha_ini and fecha_fin:
					dias_laborados.number_of_days = abs(fecha_fin.day-fecha_ini.day)+1
				else:
					dias_laborados.number_of_days = abs(DLAB.dias-fecha_ini.day)+1

			elif payslip.contract_id.date_start > self.date_start:
				fecha_ini = fields.Date.from_string(payslip.contract_id.date_start)
				if fecha_ini:
					dias_laborados.number_of_days = 30-fecha_ini.day+1
			elif payslip.contract_id.date_end < self.date_end:
				if payslip.contract_id.date_end:
					fecha_fin = fields.Date.from_string(payslip.contract_id.date_end)
					if fecha_fin:
						dias_laborados.number_of_days = fecha_fin.day
				else:
					dias_laborados.number_of_days = DLAB.dias
			else:
				dias_laborados.number_of_days = DLAB.dias

			faltas = payslip.worked_days_line_ids.search([('payslip_id', '=', payslip.id), ('code', 'in', planilla_ajustes.cod_dias_subsidiados.mapped('codigo'))])
			for i in faltas:
				dias_laborados.number_of_days += -i.number_of_days

		return self.env['planilla.warning'].info(title='Resultado de generacion', message="SE GENERO DE MANERA EXITOSA!")

	@api.one
	def write(self, vals):
		line = False
		self.ensure_one()
		if 'date_start' in vals and 'date_end' in vals:
			line = self.env['hr.payslip.run'].search(
				[('date_start', '=', vals['date_start']), ('date_end', '=',  vals['date_start'])])
		if line:
			raise ValidationError(
				"Ya existe una nomina con las fechas  %s y %s" % (vals['date_start'], self.date_end))
		if 'date_start' in vals:
			line = self.env['hr.payslip.run'].search(
				[('date_start', '=', vals['date_start']), ('date_end', '=', self.date_end)])

		if line:
			raise ValidationError(
				"Ya existe una nomina con las fechas  %s y %s" % (vals['date_start'], self.date_end))
		if 'date_end' in vals:
			line = self.env['hr.payslip.run'].search(
				[('date_start', '=', self.date_start), ('date_end', '=', vals['date_end'])])

		if line:
			raise ValidationError(
				"Ya existe una nomina con las fechas  %s y %s" % (self.date_start, vals['date_end']))

		return super(HrPayslipRun, self).write(vals)

	@api.model
	def create(self, vals):
		line = self.env['hr.payslip.run'].search(
			[('date_start', '=', vals['date_start']), ('date_end', '=', vals['date_end'])])
		if line:
			raise ValidationError(
				"Ya existe una nomina con las fechas  %s y %s" % (vals['date_start'], vals['date_end']))
		return super(HrPayslipRun, self).create(vals)

	def get_mes(self, mes):
		if mes == 1:
			return "Enero"
		elif mes == 2:
			return "Febrero"
		elif mes == 3:
			return "Marzo"
		elif mes == 4:
			return "Abril"
		elif mes == 5:
			return "Mayo"
		elif mes == 6:
			return "Junio"
		elif mes == 7:
			return "Julio"
		elif mes == 8:
			return "Agosto"
		elif mes == 9:
			return "Septiembre"
		elif mes == 10:
			return "Octubre"
		elif mes == 11:
			return "Noviembre"
		else:
			return "Diciembre"

	@api.multi
	def draft_payslip_run(self):
		if self.state =='generado':
			self.asiento_contable_id.unlink()
		else:
			for line in self.slip_ids:
				line.line_ids.unlink()
				line.write({'state': 'draft'})
		self.refresh()
		return super(HrPayslipRun, self).draft_payslip_run()

	@api.multi
	def close_payslip_run(self):
		for line in self.slip_ids:
			line.write({'state': 'done'})
		return super(HrPayslipRun, self).close_payslip_run()

	@api.multi
	def genera_planilla_afp_net(self):
		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		try:
			direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		workbook = Workbook(direccion + 'planilla_afp_net.xls')
		planilla_ajustes = self.env['planilla.ajustes'].search([], limit=1)
		for payslip_run in self.browse(self.ids):
			query_vista = """  DROP VIEW IF EXISTS planilla_afp_net_xlsx;
				create or replace view planilla_afp_net_xlsx as (

				select row_number() OVER () AS id,* from
				(

					select  hc.cuspp,ptd.codigo_afp as tipo_doc,he.identification_id,he.a_paterno,he.a_materno,he.nombres,
					case
						when (hc.date_end isnull or hc.date_end<='%s' or hc.date_end>='%s') then 'S'
					else
						'N' end as relacion_laboral,
					case
						when (hc.date_start between '%s' and '%s') then 'S'
					else
						'N' end as inicio_relacion_laboral,
					case
						when (hc.date_end between '%s' and '%s') then 'S'
					else
						'N' end as cese_relacion_laboral,
						hc.excepcion_aportador,
					(select total from hr_payslip_line
							where slip_id = p.id and  code = '%s' ) as remuneracion_asegurable,
					(SELECT ''::TEXT as aporte_fin_provisional),
					(SELECT ''::TEXT as aporte_sin_fin_provisional),
					(SELECT ''::TEXT as aporte_voluntario_empleador),
					case
						when (hc.regimen_laboral isnull) then 'N'
					else
						hc.regimen_laboral end as regimen_laboral
					from hr_payslip_run hpr
					inner join hr_payslip p
					on p.payslip_run_id = hpr.id
					inner join hr_contract hc
					on hc.id = p.contract_id
					inner join hr_employee he
					on he.id = hc.employee_id
					left join planilla_tipo_documento ptd
					on ptd.id = he.tablas_tipo_documento_id
					inner join planilla_afiliacion pa on pa.id = hc.afiliacion_id
					where pa.entidad like '%s' and hpr.id= %d
						) T
				)""" % (payslip_run.date_end, payslip_run.date_end,
						payslip_run.date_start, payslip_run.date_end,
						payslip_run.date_start, payslip_run.date_end,
						planilla_ajustes.cod_remuneracion_asegurable.code if planilla_ajustes else '',
						'AFP%',
						payslip_run.id)
			self.env.cr.execute(query_vista)



			worksheet = workbook.add_worksheet(
				str(payslip_run.id)+'-'+payslip_run.date_start+'-'+payslip_run.date_end)
			worksheet.set_landscape()  # Horizontal
			worksheet.set_paper(9)  # A-4
			worksheet.set_margins(left=0.75, right=0.75, top=1, bottom=1)
			worksheet.fit_to_pages(1, 0)  # Ajustar por Columna

			bold = workbook.add_format({'bold': True})
			normal = workbook.add_format()
			boldbord = workbook.add_format({'bold': True})
			boldbord.set_border(style=2)
			boldbord.set_align('center')
			boldbord.set_align('vcenter')
			boldbord.set_text_wrap()
			boldbord.set_font_size(9)
			boldbord.set_bg_color('#DCE6F1')
			numbertres = workbook.add_format({'num_format': '0.000'})
			numberdos = workbook.add_format({'num_format': '0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)
			bord.set_text_wrap()
			# numberdos.set_border(style=1)
			numbertres.set_border(style=1)

			title = workbook.add_format({'bold': True})
			title.set_align('center')
			title.set_align('vcenter')
			title.set_text_wrap()
			title.set_font_size(20)
			# worksheet.set_row(0, 30)

			x = 0

			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			filtro = []
			for line in self.env['planilla.afp.net.xlsx'].search(filtro):
				worksheet.write(x, 0, line.id if line.id else '')
				worksheet.write(
					x, 1, line.cuspp if line.cuspp else '')
				worksheet.write(
					x, 2, line.tipo_doc if line.tipo_doc else '')

				worksheet.write(
					x, 3, line.identification_id if line.identification_id else '')
				worksheet.write(x, 4, line.a_paterno)
				worksheet.write(x, 5, line.a_materno)
				worksheet.write(x, 6, line.nombres)
				worksheet.write(
					x, 7, line.relacion_laboral if line.relacion_laboral else '')
				worksheet.write(
					x, 8, line.inicio_relacion_laboral if line.inicio_relacion_laboral else '')
				worksheet.write(
					x, 9, line.cese_relacion_laboral if line.cese_relacion_laboral else '')
				worksheet.write(
					x, 10, line.excepcion_aportador if line.excepcion_aportador else '')
				worksheet.write(
					x, 11, line.remuneracion_asegurable, numberdos)
				worksheet.write(
					x, 12, line.aporte_fin_provisional, numberdos)
				worksheet.write(
					x, 13, line.aporte_sin_fin_provisional, numberdos)
				worksheet.write(
					x, 14, line.aporte_voluntario_empleador, numberdos)
				worksheet.write(
					x, 15, line.regimen_laboral if line.regimen_laboral else '')

				x = x + 1

				tam_col = [2, 15, 2, 10, 10, 10, 35, 1, 1, 1, 1,
						   8, 5, 5, 1, 1]

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
				worksheet.set_column('M:M', tam_col[12])
				worksheet.set_column('O:O', tam_col[13])
				worksheet.set_column('P:P', tam_col[14])

		workbook.close()

		f = open(direccion+'planilla_afp_net.xls', 'rb')

		vals = {
			'output_name': 'planilla_afp_net.xls',
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

	def get_col_widths(self, datos):
		# First we find the maximum length of the index column
		datos = zip(*datos)  # transponiendo filas por columnas
		column_len = []
		for i in range(len(datos)):
			max_col = 0
			for j in range(len(datos[i])):
				if len(str(datos[i][j]).strip()) > max_col:
					max_col = len(str(datos[i][j]).strip())

			column_len.append(max_col+5)
		return column_len

	@api.multi
	def exportar_plame(self):
		if len(self.ids) > 1:
			raise UserError('Solo se puede mostrar una planilla a la vez, seleccione solo una nomina')
		output = io.BytesIO()
		# workbook = Workbook('planilla_plame.xls')

		planilla_ajustes = self.env['planilla.ajustes'].search([], limit=1)
		try:
			ruta = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		docname = ruta+'0601%s%s%s.rem' % (
			self.date_end[:4], self.date_end[5:7], planilla_ajustes.ruc if planilla_ajustes else '')

		f = open(docname, "w+")
		for payslip_run in self.browse(self.ids):
			employees = []
			for payslip in payslip_run.slip_ids:
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
						and hc.regimen_laboral_empresa in ('practicante')
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
			self.date_end[:4], self.date_end[5:7], planilla_ajustes.ruc if planilla_ajustes else ''),
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
			for payslip in payslip_run.slip_ids:
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
						where hp.payslip_run_id = %d
						and hp.employee_id = %d
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

	@api.multi
	def exportar_planilla_tabular_xlsx(self):
		if len(self.ids) > 1:
			raise UserError(
				'Solo se puede mostrar una planilla a la vez, seleccione solo una nómina')

		self.env['planilla.planilla.tabular.wizard'].reconstruye_tabla(self.date_start,self.date_end)
		try:
			direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		workbook = Workbook(direccion+'planilla_tabular.xls')
		worksheet = workbook.add_worksheet(
			str(self.id)+'-'+self.date_start+'-'+self.date_end)
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
			x, 1, self.get_mes(int(self.date_end[5:7]) if self.date_end else 0).upper()+"-"+self.date_end[:4], formatLeft)

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

		filtro = []

		query = 'select %s from planilla_tabular' % (','.join(fields))
		self.env.cr.execute(query)
		datos_planilla = self.env.cr.fetchall()
		range_row = len(datos_planilla[0] if len(datos_planilla) > 0 else 0)
		total_essalud = 0
		for i in range(len(datos_planilla)):
			for j in range(range_row):
				if j not in (3,4):
					if j == 0 or j == 1:
						worksheet.write(x, j, datos_planilla[i][j] if datos_planilla[i][j] else '0.00', formatLeft)
					else:
						worksheet.write(x, j, datos_planilla[i][j] if datos_planilla[i][j] else '0.00', numberdos)
			essalud = self.env['hr.payslip'].browse(datos_planilla[i][4]).essalud
			worksheet.write(x,j+1,essalud,formatLeft)
			total_essalud += essalud
			x = x+1
		x = x + 1
		datos_planilla_transpuesta = zip(*datos_planilla)

		for j in range(5, len(datos_planilla_transpuesta)):
			worksheet.write(x, j, sum([float(d) for d in datos_planilla_transpuesta[j]]), styleFooterSum)

		worksheet.write(x,j+1,total_essalud,styleFooterSum)

		# seteando tamaño de columnas
		col_widths = self.get_col_widths(datos_planilla)
		worksheet.set_column(0, 0, col_widths[0]-10)
		worksheet.set_column(1, 1, col_widths[1]-7)
		for i in range(2, len(col_widths)):
			worksheet.set_column(i, i, col_widths[i])

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

	@api.multi
	def generar_planillas_lotes(self):
		self.bool_field = True
		payslips = self.env['hr.payslip']

		from_date = self.date_start  # run_data.get('date_start')
		to_date = self.date_end  # $run_data.get('date_end')

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
		self.slip_ids.unlink()
		for contract in self.env['hr.contract'].browse([row['id'] for row in employee_aux_ids]):
			slip_data = self.env['hr.payslip'].onchange_employee_id(
				from_date, to_date, contract.employee_id.id, contract.id)
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
		self.bool_field = False
		return self.env['planilla.warning'].info(title='Resultado de generacion', message="SE GENERO LA PLANILLA DE MANERA EXITOSA!")

	@api.multi
	def calcular_reglas_salariales(self):
		for employee_payroll in self.slip_ids:
			employee_payroll.dias_calendarios = self.dias_calendarios
			employee_payroll.feriados = self.feriados
			employee_payroll.compute_sheet()
		self.slip_ids.refresh()
		return self.env['planilla.warning'].info(title='Resultado de calculo', message="SE CALCULO  REGLAS SALARIALES DE MANERA EXITOSA!")

	@api.multi
	def recalcular_inputs(self):
		wizard = self.env['add.input']
		return wizard.get_wizard(self.id)
		"""
		for employee_payslip in self.slip_ids:
			new_inputs = self.env['planilla.inputs.nomina'].search([])
			old_inputs = self.env['hr.payslip.input'].search([])
			for i in new_inputs:
				if i.descripcion in old_inputs.name and i.codigo in old_inputs.code:
					pass
				else:
					data = {'name': i.descripcion,
							'payslip_id': employee_payslip.id,
							'code': i.codigo,
							'amount': i.amount,
							'contract_id': employee_payslip.contract_id.id}
					self.env['hr.payslip.input'].create(data)
		raise UserError('CALCULO EXITOSO')
		"""

	@api.multi
	def generar_planilla_tabular(self):
		if len(self.ids) > 1:
			raise UserError(
				'Solo se puede generar una planilla a la vez, seleccione solo una')

		return self.env['planilla.planilla.tabular.wizard'].create({'fecha_ini': self.date_start, 'fecha_fin': self.date_end}).do_rebuild()

	@api.multi
	def ver_pantalla_planilla_tabular(self):
		if len(self.ids) > 1:
			raise UserError(
				'Solo se puede mostrar una planilla a la vez, seleccione solo una nómina')
		if not self.env['planilla.tabular'].search([]):
			raise UserError(
				'No hay Datos para mostrar,intente el boton generar planilla tabular')
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'planilla.tabular',
			'view_type': 'form',
			'view_mode': 'tree',
			'target': 'current'
		}

	@api.multi
	def generar_boletas(self):
		try:
			ruta = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')

		self.reporteador(True)

		vals = {
			'output_name': 'Planilla.pdf',
			'output_file': open(ruta+"planilla_tmp.pdf", "rb").read().encode("base64"),
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
	def reporteador(self,option):
		try:
			ruta = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')

		if option == True:
			archivo_pdf = SimpleDocTemplate(
				ruta+"planilla_tmp.pdf", pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20)

			elements = []

			categories = self.env['hr.salary.rule.category'].search(
				[('aparece_en_nomina', '=', True)], order="secuencia")
			planilla_ajustes = self.env['planilla.ajustes'].search([], limit=1)
			# genero boletas por cada payslip seleccionada en el treeview
			for payslip_run in self.browse(self.ids):  # lotes de nominas
				employees = []
				for payslip in payslip_run.slip_ids:  # lista de nominas
					if payslip.employee_id.id in employees:
						continue
					# for empleado in self.env['hr.employee'].search([]):

					dias_no_laborados,dias_laborados,first,second,dias_faltas = 0,0,0,0,0

					payslips = self.env['hr.payslip'].search([('payslip_run_id','=',payslip_run.id),('employee_id','=',payslip.employee_id.id)])
					company = self.env['res.company'].search([], limit=1)
					for pays in payslips:
						dias_no_laborados += int(pays.worked_days_line_ids.search(
							[('code', '=', planilla_ajustes.cod_dias_no_laborados.codigo if len(planilla_ajustes) > 0 else ''), ('payslip_id', '=', pays.id)], limit=1).number_of_days)

					# dias_laborados = int(
					#     payslip.dias_calendarios-dias_no_laborados)
					for pays in payslips:
						if not pays.contract_id.hourly_worker:
							dias_laborados += int(pays.worked_days_line_ids.search(
								[('code', '=', planilla_ajustes.cod_dias_laborados.codigo if len(planilla_ajustes) > 0 else ''), ('payslip_id', '=', pays.id)], limit=1).number_of_days)
					for pays in payslips:
						if not pays.contract_id.hourly_worker:
							dias_laborados -= pays.feriados
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
					# str(int(self.env.cr.dictfetchone()['sum']))
					total_sobretiempo = self.env.cr.dictfetchone()

					# formula para los dias laborados segun sunat
					# total_horas_jornada_ordinaria = (30-payslip_run.feriados)*8
					for pays in payslips:
						dias_faltas += self.env['hr.payslip.worked_days'].search([
							('code', '=', planilla_ajustes.cod_dias_no_laborados.codigo if planilla_ajustes else ''),
							('payslip_id', '=', pays.id)
							], limit=1).number_of_days
					if payslip.employee_id.calendar_id:
						total = payslip.employee_id.calendar_id.average_hours if payslip.employee_id.calendar_id.average_hours > 0 else 8
					else:
						total = 8

					#raise UserError(u'El Empleado '+payslip.employee_id.name+' no tiene un Horario establecido.')
					# formula para los dias laborados segun sunat
					if not payslip.contract_id.hourly_worker:
						total_horas_minutos = modf(int(dias_laborados-dias_faltas)*total)
					else:
						total_horas_minutos = modf(sum(payslip.worked_days_line_ids.filtered(lambda l:l.code == planilla_ajustes.cod_dias_laborados.codigo).mapped('number_of_hours')))

					total_horas_jornada_ordinaria = total_horas_minutos[1]
					total_minutos_jornada_ordinaria = Decimal(str(total_horas_minutos[0] * 60)).quantize(Decimal('1.'), rounding=ROUND_HALF_UP)

					self.genera_boleta_empleado(payslip_run.date_start, payslip_run.date_end, payslips, str(dias_no_laborados), str(dias_laborados), str(total_horas_jornada_ordinaria), str(total_minutos_jornada_ordinaria), (total_sobretiempo), str(dias_subsidiados), elements,
												company, categories, planilla_ajustes)
					employees.append(payslip.employee_id.id)

			archivo_pdf.build(elements)
		else:
			dic = {
				'contador':0,
				'ids':[],
				'date_start':'',
				'date_end':''
			}
			elements = []
			categories = self.env['hr.salary.rule.category'].search(
				[('aparece_en_nomina', '=', True)], order="secuencia")
			planilla_ajustes = self.env['planilla.ajustes'].search([], limit=1)
			c = 0
			try:
				ruta = self.env['main.parameter.hr'].search([])[0].dir_create_file
			except:
				raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
			# genero boletas por cada payslip seleccionada en el treeview
			for payslip_run in self.browse(self.ids):  # lotes de nominas
				employees = []
				for payslip in payslip_run.slip_ids:  # lista de nominas
					if payslip.employee_id.id in employees:
						continue
					archivo_pdf = SimpleDocTemplate(ruta+"planilla_tmp"+str(payslip.employee_id.id)+".pdf", pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20)
					# for empleado in self.env['hr.employee'].search([]):

					dias_no_laborados,dias_laborados,first,second,dias_faltas = 0,0,0,0,0

					payslips = self.env['hr.payslip'].search([('payslip_run_id','=',payslip_run.id),('employee_id','=',payslip.employee_id.id)])
					company = self.env['res.company'].search([], limit=1)
					for pays in payslips:
						dias_no_laborados += int(pays.worked_days_line_ids.search(
							[('code', '=', planilla_ajustes.cod_dias_no_laborados.codigo if len(planilla_ajustes) > 0 else ''), ('payslip_id', '=', pays.id)], limit=1).number_of_days)

					# dias_laborados = int(
					#     payslip.dias_calendarios-dias_no_laborados)
					for pays in payslips:
						dias_laborados += int(pays.worked_days_line_ids.search(
							[('code', '=', planilla_ajustes.cod_dias_laborados.codigo if len(planilla_ajustes) > 0 else ''), ('payslip_id', '=', pays.id)], limit=1).number_of_days)
					for pays in payslips:
						dias_laborados -= pays.feriados
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
					# str(int(self.env.cr.dictfetchone()['sum']))
					total_sobretiempo = self.env.cr.dictfetchone()

					# formula para los dias laborados segun sunat
					# total_horas_jornada_ordinaria = (30-payslip_run.feriados)*8
					for pays in payslips:
						dias_faltas += self.env['hr.payslip.worked_days'].search(
							[('code', '=', planilla_ajustes.cod_dias_no_laborados.codigo if planilla_ajustes else ''),
							 ('payslip_id', '=', pays.id)], limit=1).number_of_days

					if payslip.employee_id.calendar_id:
						total = payslip.employee_id.calendar_id.average_hours if payslip.employee_id.calendar_id.average_hours > 0 else 8
					else:
						total = 8
					# formula para los dias laborados segun sunat
					total_horas_minutos = modf(int(dias_laborados-dias_faltas)*total)
					total_horas_jornada_ordinaria = total_horas_minutos[1]
					total_minutos_jornada_ordinaria = Decimal(str(total_horas_minutos[0] * 60)).quantize(Decimal('1.'), rounding=ROUND_HALF_UP)

					dic["ids"].append(payslip.employee_id)
					dic["date_start"] = payslip_run.date_start
					dic["date_end"] = payslip_run.date_end
					self.genera_boleta_empleado(payslip_run.date_start, payslip_run.date_end, payslips, str(dias_no_laborados), str(int(dias_laborados-dias_faltas)), str(total_horas_jornada_ordinaria), str(total_minutos_jornada_ordinaria), (total_sobretiempo), str(dias_subsidiados), elements,
												company, categories, planilla_ajustes)
					archivo_pdf.build(elements)
					employees.append(payslip.employee_id.id)
					c += 1
			dic["contador"] = c
			return dic

	@api.multi
	def genera_boleta_empleado(self, date_start, date_end, payslips, dias_no_laborados, dias_laborados, total_horas_jornada_ordinaria, total_minutos_jornada_ordinaria, total_sobretiempo, dias_subsidiados, elements, company, categories, planilla_ajustes):
		try:
			ruta = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
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
			empleado.name_related.strip().title(), style_cell), '', '', '', Paragraph(contract_employee.situacion_id.descripcion_abrev if contract_employee.situacion_id.descripcion_abrev else '', style_cell), '']

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

		# +[['1', '2', '3', '4', '5', '6', '7', '8']]
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
