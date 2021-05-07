# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime, date, timedelta
import calendar
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import sys
import io
from xlsxwriter.workbook import Workbook
import base64
from dateutil.relativedelta import *

from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red , black , blue, gray, white, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table
from reportlab.lib.units import  cm,mm
from reportlab.lib.utils import simpleSplit
import os
import decimal
import logging
_logger = logging.getLogger(__name__)

class ContractInherit(models.Model):
	_inherit = 'hr.contract'

	date_start = fields.Date('Start Date', required=True, default=fields.Date.today)
	date_end = fields.Date('End Date')

	@api.onchange('employee_id')
	def _onchange_employee_id(self):
		if not self.employee_id:
			return
		else:
			self.date_start = self.employee_id.date_entry_bl
			self.date_end= self.employee_id.date_end_bl

class PlanillaLiquidacionInherit(models.Model):
	_inherit = "planilla.liquidacion"

	@api.multi
	def calcular_liquidacion(self):
		self.planilla_gratificacion_lines.unlink()
		self.planilla_cts_lines.unlink()
		self.planilla_vacaciones_lines.unlink()
		self.planilla_indemnizacion_lines.unlink()

		mes_periodo = self.month
		days = calendar.monthrange(int(self.year), mes_periodo)[1]
		date_start_liquidacion = date(int(self.year), mes_periodo, 1)
		date_end_liquidacion = date(int(self.year), mes_periodo, days)

		date_start_liquidacion_cts = date(int(self.year), mes_periodo, 1)
		date_end_liquidacion_cts = date(int(self.year), mes_periodo, days)

		date_start_liquidacion_vacaciones = date(
			int(self.year), mes_periodo, 1)
		date_end_liquidacion_vacaciones = date(
			int(self.year), mes_periodo, days)

		if mes_periodo >= 1 and mes_periodo <= 6:
			rango_inicio_contrato = date(int(self.year), 6, 1)
			rango_fin_contrato = date(int(self.year), 6, 30)
			rango_inicio_planilla = date(int(self.year), 1, 1)
			rango_fin_planilla = date(int(self.year), 6, 30)
		else:
			rango_inicio_contrato = date(int(self.year), 12, 1)
			# rango_fin_contrato = date(int(self.year), 12, 31) #30 nov
			rango_fin_contrato = date(int(self.year), 11, 30)  # 30 nov
			rango_inicio_planilla = date(int(self.year), 7, 1)
			# rango_fin_planilla = date(int(self.year), 12, 31)
			rango_fin_planilla = date(int(self.year), 11, 30)

		if mes_periodo >= 5 and mes_periodo <= 10:  # mayo a octubre
			rango_inicio_planilla_cts = date(int(self.year), 5, 1)
			rango_fin_planilla_cts = date(int(self.year), 10, 31)
			# se usa para sacar los dia del periodo anterior
			anho_periodo_anterior_cts = int(self.year)
			tipo_cts = '12'
			tipo_gratificacion = '07'

		elif mes_periodo >= 1 and mes_periodo <= 4:  # enero a abril
			rango_inicio_planilla_cts = date(int(self.year)-1, 11, 1)
			rango_fin_planilla_cts = date(int(self.year), 4, 30)
			# se usa para sacar los dia del periodo anterior
			anho_periodo_anterior_cts = int(self.year)-1
			tipo_cts = '07'
			tipo_gratificacion = '12'
		else:  # solo queda noviembre y diciembre
			rango_inicio_planilla_cts = date(int(self.year), 11, 1)
			rango_fin_planilla_cts = date(int(self.year)+1, 4, 30)
			# se usa para sacar los dia del periodo anterior
			anho_periodo_anterior_cts = int(self.year)
			tipo_cts = '07'
			tipo_gratificacion ='07'

		if mes_periodo == 12:
			tipo_gratificacion = '12'

		contratos_empleado = self.env['hr.contract'].search(
			[('date_end', '>=', date_start_liquidacion_vacaciones),
			('date_end', '<=', date_end_liquidacion_vacaciones),
			('regimen_laboral_empresa','not in',['practicante','microempresa']),
			])

		for e,contrato in enumerate(contratos_empleado,1):
			# 1 busco los contratos de ese empleado
			contratos_empleado = self.env['hr.contract'].search(
				[('employee_id', '=', contrato.employee_id.id),
				('date_end', '<=', contrato.date_end)], order='date_end desc')

			_logger.info('contratos_empleado')
			_logger.info(contratos_empleado)
			if len(contratos_empleado) > 0:
				# datetime
				fecha_ini = fields.Date.from_string(
					contratos_empleado[-1].date_start)
				fecha_fin_contrato = fields.Date.from_string(
					contratos_empleado[0].date_end)
				_logger.info(contratos_empleado[-1])
				_logger.info(fecha_fin_contrato)
				# 2 busco los contratos anteriores que esten continuos(no mas de un dia de diferencia entre contratos)
				for i in range(1, len(contratos_empleado)):
					c_empleado = contratos_empleado[i]
					fecha_fin = fields.Date.from_string(c_empleado.date_end)
					if abs(((fecha_fin)-(fecha_ini)).days) == 1:
						_logger.info('diferencia de 1')
						fecha_ini = fields.Date.from_string(c_empleado.date_start)
				_logger.info('FECHA INI Y FECHA FIN')
				_logger.info(fecha_ini)
				_logger.info(fecha_fin_contrato)
				if self.month == 12:
					grati = self.env['planilla.gratificacion'].search([('year','=',self.year),('tipo','=',self.month)])
					employee_filtered = filter(lambda g:g.employee_id.id == contrato.employee_id.id,grati.planilla_gratificacion_lines)
					if not employee_filtered:
						self.calcular_gratificacion(contrato, rango_inicio_planilla, rango_fin_planilla,
													fecha_ini, fecha_fin_contrato, date_start_liquidacion, date_end_liquidacion,e)
				else:
					self.calcular_gratificacion(contrato, rango_inicio_planilla, rango_fin_planilla,
													fecha_ini, fecha_fin_contrato, date_start_liquidacion, date_end_liquidacion,e)
				self.calcular_cts(contrato, rango_inicio_planilla_cts, rango_fin_planilla_cts,
								  fecha_ini, fecha_fin_contrato, date_start_liquidacion, date_end_liquidacion, anho_periodo_anterior_cts, tipo_cts,tipo_gratificacion,e)
				self.calcular_vacaciones(
					contrato, date_start_liquidacion_vacaciones, date_end_liquidacion_vacaciones, fecha_ini, fecha_fin_contrato,e)

		nomina = self.env['hr.payslip.run'].search([('date_start', '=', self.date_start),
													('date_end', '=', self.date_end)])
		nomina.write({'liqui_flag':True})

		return self.env['planilla.warning'].info(title='Resultado de importacion', message="SE CALCULO LIQUIDACION DE MANERA EXITOSA!")

	@api.multi
	def calcular_gratificacion(self, contrato, rango_inicio_planilla, rango_fin_planilla, fecha_ini, fecha_fin, date_start_liquidacion, date_end_liquidacion,e):
		self.ensure_one()
		_logger.info('calcular_gratificacion')
		ultimo_mes_no_cuenta = False
		helper_liquidacion = self.env['planilla.helpers']
		parametros_gratificacion = self.env['planilla.gratificacion'].get_parametros_gratificacion()
		if fecha_ini < rango_inicio_planilla:
			fecha_computable = rango_inicio_planilla
		else:
			fecha_computable = fecha_ini

		dias_mes_cese = calendar.monthrange(
			int(self.year), fecha_fin.month)[1]

		# meses = helper_liquidacion.diferencia_meses_gratificacion(
		#     fecha_computable, fecha_fin)

		meses, dias = helper_liquidacion.diferencia_meses_dias(
				fecha_computable, fecha_fin)
		if not self.calcular_meses_dias:
			dias = 0

		fecha_inicio_nominas = date(
			fecha_computable.year, fecha_computable.month, 1)
		fecha_fin_nominas = date(fecha_fin.year, fecha_fin.month, calendar.monthrange(fecha_fin.year, fecha_fin.month)[1])
		fecha_fin_nominas = fecha_fin - relativedelta(months=0)
		fecha_fin_nominas = date(fecha_fin_nominas.year, fecha_fin_nominas.month, calendar.monthrange(
			fecha_fin_nominas.year, fecha_fin_nominas.month)[1])

		sql = """
			select min(hp.id),sum(hwd.number_of_days) as days,min(hp.name) as name
			from hr_payslip hp
			inner join hr_contract hc on hc.id = hp.contract_id
			inner join hr_payslip_worked_days hwd on hwd.payslip_id = hp.id
			where hp.date_from >= '%s'
			and hp.date_to <= '%s'
			and hp.employee_id = %d
			and hc.regimen_laboral_empresa not in ('practicante','microempresa')
			and hwd.code in (%s)
			group by hp.employee_id, hp.payslip_run_id
		"""%(fecha_inicio_nominas,
			fecha_fin_nominas,
			contrato.employee_id.id,
			','.join("'%s'"%(wd.codigo) for wd in parametros_gratificacion.cod_wds))
		self.env.cr.execute(sql)
		conceptos = self.env.cr.dictfetchall()

		verificar_meses, _ = helper_liquidacion.diferencia_meses_dias(
			fecha_inicio_nominas, fecha_fin_nominas)
		if len(conceptos) != verificar_meses:
			fecha_encontradas = ' '.join(['\t-'+x['name']+'\n' for x in conceptos])
			if not fecha_encontradas:
				fecha_encontradas = '"No tiene nominas"'
			raise UserError(
				'Error en GRATIFICACION: El empleado %s debe tener nominas desde:\n %s hasta %s pero solo tiene nominas en las siguientes fechas:\n %s \nfaltan %d nominas, subsanelas por favor ' % (
					contrato.employee_id.name_related, fecha_inicio_nominas, fecha_fin_nominas, fecha_encontradas, abs(len(
						conceptos) - (verificar_meses))
				))
		lines = []
		if contrato.hourly_worker:
			payslips = self.env['hr.payslip'].search([('employee_id','=',contrato.employee_id.id),
														('date_from','>=',rango_inicio_planilla),
														('date_to','<=',rango_fin_planilla)])
			for payslip in payslips:
				lines.append(next(iter(filter(lambda l:l.code == 'BAS',payslip.line_ids)),None))
			basico = sum([line.amount for line in lines])/6.0
		else:
			basico = helper_liquidacion.getBasicoByDate(date(fecha_fin_nominas.year,fecha_fin_nominas.month,1),fecha_fin_nominas,contrato.employee_id.id,parametros_gratificacion.cod_basico.code,True )  # conceptos[0].basico if conceptos else 0.0
		if parametros_gratificacion.cod_dias_faltas:
			faltas = helper_liquidacion.getSumFaltas(fecha_inicio_nominas,fecha_fin_nominas,contrato.employee_id.id,parametros_gratificacion.cod_dias_faltas.codigo ) #sum([x.dias_faltas for x in conceptos])
		else:
			faltas = 0
		afam = helper_liquidacion.getAsignacionFamiliarByDate(date(fecha_fin_nominas.year,fecha_fin_nominas.month,1),fecha_fin_nominas,contrato.employee_id.id,parametros_gratificacion.cod_asignacion_familiar.code )  #conceptos[0].asignacion_familiar if conceptos else 0.0

		comisiones_periodo, promedio_bonificaciones, promedio_horas_trabajo_extra = helper_liquidacion.calcula_comision_gratificacion_hrs_extras(
			contrato, fecha_inicio_nominas, fecha_fin_nominas, meses, fecha_fin)

		bonificacion_9 = 0
		bonificacion = promedio_bonificaciones
		comision = comisiones_periodo
		rem_computable = basico + bonificacion+comision + afam + promedio_horas_trabajo_extra
		if contrato.regimen_laboral_empresa == 'pequenhaempresa':
				rem_computable = rem_computable/2.0
		monto_x_mes = round(rem_computable/6.0, 2)
		monto_x_dia = round(monto_x_mes/30.0, 2)
		monto_x_meses = round(
			monto_x_mes*meses, 2) if meses != 6 else rem_computable
		monto_x_dias = round(monto_x_dia*dias, 2)
		total_faltas = round(monto_x_dia*faltas, 2)
		total_gratificacion = (monto_x_meses+monto_x_dias)-total_faltas

		if self.plus_9:
			if contrato.seguro_salud_id:
				bonificacion_9 =contrato.seguro_salud_id.porcentaje / \
					100.0*float(total_gratificacion)
		vals = {
			'planilla_liquidacion_id': self.id,
			'orden':e,
			'employee_id': contrato.employee_id.id,
			'identification_number': contrato.employee_id.identification_id,
			'last_name_father': contrato.employee_id.a_paterno,
			'last_name_mother': contrato.employee_id.a_materno,
			'names': contrato.employee_id.nombres,
			'fecha_ingreso': fecha_ini,
			'fecha_computable': fecha_computable,
			'fecha_cese': fecha_fin,
			'meses': meses,
			'dias': dias,
			'faltas': faltas,
			'basico': basico,
			'a_familiar': afam,
			'comision': comisiones_periodo,
			'bonificacion': bonificacion,
			'horas_extras_mean': promedio_horas_trabajo_extra,
			'remuneracion_computable': rem_computable,
			'monto_x_mes': monto_x_mes,
			'monto_x_dia': monto_x_dia,
			'monto_x_meses': monto_x_meses,
			'monto_x_dias': monto_x_dias,
			'total_faltas': total_faltas,
			'total_gratificacion': total_gratificacion,
			'plus_9': bonificacion_9,
			'total': total_gratificacion+bonificacion_9
		}

		self.planilla_gratificacion_lines.create(vals)
		return True

	@api.multi
	def calcular_cts(self, contrato, rango_inicio_planilla, rango_fin_planilla, fecha_ini, fecha_fin, date_start_liquidacion, date_end_liquidacion, anho_periodo_anterior_cts, tipo_cts,tipo_gratificacion,e):
		self.ensure_one()
		_logger.info('calcular_cts')
		ultimo_mes_no_cuenta = False
		helper_liquidacion = self.env['planilla.helpers']
		parametros_gratificacion = self.env['planilla.gratificacion'].get_parametros_gratificacion()

		# el resto se queda
		dias = 0
		dias_mes_cese = calendar.monthrange(
			int(fecha_fin.month), fecha_fin.month)[1]
		meses = 0
		if rango_inicio_planilla <= fecha_ini and rango_fin_planilla >= fecha_ini:
			fecha_computable = fecha_ini
		else:
			fecha_computable = rango_inicio_planilla

		_logger.info('diferencia_meses_dias')
		_logger.info(fecha_computable)
		_logger.info(fecha_fin)
		meses, dias = helper_liquidacion.diferencia_meses_dias(
			fecha_computable, fecha_fin)

		fecha_inicio_nominas = date(
			fecha_computable.year, fecha_computable.month, 1)
		fecha_fin_nominas = fecha_fin - relativedelta(months=0)
		fecha_fin_nominas = date(fecha_fin_nominas.year, fecha_fin_nominas.month, calendar.monthrange(
			fecha_fin_nominas.year, fecha_fin_nominas.month)[1])

		sql = """
			select min(hp.id),sum(hwd.number_of_days) as days,min(hp.name) as name
			from hr_payslip hp
			inner join hr_contract hc on hc.id = hp.contract_id
			inner join hr_payslip_worked_days hwd on hwd.payslip_id = hp.id
			where hp.date_from >= '%s'
			and hp.date_to <= '%s'
			and hp.employee_id = %d
			and hc.regimen_laboral_empresa not in ('practicante','microempresa')
			and hwd.code in (%s)
			group by hp.employee_id, hp.payslip_run_id
		"""%(fecha_inicio_nominas,
			fecha_fin_nominas,
			contrato.employee_id.id,
			','.join("'%s'"%(wd.codigo) for wd in parametros_gratificacion.cod_wds)
			)
		self.env.cr.execute(sql)
		conceptos = self.env.cr.dictfetchall()

		# meses-1#meses-1 if ultimo_mes_no_cuenta else meses
		verificar_meses, _ = helper_liquidacion.diferencia_meses_dias(
			fecha_inicio_nominas, fecha_fin_nominas)

		if len(conceptos) != verificar_meses:
			fecha_encontradas = ' '.join(
				['\t-'+x['name']+'\n' for x in conceptos])
			if not fecha_encontradas:
				fecha_encontradas = '"No tiene nominas"'
			raise UserError(
				'Error en CTS: El empleado %s debe tener nominas desde:\n %s hasta %s pero solo tiene nominas en las siguientes fechas:\n %s \nfaltan %d nominas, subsanelas por favor ' % (
					contrato.employee_id.name_related, fecha_inicio_nominas, fecha_fin_nominas, fecha_encontradas, abs(len(
						conceptos) - (verificar_meses))
				))
		lines = []
		if contrato.hourly_worker:
			payslips = self.env['hr.payslip'].search([('employee_id','=',contrato.employee_id.id),
														('date_from','>=',rango_inicio_planilla),
														('date_to','<=',rango_fin_planilla)])
			for payslip in payslips:
				lines.append(next(iter(filter(lambda l:l.code == 'BAS',payslip.line_ids)),None))
			basico = sum([line.amount for line in lines])/6.0
		else:
			basico = helper_liquidacion.getBasicoByDate(date(fecha_fin_nominas.year,fecha_fin_nominas.month,1),fecha_fin_nominas,contrato.employee_id.id,parametros_gratificacion.cod_basico.code,True)  # conceptos[0].basico if conceptos else 0.0
		if parametros_gratificacion.cod_dias_faltas:
			faltas = helper_liquidacion.getSumFaltas(fecha_inicio_nominas,fecha_fin_nominas,contrato.employee_id.id,parametros_gratificacion.cod_dias_faltas.codigo ) #sum([x.dias_faltas for x in conceptos])
		else:
			faltas = 0
		afam = helper_liquidacion.getAsignacionFamiliarByDate(date(fecha_fin_nominas.year,fecha_fin_nominas.month,1),fecha_fin_nominas,contrato.employee_id.id,parametros_gratificacion.cod_asignacion_familiar.code )  #conceptos[0].asignacion_familiar if conceptos else 0.0

		if fecha_fin.month == 7 and fecha_fin.day > 15:
			query_gratificacion = """
			select total_gratificacion/6.0 as gratificacion from planilla_gratificacion pg
			inner join planilla_gratificacion_line pgl
			on pgl.planilla_gratificacion_id= pg.id
			where employee_id =%d and year='%s' and tipo='%s'
			""" % (contrato.employee_id, fecha_fin.year, '07')
		else:
			query_gratificacion = """
			select total_gratificacion/6.0 as gratificacion from planilla_gratificacion pg
			inner join planilla_gratificacion_line pgl
			on pgl.planilla_gratificacion_id= pg.id
			where employee_id =%d and year='%s' and tipo='%s'
			""" % (contrato.employee_id, anho_periodo_anterior_cts, tipo_gratificacion)

		self.env.cr.execute(query_gratificacion)
		gratificacion = self.env.cr.dictfetchone()
		gratificacion = gratificacion['gratificacion'] if gratificacion else 0.0

		query_dias_pasados = """
		select dias_proxima_fecha as dias_cts_periodo_anterior from planilla_cts pc
		inner join planilla_cts_line pcl
		on pc.id= pcl.planilla_cts_id
		where employee_id=%d    and year='%s' and tipo='%s'
		""" % (contrato.employee_id, anho_periodo_anterior_cts, tipo_cts)

		self.env.cr.execute(query_dias_pasados)
		dias_cts_periodo_anterior = self.env.cr.dictfetchone()
		dias_cts_periodo_anterior = dias_cts_periodo_anterior[
			'dias_cts_periodo_anterior'] if dias_cts_periodo_anterior else 0
		dias = dias+dias_cts_periodo_anterior

		helper_liquidacion = self.env['planilla.helpers']
		comisiones_periodo, promedio_bonificaciones, promedio_horas_trabajo_extra = helper_liquidacion.calcula_comision_gratificacion_hrs_extras(
			contrato, fecha_computable, fecha_fin_nominas, meses, fecha_fin)

		bonificacion = promedio_bonificaciones
		comision = comisiones_periodo

		rem_computable = basico+afam + gratificacion + bonificacion + comision + promedio_horas_trabajo_extra
		if contrato.regimen_laboral_empresa == 'pequenhaempresa':
				rem_computable = rem_computable/2.0
		monto_x_mes = round(rem_computable/12.0, 2)
		monto_x_dia = round(monto_x_mes/30.0, 2)
		monto_x_meses = round(monto_x_mes*meses, 2)
		monto_x_dias = round(monto_x_dia*dias, 2)
		total_faltas = round(monto_x_dia*faltas, 2)

		cts_soles = monto_x_dias+monto_x_meses-total_faltas
		cts_interes = 0.0
		otros_dtos = 0.0
		cts_a_pagar = (cts_soles+cts_interes)-otros_dtos

		tipo_cambio_venta = self.tipo_cambio
		cts_dolares = round(cts_a_pagar/tipo_cambio_venta, 2)
		cuenta_cts = contrato.employee_id.bacts_acc_number_rel
		banco = contrato.employee_id.bacts_bank_id_rel.id

		vals = {
			'planilla_liquidacion_id': self.id,
			'orden':e,
			'employee_id': contrato.employee_id.id,
			'contract_id': contrato.id,
			'identification_number': contrato.employee_id.identification_id,
			'last_name_father': contrato.employee_id.a_paterno,
			'last_name_mother': contrato.employee_id.a_materno,
			'names': contrato.employee_id.nombres,
			'fecha_ingreso': fecha_ini,
			'fecha_computable': fecha_computable,
			'fecha_cese': fecha_fin,
			'basico': basico,
			'a_familiar': afam,
			'gratificacion': gratificacion,
			'horas_extras_mean': promedio_horas_trabajo_extra,
			'bonificacion': bonificacion,
			'comision': comisiones_periodo,
			'base': rem_computable,
			'monto_x_mes': monto_x_mes,
			'monto_x_dia': monto_x_dia,
			'faltas': faltas,
			'meses': meses,
			'dias': dias,
			'monto_x_meses': monto_x_meses,
			'monto_x_dias':  monto_x_dias,
			'total_faltas':  total_faltas,
			'cts_soles': cts_soles,
			'intereses_cts': cts_interes,
			'otros_dtos': otros_dtos,
			'cts_a_pagar': cts_a_pagar,
			'tipo_cambio_venta': tipo_cambio_venta,
			'cts_dolares': cts_dolares,
			'cta_cts': cuenta_cts,
			'banco': banco
		}

		self.planilla_cts_lines.create(vals)
		return True

	@api.multi
	def calcular_vacaciones(self, contrato, date_start_liquidacion, date_end_liquidacion, fecha_ini, fecha_fin,e):
		self.ensure_one()
		helper_liquidacion = self.env['planilla.helpers']
		parametros_gratificacion = self.env['planilla.gratificacion'].get_parametros_gratificacion()
		'''
			se toma como base el año actual por ejm si su contrato inicia 2015-05-13
			se tendria que cambiar a 2019-05-13 esto solo si el mes de la liquidacion
			es mayor al mes en que se esta iniciando el contrato
		'''
		if self.month >= fecha_ini.month:
			fecha_ini = date(int(self.year), fecha_ini.month, fecha_ini.day)
		else:
			fecha_ini = date(int(self.year)-1, fecha_ini.month, fecha_ini.day)

		fecha_computable = fecha_fin - relativedelta(months=+6)

		dias = 0
		dias_mes_cese = calendar.monthrange(
			int(fecha_fin.month), fecha_fin.month)[1]
		if fecha_computable < fecha_ini:
			fecha_computable = fecha_ini
		dias_del_mes_fin = calendar.monthrange(
			int(self.year), fecha_fin.month)[1]


		meses, _ = helper_liquidacion.diferencia_meses_dias(
			fecha_ini, fecha_fin)

		mes_tmp = date(fecha_fin.year, fecha_fin.month, fecha_ini.day)
		if mes_tmp > fecha_fin:
			dias = abs(mes_tmp-fecha_fin)+timedelta(days=1)
			dias = 31-dias.days
		else:
			if fecha_fin.day == dias_mes_cese and fecha_ini.day == 1:
				dias = 0
				meses += 1
			else:
				dias = abs(fecha_ini.day-fecha_fin.day)+1

		meses, dias = helper_liquidacion.diferencia_meses_dias(
			fecha_ini, fecha_fin)

		# 4 sacando basico afam y faltas
		if fecha_fin.month-fecha_ini.month == 0:
			# solo esta un mes o menos, no hay nomina anterior
			basico = contrato.wage
			faltas = 0.0
			afam = 0.0
			comisiones_periodo = 0.0
			promedio_bonificaciones = 0.0
			promedio_horas_trabajo_extra = 0.0
			fecha_computable = date(
				fecha_fin.year, fecha_ini.month, fecha_ini.day)
		else:
			fecha_inicio_nominas = date(fecha_ini.year, fecha_ini.month, 1)
			fecha_fin_nominas = fecha_fin - relativedelta(months=0)
			fecha_fin_nominas = date(fecha_fin_nominas.year, fecha_fin_nominas.month, calendar.monthrange(
				fecha_fin_nominas.year, fecha_fin_nominas.month)[1])

			sql = """
				select min(hp.id),sum(hwd.number_of_days) as days,min(hp.name) as name
				from hr_payslip hp
				inner join hr_contract hc on hc.id = hp.contract_id
				inner join hr_payslip_worked_days hwd on hwd.payslip_id = hp.id
				where hp.date_from >= '%s'
				and hp.date_to <= '%s'
				and hp.employee_id = %d
				and hc.regimen_laboral_empresa not in ('practicante','microempresa')
				and hwd.code in (%s)
				group by hp.employee_id, hp.payslip_run_id
			"""%(fecha_inicio_nominas,fecha_fin_nominas,contrato.employee_id.id,
				','.join("'%s'"%(wd.codigo) for wd in parametros_gratificacion.cod_wds))
			self.env.cr.execute(sql)
			conceptos = self.env.cr.dictfetchall()

			verificar_meses, _ = helper_liquidacion.diferencia_meses_dias(
				fecha_inicio_nominas, fecha_fin_nominas)

			if len(conceptos) != verificar_meses:
				fecha_encontradas = ' '.join(['\t-'+x['name']+'\n' for x in conceptos])
				if not fecha_encontradas:
					fecha_encontradas = '"No tiene nominas"'
				raise UserError(
					'Error en VACACIONES: El empleado %s debe tener nominas desde:\n %s hasta %s pero solo tiene nominas en las siguientes fechas:\n %s \nfaltan %d nominas, subsanelas por favor ' % (
						contrato.employee_id.name_related, fecha_inicio_nominas, fecha_fin_nominas, fecha_encontradas, abs(len(
							conceptos) - (verificar_meses))
					))
			if contrato.hourly_worker:
				payslips = self.env['hr.payslip'].search([('employee_id','=',contrato.employee_id.id),
															('date_from','>=',rango_inicio_planilla),
															('date_to','<=',rango_fin_planilla)])
				for payslip in payslips:
					lines.append(next(iter(filter(lambda l:l.code == 'BAS',payslip.line_ids)),None))
				basico = sum([line.amount for line in lines])/6.0
			else:
				basico = helper_liquidacion.getBasicoByDate(date(fecha_fin_nominas.year,fecha_fin_nominas.month,1),fecha_fin_nominas, contrato.employee_id.id,parametros_gratificacion.cod_basico.code,True)  # conceptos[0].basico if conceptos else 0.0

			if parametros_gratificacion.cod_dias_faltas:
				faltas = helper_liquidacion.getSumFaltas(fecha_inicio_nominas,fecha_fin_nominas, contrato.employee_id.id,parametros_gratificacion.cod_dias_faltas.codigo ) #sum([x.dias_faltas for x in conceptos])
			else:
				faltas = 0
			helper_liquidacion = self.env['planilla.helpers']
			meses_comisiones = fecha_fin.month-fecha_computable.month
			comisiones_periodo, promedio_bonificaciones, promedio_horas_trabajo_extra = helper_liquidacion.calcula_comision_gratificacion_hrs_extras(
				contrato, fecha_computable, fecha_fin_nominas, meses_comisiones, fecha_fin)

		bonificacion = promedio_bonificaciones
		comision = comisiones_periodo
		afam = 93.0 if contrato.employee_id.children > 0 else 0.0

		rem_computable = basico + afam + bonificacion + comision + promedio_horas_trabajo_extra
		if contrato.regimen_laboral_empresa == 'pequenhaempresa':
				rem_computable = rem_computable/2.0
		monto_x_mes = round(rem_computable/12.0, 2)
		monto_x_dia = round(monto_x_mes/30.0, 2)
		monto_x_meses = round(monto_x_mes*meses, 2)
		monto_x_dias = round(monto_x_dia*dias, 2)
		total_faltas = round(monto_x_dia*faltas, 2)

		vacaciones_truncas = monto_x_meses+monto_x_dias
		vacaciones_devengadas = 0
		total_vacaciones = vacaciones_truncas+vacaciones_devengadas

		afiliacion_lines = self.env['planilla.afiliacion.line'].search(
			[('fecha_ini', '=', date_start_liquidacion), ('fecha_fin', '=', date_end_liquidacion)])

		query_afiliacion = """
		select lower(pa.entidad) as entidad,pa.fondo,segi,comf,comm from planilla_afiliacion_line pal
		inner join planilla_afiliacion pa
		on pa.id = pal.planilla_afiliacion_id
		where fecha_ini= '%s' and fecha_fin ='%s' and planilla_afiliacion_id=%d
		""" % (date_start_liquidacion, date_end_liquidacion, contrato.afiliacion_id)

		self.env.cr.execute(query_afiliacion)
		afiliacion = self.env.cr.dictfetchone()
		onp = 0
		afp_jub = 0
		afp_si = 0
		afp_com = 0

		if contrato.afiliacion_id.entidad.lower() == 'onp':
			onp = contrato.afiliacion_id.fondo/100*total_vacaciones
		else:
			afp_jub = contrato.afiliacion_id.fondo/100*total_vacaciones
			afp_si = contrato.afiliacion_id.prima_s/100*total_vacaciones
			afp_com = contrato.afiliacion_id.com_mix/100*total_vacaciones

		neto_total = total_vacaciones - (onp+afp_jub+afp_si+afp_com)

		vals = {
			'planilla_liquidacion_id': self.id,
			'orden':e,
			'employee_id': contrato.employee_id.id,
			'contract_id': contrato.id,
			'identification_number': contrato.employee_id.identification_id,
			'last_name_father': contrato.employee_id.a_paterno,
			'last_name_mother': contrato.employee_id.a_materno,
			'names': contrato.employee_id.nombres,
			'fecha_ingreso': fecha_ini,
			'fecha_computable': fecha_computable,
			'fecha_cese': fecha_fin,
			'faltas': faltas,
			'basico': basico,
			'afam': afam,
			'comision': comision,
			'bonificacion': bonificacion,
			'horas_extras_mean': promedio_horas_trabajo_extra,
			'remuneracion_computable': rem_computable,
			'meses': meses,
			'dias': dias,
			'monto_x_mes': monto_x_meses,
			'monto_x_dia': monto_x_dias,
			'vacaciones_devengadas': '',
			'vacaciones_truncas': vacaciones_truncas,
			'total_vacaciones': total_vacaciones,
			'onp': onp,
			'afp_jub': afp_jub,
			'afp_si': afp_si,
			'afp_com': afp_com,
			'neto_total': neto_total
		}

		self.planilla_vacaciones_lines.create(vals)
		vals = {
			'planilla_liquidacion_id': self.id,
			'orden':e,
			'employee_id': contrato.employee_id.id,
			'contract_id': contrato.id,
			'identification_number': contrato.employee_id.identification_id,
			'last_name_father': contrato.employee_id.a_paterno,
			'last_name_mother': contrato.employee_id.a_materno,
			'names': contrato.employee_id.nombres,
			'fecha_ingreso': fecha_ini,
			'fecha_cese': fecha_fin,
		}
		self.planilla_indemnizacion_lines.create(vals)


		return True
