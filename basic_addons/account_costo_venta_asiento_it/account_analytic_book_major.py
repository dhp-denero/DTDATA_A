# -*- coding: utf-8 -*-

from openerp import models, fields, api


class view_costo_venta_it(models.Model):
	_name = 'view.costo.venta.it'
	_auto = False

	period_id = fields.Many2one('account.period','Periodo')
	almacen = fields.Many2one('stock.location','Almacen')
	producto = fields.Many2one('product.product','Producto')
	salidas = fields.Float('Salidas')
	devoluciones = fields.Float('Devoluciones')
	costo_ventas = fields.Float('Costo de Ventas')
	cuenta_salida = fields.Many2one('account.account','Cuenta Salida')
	cuenta_valuacion = fields.Many2one('account.account','Cuenta Valuacion')