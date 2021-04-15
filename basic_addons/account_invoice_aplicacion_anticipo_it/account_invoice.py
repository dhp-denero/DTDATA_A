# -*- coding: utf-8 -*-

import json
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

from odoo.exceptions import UserError, RedirectWarning, ValidationError

import odoo.addons.decimal_precision as dp
import logging


class advance_payment(models.Model):
	_inherit= 'advance.payment'

	td = fields.Many2one('einvoice.catalog.01','T.D.')


class account_invoice(models.Model):
	_inherit = 'account.invoice'
	
	@api.multi
	def aplicacion_anticipo(self):
		parametro = self.env['main.parameter'].search([], limit=1)
		cuentas = []
		if parametro.account_anticipo_proveedor_mn.id:
			cuentas.append(parametro.account_anticipo_proveedor_mn.id)

		if parametro.account_anticipo_proveedor_me.id:
			cuentas.append(parametro.account_anticipo_proveedor_me.id)

		if parametro.account_anticipo_clientes_mn.id:
			cuentas.append(parametro.account_anticipo_clientes_mn.id)

		if parametro.account_anticipo_clientes_me.id:
			cuentas.append(parametro.account_anticipo_clientes_me.id)

		compro = None
		tipo = None
		for i in self.advance_payment_ids:
			tipo = i.td.id
			compro = i.serial + '-' + i.number

		if not compro or not tipo:
			raise UserError('No hay anticipo para aplicar.')

		for i in self:
			for m in i.move_id.line_ids:
				if m.account_id.id in cuentas:
					m.type_document_it = tipo
					m.nro_comprobante = compro