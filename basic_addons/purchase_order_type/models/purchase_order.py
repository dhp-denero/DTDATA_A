# -*- coding: utf-8 -*-
# Copyright 2015 Guewen Baconnier <guewen.baconnier@camptocamp.com>
# Copyright 2016 Vicent Cubells <vicent.cubells@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
# from openerp.addons.purchase.purchase import PurchaseOrder as purchase_order


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _default_order_type(self):
        return self.env['purchase.order.type'].search([], limit=1)

    order_type = fields.Many2one('purchase.order.type',require=True,string='Type',ondelete='restrict',default=_default_order_type)
    state_importation = fields.Many2one('purchase.state.importation',require=True,string='Estado de importacion',ondelete='restrict')
    origen_compra = fields.Selection([('nacional', 'Nacional'),('internacional','Internacional')], "Origen de compra",default='nacional')

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id_purchase_order_type(self):
        if self.partner_id.purchase_type:
            self.order_type = self.partner_id.purchase_type.id

    @api.onchange('order_type')
    def onchange_purchase_order_type(self):
        if self.order_type:
            if self.order_type.incoterm_id:
                self.incoterm_id = self.order_type.incoterm_id.id
            if self.order_type.picking_type_id:
                self.picking_type_id = self.order_type.picking_type_id.id

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            order_type = self.env['purchase.order.type'].search([], limit=1)
            if not order_type:
                raise exceptions.Warning('No existe un tipo de orden creado.')

            if vals.get('order_type', order_type) == order_type:
                order_type = order_type[0].id
            else:
                order_type = vals['order_type']
            if order_type:
                order_type = self.env['purchase.order.type'].browse(order_type)
                if order_type:
                    vals['name'] = order_type.serie_guia.next_by_id() or '/'
        return super(PurchaseOrder, self).create(vals)
