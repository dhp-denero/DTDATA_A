from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from numero_letras import numero_a_letras, numero_a_moneda
import logging
_logger = logging.getLogger(__name__)

class HrPayslipExtend(models.Model):
	_inherit = 'hr.payslip'
	_description = 'Pay Slip Extend'

	@api.multi
	def imprimir_boleta_xml(self):
		self.ensure_one()

		records = Element('records')
		record = SubElement(records, 'record')
		documento_identidad = SubElement(record, 'documento_identidad')
		tipo = SubElement(documento_identidad, 'tipo')
		de = SubElement(documento_identidad, 'de')
		codigo = SubElement(record, 'codigo')
		mesyanho = SubElement(record, 'mesyanho')
		nombres = SubElement(record, 'nombres')
		dni = SubElement(record, 'dni')
		fingreso = SubElement(record, 'fingreso')
		fcese = SubElement(record, 'fcese')
		dvac = SubElement(record, 'dvac')
		dsub = SubElement(record, 'dsub')
		ddme = SubElement(record, 'ddme')
		hlab = SubElement(record, 'hlab')
		hequarto = SubElement(record, 'hequarto')
		hetrigquinto = SubElement(record, 'hetrigquinto')
		heciento = SubElement(record, 'heciento')
		basico = SubElement(record, 'basico')
		tcontrato = SubElement(record, 'tcontrato')
		vacini = SubElement(record, 'vacini')
		vacfin = SubElement(record, 'vacfin')
		oficina = SubElement(record, 'oficina')
		regpensionario = SubElement(record, 'regpensionario')
		cuspp = SubElement(record, 'cuspp')
		banco = SubElement(record, 'banco')
		nrocta = SubElement(record, 'nrocta')
		dfalta = SubElement(record, 'dfalta')
		dtrabajados = SubElement(record, 'dtrabajados')
		totalingresos = SubElement(record, 'totalingresos')
		totaldescuentos = SubElement(record, 'totaldescuentos')
		totalaportes = SubElement(record, 'totalaportes')
		totalneto = SubElement(record, 'totalneto')
		vacfin = SubElement(record, 'vacfin')

		for line in self.worked_days_line_ids:
			if line.code == "DVAC":
				dvac = line.number_of_days
			elif line.code == "DESUBE":
				dsube = line.number_of_days
			elif line.code == "DSUBM":
				dsubm = line.number_of_days
			elif line.code == "DLAB":
				dlab = line.number_of_days

		# for line in self.line_ids:



		tipo.text = self.employee_id.tablas_tipo_documento_id.codigo_sunat
		de.text = self.employee_id.identification_id
		codigo = self.employee_id.identification_id
		nombres.text = self.employee_id.name
		dni.text = self.employee_id.identification_id
		fingreso.text = self.employee_id.date_entry_bl
		fcese.text = self.employee_id.date_end_bl
		# dvac.text =


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
