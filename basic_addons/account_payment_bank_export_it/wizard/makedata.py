# -*- encoding: utf-8 -*-
import base64
from odoo import models, fields, api
import codecs
import pprint
from datetime import *
from odoo.exceptions import UserError, ValidationError

class export_makedata_wizard(models.TransientModel):
	_name='export.makedata.wizard'


	bank_bcp=fields.Many2one('res.bank','Banco BCP')
	bank_bbva=fields.Many2one('res.bank','Banco BBVA')
	bank_scotia=fields.Many2one('res.bank','Banco SCOTIA')


	def create_data(self):
		avalstc=[]
		model_tc = self.env['export.bank.acctype']
		
		avalstd=[]
		model_td = self.env['export.typedoc.partner']

		avalsti=[]
		model_ti = self.env['export.typedoc.invoice']

		avalscu=[]
		model_cu = self.env['export.currency']
		if len(model_tc.search([]))>0:
			raise UserError(u'Existen datos en /Contabilidad/Conficuración/Pagos/Exportar Pagos/Tipos de cuenta')		
		if len(model_td.search([]))>0:
			raise UserError(u'Existen datos en /Contabilidad/Conficuración/Pagos/Exportar Pagos/Documento de Identidad')		
		if len(model_ti.search([]))>0:
			raise UserError(u'Existen datos en /Contabilidad/Conficuración/Pagos/Exportar Pagos/Tipo de Comprobante')					
		if len(model_cu.search([]))>0:
			raise UserError(u'Existen datos en /Contabilidad/Conficuración/Pagos/Exportar Pagos/Equivalente Monedas')		
		if len(self.env['export.field.usable'].search([]))>0:
			raise UserError(u'Existen datos en /Contabilidad/Conficuración/Pagos/Exportar Pagos/Campos Disponibles')		

		
		c = self.env['einvoice.catalog.06'].search([('code','in',['1','4','6','7'])])
		d = self.env['einvoice.catalog.01'].search([('code','in',['01','07','08','00','03'])])
		e = self.env['res.currency'].search([('name','in',['PEN','USD'])])
		if self.bank_bcp.id:
			avalstc.append({
					'bank_id':self.bank_bcp.id,
					'type_acc':'Corriente',
					'cod_type_acc':'C'
				})
			avalstc.append({
					'bank_id':self.bank_bcp.id,
					'type_acc':'Maestra',
					'cod_type_acc':'M'
				})
			avalstc.append({
					'bank_id':self.bank_bcp.id,
					'type_acc':'Ahorros',
					'cod_type_acc':'A'
				})
			avalstc.append({
					'bank_id':self.bank_bcp.id,
					'type_acc':'Interbancario',
					'cod_type_acc':'B'
				})


			for l in c:
				if l.code=='6':
					avalstd.append({
						'bank_id':self.bank_bcp.id,
						'type_doc_partner_id':l.id,
						'code_type_doc':'6'
					})					
				if l.code=='1':
					avalstd.append({
						'bank_id':self.bank_bcp.id,
						'type_doc_partner_id':l.id,
						'code_type_doc':'1'
					})					
				if l.code=='4':
					avalstd.append({
						'bank_id':self.bank_bcp.id,
						'type_doc_partner_id':l.id,
						'code_type_doc':'3'
					})								
				if l.code=='7':
					avalstd.append({
						'bank_id':self.bank_bcp.id,
						'type_doc_partner_id':l.id,
						'code_type_doc':'4'
					})					

			for l in d:
				if l.code=='00':
					avalsti.append({
						'bank_id':self.bank_bcp.id,
						'type_doc_invoice_id':l.id,
						'code_type_doc':'D'
					})					
				if l.code=='01':
					avalsti.append({
						'bank_id':self.bank_bcp.id,
						'type_doc_invoice_id':l.id,
						'code_type_doc':'F'
					})					
				if l.code=='07':
					avalsti.append({
						'bank_id':self.bank_bcp.id,
						'type_doc_invoice_id':l.id,
						'code_type_doc':'N'
					})								
				if l.code=='08':
					avalsti.append({
						'bank_id':self.bank_bcp.id,
						'type_doc_invoice_id':l.id,
						'code_type_doc':'C'
					})					


			for l in e:
				if l.name=='PEN':
					avalscu.append({
						'bank_id':self.bank_bcp.id,
						'currency_id':l.id,
						'code_currency':'S'
					})					
				if l.name=='USD':
					avalscu.append({
						'bank_id':self.bank_bcp.id,
						'currency_id':l.id,
						'code_currency':'D'
					})					





		if self.bank_bbva.id:
			
			avalstc.append({
					'bank_id':self.bank_bbva.id,
					'type_acc':'Propio en Banco',
					'cod_type_acc':'P'
				})
			avalstc.append({
					'bank_id':self.bank_bbva.id,
					'type_acc':'Interbancario',
					'cod_type_acc':'I'
				})


			for l in c:
				if l.code=='1':
					avalstd.append({
						'bank_id':self.bank_bbva.id,
						'type_doc_partner_id':l.id,
						'code_type_doc':'L'
					})					
				if l.code=='4':
					avalstd.append({
						'bank_id':self.bank_bbva.id,
						'type_doc_partner_id':l.id,
						'code_type_doc':'E'
					})					
				if l.code=='6':
					avalstd.append({
						'bank_id':self.bank_bbva.id,
						'type_doc_partner_id':l.id,
						'code_type_doc':'R'
					})								
				if l.code=='7':
					avalstd.append({
						'bank_id':self.bank_bbva.id,
						'type_doc_partner_id':l.id,
						'code_type_doc':'P'
					})								

			for l in d:
		
				if l.code=='01':
					avalsti.append({
						'bank_id':self.bank_bbva.id,
						'type_doc_invoice_id':l.id,
						'code_type_doc':'F'
					})					
				if l.code=='03':
					avalsti.append({
						'bank_id':self.bank_bbva.id,
						'type_doc_invoice_id':l.id,
						'code_type_doc':'B'
					})								
				if l.code=='07':
					avalsti.append({
						'bank_id':self.bank_bbva.id,
						'type_doc_invoice_id':l.id,
						'code_type_doc':'N'
					})					

		if self.bank_scotia.id:
			avalstc.append({
					'bank_id':self.bank_scotia.id,
					'type_acc':'CTA. CORRIENTE SCOTIABANK',
					'cod_type_acc':'CTA. CORRIENTE SCOTIABANK'
				})
			avalstc.append({
					'bank_id':self.bank_scotia.id,
					'type_acc':'CTA. AHORRO SCOTIABANK',
					'cod_type_acc':'CTA. AHORRO SCOTIABANK'
				})
			avalstc.append({
					'bank_id':self.bank_scotia.id,
					'type_acc':'CTA. INTERBANCARIA',
					'cod_type_acc':'CTA. INTERBANCARIA'
				})
			avalstc.append({
					'bank_id':self.bank_scotia.id,
					'type_acc':'CHEQUE DE GERENCIA',
					'cod_type_acc':'CHEQUE DE GERENCIA'
				})

			for l in e:
				if l.name=='PEN':
					avalscu.append({
						'bank_id':self.bank_scotia.id,
						'currency_id':l.id,
						'code_currency':'SOLES'
					})					
				if l.name=='USD':
					avalscu.append({
						'bank_id':self.bank_scotia.id,
						'currency_id':l.id,
						'code_currency':'DOLARES'
					})		

		model_line = self.env['ir.model'].search([('name','=','multipayment.advance.invoice.line')])[0]
		fields_model = self.env['ir.model.fields'].search([('model_id','=',model_line.id)])
		for l in fields_model:
			vals={
				'name':l.field_description,
				'module_id':l.model_id.id,
				'field_id':l.id,
			}
			self.env['export.field.usable'].create(vals)

		for l in avalstc:
			model_tc.create(l)
			
		for l in avalstd:
			model_td.create(l)

		for l in avalsti:
			model_ti.create(l)

		for l in avalscu:
			model_cu.create(l)
