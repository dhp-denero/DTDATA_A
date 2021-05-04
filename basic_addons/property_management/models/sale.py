# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')
    is_property = fields.Boolean(
        string='Is Property')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        domain=[('sale_ok', '=', True)],
        change_default=True,
        ondelete='restrict',
        required=False)
    product_uom = fields.Many2one(
        comodel_name='product.uom',
        string='Unit of Measure',
        required=False)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_property = fields.Boolean(
        string='Is Property',
        default=False)
