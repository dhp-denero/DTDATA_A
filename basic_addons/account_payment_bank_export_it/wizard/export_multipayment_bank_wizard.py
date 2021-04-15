# -*- encoding: utf-8 -*-
import base64
from odoo import models, fields, api
import codecs
import pprint
from datetime import *
from odoo.exceptions import UserError, ValidationError

class export_multipayment_wizard(models.TransientModel):
	_name='export.multipayment.wizard'
	
	report_type = fields.Many2one('export.report.head','Tipo Reporte')
	date_pay = fields.Date('Fecha de pago')
	bank_acc = fields.Char('Cuenta de Cargo')
	amount_total = fields.Char('Monto Total de Planilla')
	qty_abonos = fields.Char('Cantidad de abonos planilla')
	ref = fields.Char('Referencia',default='Pagos a proveedores')
	type_acc = fields.Char('Tipo de cuenta de cargo')
	lines_ids = fields.One2many('export.multipayment.wizard.lines','main_id','detalle')

	def prepare_data(self):
		lastlist=[]
		if self.report_type.group_4_partner:
			apartners = []
			n_operations=0
			total = 0
			
			for l in self.env['multipayment.advance.invoice'].browse(self._context['active_id']).invoice_ids:
				if l.partner_id.id not in apartners:
					apartners.append(l.partner_id.id)
			for o in apartners:
				amount_doc =0
				nmovs=0
				yahead=[]
				elementos=self.env['multipayment.advance.invoice.line'].search([('main_id','=',self._context['active_id']),('partner_id','=',o)],order='partner_id')
				linesappend=[]
				for deta in elementos:
					# solo voy a tomar facturas
					if deta.invoice_id.type_document_it.code in ['01','03','02','00','10']:
						yahead.append(deta)
				yahead = set(yahead)
				for deta in yahead:
					nmovs=nmovs+1
					if deta.importe_divisa!=0:
						total=total+abs(deta.amount_currency)
						amount_doc=amount_doc+abs(deta.importe_divisa)
					else:
						total=total+abs(deta.debe)-abs(deta.haber)
						amount_doc=amount_doc+abs(deta.debe)-abs(deta.haber)	
					vals = {
						'record_type':'D',
						'payment_form':'',
						'account_number':'',
						'cci':'',
						'tdocpartner':'',
						'numdocpartner':'',
						'correlativo_partner':'',
						'partner_name':'',
						'currency_name':'',
						'amount_payment_subtot':'',
						'idc_validator':'',
						'doc_rel_qty':'',
						'pay_doc_type':deta.pay_doc_type,
						'doc_number_pay':deta.doc_number_pay,
						'currency_doc_name':deta.currency_doc_name,
						'amount_payment':"{:.2f}".format(float(deta.amount_payment)),
						'group_payment':'',
						'ref_report':'',
						'notify_report':'',
						'notify_method':'',
						'contact_name':'',
						'email_report':'',
					}
					linesappend.append(vals)




				vals = {
					'record_type':'A',
					'payment_form':deta.payment_form,
					'account_number':deta.account_number,
					'cci':'',
					'tdocpartner':deta.tdocpartner,
					'numdocpartner':deta.numdocpartner,
					'correlativo_partner':'',
					'partner_name':deta.partner_name,
					'currency_name':deta.currency_name,
					'amount_payment_subtot':"{:.2f}".format(amount_doc),
					'idc_validator':deta.idc_validator,
					'doc_rel_qty':str(nmovs).rjust(4,'0'),
					'pay_doc_type':'',
					'doc_number_pay':'',
					'currency_doc_name':'',
					'amount_payment':'',
					'group_payment':'',
					'ref_report':'',
					'notify_report':'',
					'notify_method':'',
					'contact_name':'',
					'email_report':'',
				}
				lastlist.append(vals)
				for jlst in linesappend:
					lastlist.append(jlst)
		else:
			elementos=self.env['multipayment.advance.invoice.line'].search([('main_id','=',self._context['active_id'])],order='partner_id')
			for deta in elementos:
				print(deta)
				vals = {
					'record_type':'A',
					'payment_form':deta.payment_form,
					'account_number':deta.account_number if deta.cci=='' else '',
					'cci':deta.cci if deta.cci!='' else '',
					'tdocpartner':deta.tdocpartner,
					'numdocpartner':deta.numdocpartner,
					'correlativo_partner':'',
					'partner_name':deta.partner_name,
					'currency_name':deta.currency_name,
					'amount_payment_subtot':'',
					'idc_validator':deta.idc_validator,
					'doc_rel_qty':'',
					'pay_doc_type':deta.pay_doc_type,
					'doc_number_pay':deta.doc_number_pay,
					'currency_doc_name':deta.currency_doc_name,
					'amount_payment':deta.amount_payment,
					'group_payment':deta.group_payment,
					'ref_report':deta.doc_number_pay,
					'notify_report':deta.notify_report,
					'notify_method':deta.notify_method,
					'contact_name':deta.contact_name,
					'email_report':deta.email_report,
				}
				lastlist.append(vals)
		for l in lastlist:
			l.update({'main_id':self.id})
			self.env['export.multipayment.wizard.lines'].create(l)
		return lastlist

	@api.multi
	def do_rebuild(self):


		import io
		from xlsxwriter.workbook import Workbook
		from xlsxwriter.utility import xl_rowcol_to_cell

		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		workbook = Workbook( direccion + 'tempo_reportcajabanco.xlsx')
		worksheet = workbook.add_worksheet("Exportar a bancos")
		bold = workbook.add_format({'bold': True})

		bold_title = workbook.add_format({'bold': True,'align': 'center','valign': 'vcenter'})
		bold_title.set_font_size(14)
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		boldbord.set_text_wrap()
		boldbord.set_font_size(9)
		boldbord.set_bg_color('#DCE6F1')
		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		bord = workbook.add_format()
		bord.set_border(style=1)
		numberdos.set_border(style=1)
		numbertres.set_border(style=1)			
		x= 10				
		tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		tam_letra = 1
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		compania_obj = self.env['res.company'].search([])[0]


		lastlist = self.prepare_data()

		 

		
		
		
		worksheet.write(0,4,u'Exportación de pagos',bold_title)
		


		worksheet.write(2,0,'Expotado para:',bold)
		worksheet.write(3,0,'Fecha de Pago',bold)
		worksheet.write(4,0,'Cuenta Cargo',bold)
		worksheet.write(5,0,'Total',bold)
		worksheet.write(6,0,'Cantidad de Pagos',bold)
		worksheet.write(7,0,'Referencia',bold)

		worksheet.write(2,1,self.report_type.name)
		worksheet.write(3,1,self.date_pay)
		worksheet.write(4,1,self.bank_acc)
		worksheet.write(5,1,self.amount_total)
		worksheet.write(6,1,self.qty_abonos)
		worksheet.write(7,1,self.ref)



		fields_names = []


		y=0
		for l in self.env['export.report.field'].search([('report_id','=',self.report_type.id)],order="position"):
			fields_names.append(l.name.field_id.name)
			worksheet.write(8,y,l.name.name,boldbord)
			y=y+1

		for line in lastlist:
			y=0
			for f in fields_names:
				worksheet.write(x,y,line[f])
				y=y+1
			x = x +1

	


		worksheet.set_column('A:A', 20)
		worksheet.set_column('B:B',20 )
		worksheet.set_column('C:C',20 )
		worksheet.set_column('D:D',20 )
		worksheet.set_column('E:E',20 )
		worksheet.set_column('F:F',20 )
		worksheet.set_column('G:G', 20)
		worksheet.set_column('H:H', 20)
		worksheet.set_column('I:I', 20)
		worksheet.set_column('J:J', 20)
		worksheet.set_column('K:K', 20)
		worksheet.set_column('L:L', 20)
		worksheet.set_column('M:M', 20)
		worksheet.set_column('N:N', 20)
		worksheet.set_column('O:O', 20)
		worksheet.set_column('P:P', 20)

		workbook.close()
		
		f = open(direccion + 'tempo_reportcajabanco.xlsx', 'rb')
		
		
		vals = {
			'output_name': 'Exportado para pagos.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		sfs_id = self.env['export.file.save'].create(vals)
		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    "views": [[False, "form"]],
		    "res_id": sfs_id.id,
		    "target": "new",
		}
	


