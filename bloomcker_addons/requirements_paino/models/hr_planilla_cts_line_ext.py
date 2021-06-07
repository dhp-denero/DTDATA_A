from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from numero_letras import numero_a_letras, numero_a_moneda
from datetime import datetime, timedelta
import logging
import locale
_logger = logging.getLogger(__name__)

class HrPlanillaCtsLineExtend(models.Model):
	_inherit = 'planilla.cts.line'
	_description = 'Planilla CTS Line Extend'

	@api.multi
	def imprimir_cts_xml(self):
		self.ensure_one()

		month = ['0','Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Setiembre','Octubre','Noviembre','Diciembre']
		now = datetime.now()
		records = Element('records')
		record = SubElement(records, 'record')
		ciudad_fecha = SubElement(record, 'ciudad_fecha')
		datos_empleador = SubElement(record, 'datos_empleador')
		de = SubElement(record, 'de')
		nombres_apellidos = SubElement(record, 'nombres_apellidos')
		cargo = SubElement(record, 'cargo')
		fecha_ingreso = SubElement(record, 'fecha_ingreso')
		entidad_depositaria = SubElement(record, 'entidad_depositaria')
		cuenta_soles = SubElement(record, 'cuenta_soles')
		cuenta_dolares = SubElement(record, 'cuenta_dolares')
		periodo_deposito_liquidar_del = SubElement(record, 'periodo_deposito_liquidar_del')
		periodo_deposito_liquidar_al = SubElement(record, 'periodo_deposito_liquidar_al')
		periodo_depositar_del = SubElement(record, 'periodo_depositar_del')
		periodo_depositar_al = SubElement(record, 'periodo_depositar_al')
		mes = SubElement(record, 'mes')
		dia = SubElement(record, 'dia')
		calculo_meses_laborados = SubElement(record, 'calculo_meses_laborados')
		calculo_dias_laborados = SubElement(record, 'calculo_dias_laborados')
		importe_calculado = SubElement(record, 'importe_calculado')
		total = SubElement(record, 'total')
		tipo_cambio = SubElement(record, 'tipo_cambio')
		importe_depositado_dolares = SubElement(record, 'importe_depositado_dolares')
		importe_letras = SubElement(record, 'importe_letras')
		ingresos = SubElement(record, 'ingresos')
		ingreso1 = SubElement(ingresos, 'ingreso')
		concepto1 = SubElement(ingreso1, 'concepto')
		monto1 = SubElement(ingreso1, 'monto')
		ingreso2 = SubElement(ingresos, 'ingreso')
		concepto2 = SubElement(ingreso2, 'concepto')
		monto2 = SubElement(ingreso2, 'monto')
		ingreso3 = SubElement(ingresos, 'ingreso')
		concepto3 = SubElement(ingreso3, 'concepto')
		monto3 = SubElement(ingreso3, 'monto')
		ingreso4 = SubElement(ingresos, 'ingreso')
		concepto4 = SubElement(ingreso4, 'concepto')
		monto4 = SubElement(ingreso4, 'monto')
		ingreso5 = SubElement(ingresos, 'ingreso')
		concepto5 = SubElement(ingreso5, 'concepto')
		monto5 = SubElement(ingreso5, 'monto')
		ingreso6 = SubElement(ingresos, 'ingreso')
		concepto6 = SubElement(ingreso6, 'concepto')
		monto6 = SubElement(ingreso6, 'monto')

		ciudad_fecha.text = "LIMA, " + str(now.day )+ ' de ' + month[now.month] + ' de ' + str(now.year)
		datos_empleador.text = "PAINO SCARPATI JOSE ALFREDO"
		de.text = self.employee_id.identification_id
		nombres_apellidos.text = self.employee_id.name_total
		cargo.text = self.employee_id.job_id.name
		fecha_ingreso.text = self.employee_id.date_entry_bl
		entidad_depositaria.text = self.banco.name
		cuenta_dolares.text = self.cta_cts
		periodo_deposito_liquidar_del.text = self.planilla_cts_id.date_start
		periodo_deposito_liquidar_al.text = self.planilla_cts_id.date_end
		periodo_depositar_del.text = self.planilla_cts_id.date_start
		periodo_depositar_al.text = self.planilla_cts_id.date_end
		mes.text = str(self.meses)
		dia.text = str(self.dias)
		calculo_meses_laborados.text = str(self.monto_x_meses)
		calculo_dias_laborados.text = str(self.monto_x_dias)
		importe_calculado.text = str(self.cts_soles)
		total.text = str(self.cts_a_pagar)
		tipo_cambio.text = str(self.tipo_cambio_venta)
		importe_depositado_dolares.text = str(self.cts_dolares)
		importe_letras.text = numero_a_letras(self.cts_dolares).upper() + ' DOLARES AMERICANOS'
		concepto1.text = "SUELDO BASICO"
		monto1.text = str(self.basico)
		concepto2.text = "ASIGNACION FAMILIAR"
		monto2.text = str(self.a_familiar)
		concepto3.text = "GRATIFICACION (GRAT)"
		monto3.text = str(self.gratificacion)
		concepto4.text = "HORAS EXTRAS"
		monto4.text = str(self.horas_extras_mean)
		concepto5.text = "BONIFICACION"
		monto5.text = str(self.bonificacion)
		concepto6.text = "COMISION"
		monto6.text = str(self.comision)

		vals = {
			'output_name': 'cts_tmp.xml',
			'output_file': tostring(records).encode("base64"),
		}
		sfs_id = self.env['planilla.export.file'].create(vals)
		return {
			"type": "ir.actions.act_window",
			"res_model": "planilla.export.file",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}
