# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    commission_line = fields.One2many(
        comodel_name='account.analytic.account',
        inverse_name='agent',
        string='Commission')
