# -*- encoding: utf-8 -*-
from odoo import models, fields, api , exceptions
from odoo.exceptions import UserError
import base64
from datetime import datetime
from functools import reduce

class multipayment_advance_invoice(models.Model):
	_inherit = 'multipayment.advance.invoice'

	account_bank_id = fields.Many2one('res.partner.bank','Cta. Bancaria Pago')		


	def export_telebank(self):
		if self.account_bank_id.id:
			ndocs = 0
			ntot = 0
			for l in self.invoice_ids:
				l.make_fields_values_report()
				ndocs=ndocs+1
				ntot = ntot + float(l.amount_payment)
			wizard_form = self.env.ref('account_payment_bank_export_it.view_export_multipayment_bank_wizard_form', False)
			view_id = self.env['export.multipayment.wizard']

			dd=self.env['export.report.head'].search([('bank_id','=',self.account_bank_id.bank_id.id)])
			bank_r = False
			if len(dd)>0:
				bank_r=dd[0].id
			vals = {
						'report_type':bank_r,
						'date_pay':self.payment_date,
						'bank_acc':self.account_bank_id.acc_number,
						'amount_total':str(ntot),
						'qty_abonos':str(ndocs),
						'ref':'Pagos a proveedores'
					}
			new = view_id.create(vals)
			c={
						'name'	  : 'Exportar Pagos',
						'type'	  : 'ir.actions.act_window',
						'res_model' : 'export.multipayment.wizard',
						'res_id'	: new.id,
						'view_id'   : wizard_form.id,
						'view_type' : 'form',
						'view_mode' : 'form',
						'target'	: 'new'
					}
			print(c)
			return c
		else:
			raise UserError('Seleccione una cuenta bancaria en la pestaña "Otra Información"')		
	



class MultipaymentAdvanceInvoiceLine(models.Model):
	_inherit = 'multipayment.advance.invoice.line'

	account_bank_id = fields.Many2one('res.partner.bank','Cta. Bancaria')

	record_type = fields.Char('Tipo de registro')
	payment_form = fields.Char('Forma de Pago')
	account_number = fields.Char('Nro. Cuenta')
	cci = fields.Char('CCI')
	tdocpartner= fields.Char('Tipo de Documento de Identidad')
	numdocpartner = fields.Char('Número de Documento de Identidad')
	correlativo_partner=fields.Char('Correlativo Provbedor',default='')
	partner_name = fields.Char('Nombre Proveedor')
	currency_name = fields.Char('Tipo Moneda a pagar')
	amount_payment_subtot = fields.Char('Sub total de monto a pagar')
	idc_validator = fields.Char('Validación IDC del proveedor vs Cuenta')
	doc_rel_qty = fields.Char('Cantidad Documentos relacionados al Abono')
	pay_doc_type = fields.Char('Tipo de Documento a pagar')
	doc_number_pay = fields.Char('Nro. del Documento')
	currency_doc_name = fields.Char('Tipo Moneda del comprobante')
	amount_payment = fields.Char('Monto del Documento')
	group_payment = fields.Char('Abono Agrupado')
	ref_report = fields.Char('Referencia')
	notify_report= fields.Char('Indicador Aviso')
	notify_method= fields.Char('Medio de aviso')
	contact_name= fields.Char('Persona Contacto')
	email_report= fields.Char('correo electrónico')




	@api.onchange('partner_id')
	def onchange_partner(self):
		if self.partner_id.id:
			c = self.env['res.partner.bank'].search([('partner_id','=',self.partner_id.id)])
			if len(c)>0:
				self.account_bank_id = c[0]

	def make_fields_values_report(self):
		# record_type

		if self.main_id.account_bank_id.id and self.account_bank_id:
			main_acc =self.main_id.account_bank_id
						
			for l in self.account_bank_id.export_type_acc:
				if l.bank_id.id == main_acc.bank_id.id:
					self.payment_form=l.cod_type_acc
			
			if self.account_bank_id.bank_id.id == main_acc.bank_id.id:
				self.account_number=self.account_bank_id.acc_number
				self.cci=''
			else:
				self.account_number=self.account_bank_id.acc_icc_number.replace('-','').replace(' ','')
				self.cci=self.account_bank_id.acc_icc_number.replace('-','').replace(' ','')

			r = self.env['export.typedoc.partner'].search([('bank_id','=',main_acc.bank_id.id),
				('type_doc_partner_id','=',self.partner_id.type_document_partner_it.id)])
			if len(r)>0:
				self.tdocpartner=r[0].code_type_doc

			self.numdocpartner=self.partner_id.nro_documento
			self.partner_name=self.partner_id.name

			r = self.env['export.currency'].search([('bank_id','=',main_acc.bank_id.id),
					('currency_id','=',main_acc.currency_id.id)])
			if len(r)>0:
				self.currency_name=r[0].code_currency

			# amount_payment_subtot
			
			self.idc_validator='N'
			# doc_rel_qty
			r = self.env['export.typedoc.invoice'].search([('bank_id','=',main_acc.bank_id.id),
					('type_doc_invoice_id','=',self.invoice_id.type_document_it.id)])
			if len(r)>0:
				self.pay_doc_type=r[0].code_type_doc

			if self.invoice_id.id:
				self.doc_number_pay=self.invoice_id.ref.replace('-','').replace(' ','')

			self.currency_doc_name='S'
			r = self.env['export.currency'].search([('bank_id','=',main_acc.bank_id.id),
					('currency_id','=',self.invoice_id.currency_id.id)])
			if len(r)>0:
				self.currency_doc_name=r[0].code_currency

			
			self.amount_payment=str(abs(self.debe-self.haber))

			self.group_payment='N'
			
			self.ref_report='PAGO DE PROVEEDORES'
			self.notify_report='E' if self.invoice_id.partner_id.email else ''
			self.notify_method=self.invoice_id.partner_id.email if self.invoice_id.partner_id.email else ''
			self.contact_name=self.partner_id.name if self.invoice_id.partner_id.email else ''
			self.email_report=self.invoice_id.partner_id.email if self.invoice_id.partner_id.email else ''


			print('==========')
			print('record_type',self.record_type)
			print('payment_form',self.payment_form)
			print('account_number',self.account_number)
			print('cci',self.cci)
			print('tdocpartner',self.tdocpartner)
			print('numdocpartner',self.numdocpartner)
			print('partner_name',self.partner_name)
			print('currency_name',self.currency_name)
			print('amount_payment_subtot',self.amount_payment_subtot)
			print('idc_validator',self.idc_validator)
			print('doc_rel_qty',self.doc_rel_qty)
			print('pay_doc_type',self.pay_doc_type)
			print('doc_number_pay',self.doc_number_pay)
			print('currency_doc_name',self.currency_doc_name)
			print('amount_payment',self.amount_payment)
			print('group_payment',self.group_payment)
			print('ref_report',self.ref_report)
			print('notify_report',self.notify_report)
			print('notify_method',self.notify_method)
			print('contact_name',self.contact_name)
			print('email_report',self.email_report)
			print('==========')



