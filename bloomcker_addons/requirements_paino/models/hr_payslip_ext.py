from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
import logging
_logger = logging.getLogger(__name__)

class HrPayslipExtend(models.Model):
	_inherit = 'hr.payslip'
	_description = 'Pay Slip Extend'

	@api.multi
	def imprimir_boleta_xml(self):
		_logger.info('imprimir_xml')
		self.ensure_one()

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
		ingreso = SubElement(ingresos, 'ingreso')
		concepto = SubElement(ingreso, 'concepto')
		monto = SubElement(ingreso, 'monto')

		ciudad_fecha.text = "LIMA, 13 de Noviembre de 2018"
		datos_empleador.text = "PAINO SCARPATI JOSE ALFREDO"
		de.text = "46969060"
		nombres_apellidos.text = self.employee_id.name
		cargo.text = self.contract_id.job_id.name
		fecha_ingreso.text = self.employee_id.date_entry_bl
		entidad_depositaria.text = "FINANCIERA TFC"
		cuenta_dolares.text = "143004200137639"
		periodo_deposito_liquidar_del.text = "2018-05-01"
		periodo_deposito_liquidar_al.text = "2018-10-31"
		periodo_depositar_del.text = "2018-05-01"
		periodo_depositar_al.text = "2018-10-31"
		mes.text = "6"
		dia.text = "0"
		calculo_meses_laborados.text = "1400.00"
		calculo_dias_laborados.text = "0.00"
		importe_calculado.text = "1400.00"
		total.text = "2800.00"
		tipo_cambio.text = "3.3610"
		importe_depositado_dolares.text = "416.54"
		importe_letras.text = "CUATROCIENTOS DIEC Y SEIS Y 54/100 DOLARES AMERICANOS"
		concepto.text = "SEULDO BASICO"
		monto.text = "2400.00"

		vals = {
			'output_name': 'output.xml',
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
