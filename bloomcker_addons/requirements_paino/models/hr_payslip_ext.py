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
		lsgh = SubElement(record, 'lsgh')
		basico = SubElement(record, 'basico')
		tcontrato = SubElement(record, 'tcontrato')
		cargo = SubElement(record, 'cargo')
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
		ingresos = SubElement(record, 'ingresos')
		descuentos = SubElement(record, 'descuentos')
		aportaciones = SubElement(record, 'aportaciones')

		dvacn = dsuben = dsubmn = dlabn = he25n = he35n = he100n = faln = 0
		tingr = tdes = totapor = net = 0

		for line in self.worked_days_line_ids:
			if line.code == "DVAC":
				dvacn = line.number_of_days
			elif line.code == "DESUBE":
				dsuben = line.number_of_days
			elif line.code == "DSUBM":
				dsubmn = line.number_of_days
			elif line.code == "DLAB":
				dlabn = line.number_of_days
			elif line.code == "HE25":
				he25n = line.number_of_hours
			elif line.code == "HE100":
				he100n = line.number_of_hours
			elif line.code == "HE35":
				he35n = line.number_of_hours
			elif line.code == "FAL":
				faln = line.number_of_days

		for line in self.line_ids:
			if line.code == "TINGR":
				tingr = line.total
			elif line.code == "TDES":
				tdes = line.total
			elif line.code == "TOTAPOR":
				totapor = line.total
			elif line.code == "NET":
				net = line.total

		tipo.text = self.employee_id.tablas_tipo_documento_id.codigo_sunat
		de.text = self.employee_id.identification_id
		codigo.text = self.employee_id.identification_id
		mesyanho.text = "PRUEBA - BOLETA DE PAGO DE REMUNERACIONES D.S.N°001-98TR MES" + "ABRIL" + "DEL" + "2021"
		nombres.text = self.employee_id.name
		dni.text = self.employee_id.identification_id
		fingreso.text = self.employee_id.date_entry_bl
		fcese.text = self.employee_id.date_end_bl
		dvac.text = str(int(dvacn))
		dsub.text = str(int(dsuben))
		ddme.text = str(int(dsubmn))
		lsgh.text = "0"
		hlab.text = str(int(dlabn*8))
		hequarto.text = str(int(he25n))
		hetrigquinto.text = str(int(he35n))
		heciento.text = str(int(he100n))
		basico.text = str(self.contract_id.wage)
		tcontrato.text = self.contract_id.type_id.name
		cargo.text = self.contract_id.job_id.name
		oficina.text = "NOTARIA"
		cuspp.text = str(self.contract_id.cuspp)
		banco.text = self.employee_id.bank_account_id_bank_id_rel.name
		nrocta.text = self.employee_id.bank_account_id_acc_number_rel
		dfalta.text = str(int(faln))
		dtrabajados.text = str(int(dlabn))
		totalingresos.text = str(tingr)
		totaldescuentos.text = str(tdes)
		totalaportes.text = str(totapor)
		totalneto.text = str(net)

		for line in self.line_ids:
			if line.category_id.code == "ING" and line.total:
				ingreso = SubElement(ingresos, 'ingreso')
				idetalle = SubElement(ingreso, 'idetalle').text = line.name
				imonto = SubElement(ingreso, 'imonto').text = str(line.total)
			elif line.category_id.code == "DES_NET" and line.total:
				descuento = SubElement(descuentos, 'descuento')
				ddetalle = SubElement(descuento, 'ddetalle').text = line.name
				dmonto = SubElement(descuento, 'dmonto').text = str(line.total)
			elif line.category_id.code == "APOR_TRA" and line.total:
				aportacione = SubElement(aportaciones, 'aportacione')
				adetalle = SubElement(aportacione, 'adetalle').text = line.name
				amonto = SubElement(aportacione, 'amonto').text = str(line.total)

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
