# -*- encoding: utf-8 -*-
from odoo import models, fields, api , exceptions
from odoo.exceptions import UserError
import base64
from datetime import datetime
from functools import reduce

class ResPartnerBank(models.Model):
	_inherit = 'res.partner.bank'

	acc_icc_number = fields.Char(u'Número ICC')
	export_type_acc= fields.Many2many('export.bank.acctype','partbank_exacctyp_rel','partbank_id','exacctyp_id','Tipo de cuenta para los bancos')

class export_bank_acctype(models.Model):
	_name = 'export.bank.acctype'
	_description = 'Tipo de Cuentas por Banco'

	bank_id = fields.Many2one('res.bank','Banco')
	type_acc = fields.Char('Tipo en Banco')
	cod_type_acc = fields.Char(u'Código en Banco')

class export_typedoc_partner(models.Model):
	_name='export.typedoc.partner'
	_description = u'Tipo de Documento de identificación por banco'

	bank_id = fields.Many2one('res.bank','Banco')
	type_doc_partner_id = fields.Many2one('einvoice.catalog.06','Tipo DOC.')
	code_type_doc = fields.Char(u'Código en Banco')	


class export_typedoc_invoice(models.Model):
	_name='export.typedoc.invoice'
	_description = 'Tipo de comprobante por banco'

	bank_id = fields.Many2one('res.bank','Banco')
	type_doc_invoice_id = fields.Many2one('einvoice.catalog.01','Tipo DOC.')
	code_type_doc = fields.Char(u'Código en Banco')	

class export_currency(models.Model):
	_name='export.currency'
	_description='Tipo de moneda por banco'

	bank_id = fields.Many2one('res.bank','Banco')
	currency_id = fields.Many2one('res.currency','Moneda')
	code_currency = fields.Char(u'Código en Banco')	


class export_field_usable(models.Model):
	_name='export.field.usable'
	_description='Campos Usables'

	name=fields.Char('Campo Disponible')
	module_id = fields.Many2one('ir.model',u'Módulo')
	field_id = fields.Many2one('ir.model.fields','Campo')




class export_report_head(models.Model):
	_name='export.report.head'
	_description=u'Cabecera de Exportación'

	name = fields.Char('Reporte')
	bank_id = fields.Many2one('res.bank','Banco')
	group_4_partner = fields.Boolean('Agrupar por Proveedor')
	field_ids = fields.One2many('export.report.field','report_id','Campos del reporte')

class export_report_field(models.Model):
	_name = 'export.report.field'
	_description=u'Detalle de Exportación'

	name		= fields.Many2one('export.field.usable','Campo')
	position	= fields.Integer(u'Posición en el Reporte')
	report_id 	= fields.Many2one('export.report.head','Reporte')


