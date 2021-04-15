# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class account_voucher_advance(models.Model):
	_name = 'account.voucher.advance'

	fecha = fields.Date('Fecha')
	period_id = fields.Many2one('account.period','Periodo')
	caja = fields.Many2one('account.journal','Caja')
	flujo_caja = fields.Many2one('it.flujo.caja','Flujo de Caja')
	moneda = fields.Many2one('res.currency','Moneda de Pago')
	type_mov = fields.Selection([('ingreso','Ingreso'),('egreso','Egreso')],'Tipo de Movimiento')
	ref_pago = fields.Char('Ref. Pago',size=30)
	glosa = fields.Char('Glosa', size=200)
	partner_id = fields.Many2many('res.partner','partner_voucher_advance_rel','advance_id','partner_id','Proveedores')
	total = fields.Float('Total',digits=(12,2))
	tipo_cambio = fields.Float('Tipo de Cambio',digits=(12,3))

	line_ids = fields.One2many('account.voucher.advance.line','padre','Detalle')


	
	@api.onchange('fecha')
	def onchange_fecha(self):
		if self.fecha:
			ss = self.fecha.split('-')[1] + '/' + self.fecha.split('-')[0]
			periodo = self.env['account.period'].search([('code','=',ss)])
			if len(periodo) >0:
				self.period_id = periodo[0].id
			else:
				self.period_id = False
		else:
			self.period_id = False



class account_voucher_advance_line(models.Model):
	_name = 'account.voucher.advance.line'

	periodo = fields.Many2one('account.period','Periodo')
	fecha_emision = fields.Date(u'Fecha Emisión')
	empresa = fields.Char('Empresa')
	ruc = fields.Char('RUC')
	cuenta = fields.Many2one('account.account','Cuenta Contable')
	divisa = fields.Many2one('res.currency','Divisa')
	tipo = fields.Char('Tipo')
	nro_comprobante = fields.Char('Nro. Comprobante')
	saldo_mn = fields.Float('Saldo MN.')
	saldo_me = fields.Float('Saldo ME.')
	monto = fields.Float('Monto')
	padre = fields.Many2one('account.voucher.advance','Padre')