class export_multipayment_wizard_lines(models.TransientModel):
	_name='export.multipayment.wizard.lines'

	main_id = fields.Many2one('export.multipayment.wizard','main')
	
	record_type 			= fields.Char('Tipo de registro')
	payment_form 			= fields.Char('Forma de Pago')
	account_number			= fields.Char('Nro. Cuenta')
	cci 					= fields.Char('CCI')
	tdocpartner				= fields.Char('Tipo de Documento de Identidad')
	numdocpartner 			= fields.Char('Número de Documento de Identidad')
	correlativo_partner		= fields.Char('Correlativo Provbedor',default='')
	partner_name 			= fields.Char('Nombre Proveedor')
	currency_name 			= fields.Char('Tipo Moneda a pagar')
	amount_payment_subtot 	= fields.Char('Sub total de monto a pagar')
	idc_validator 			= fields.Char('Validación IDC del proveedor vs Cuenta')
	doc_rel_qty 			= fields.Char('Cantidad Documentos relacionados al Abono')
	pay_doc_type 			= fields.Char('Tipo de Documento a pagar')
	doc_number_pay 			= fields.Char('Nro. del Documento')
	currency_doc_name 		= fields.Char('Tipo Moneda del comprobante')
	amount_payment 			= fields.Char('Monto del Documento')
	group_payment 			= fields.Char('Abono Agrupado')
	ref_report 				= fields.Char('Referencia')
	notify_report			= fields.Char('Indicador Aviso')
	notify_method			= fields.Char('Medio de aviso')
	contact_name			= fields.Char('Persona Contacto')
	email_report			= fields.Char('correo electrónico')