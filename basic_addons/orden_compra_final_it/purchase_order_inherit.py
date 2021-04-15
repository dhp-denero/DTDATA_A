# -*- encoding: utf-8 -*-
#from openerp.osv import osv
import base64
from odoo import models, fields, api , exceptions

class ModeloSaleOrderInherit(models.Model):
	_inherit = 'purchase.order'
	x_validez_val_1 = fields.Char(string='Validez') 
	x_condiciones_entrega_1 = fields.Char(string='Condiciones de Entrega')
	plazos_pago = fields.Many2one("account.payment.term",string="Plazos de Pago")