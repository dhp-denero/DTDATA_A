# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
from odoo import models, fields, api


class AccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    @api.multi
    @api.depends('tenancy_property')
    def total_exp_amt_calc(self):
        """
        This method is used to calculate Total income amount.
        --------------------------------------------------------
        @param self: The object pointer
        """
        analytic_obj = self.env['account.analytic.account']
        for property_brw in self:
            tenant_rec = analytic_obj.search(
                [('prop_ids', '=', property_brw.id),
                 ('is_tenancy_rent', '=', True)])
            total = sum(tenancy.total_deb_cre_amt for tenancy in tenant_rec)
            property_brw.total_exp_amt = total

    tenancy_property = fields.One2many(
        'account.analytic.account', 'prop_ids', 'Tenancy Property')
    currenttenant_id = fields.Many2one('tenant.partner', 'Current Tenant')
    total_exp_amt = fields.Float(compute='total_exp_amt_calc',
                                 string='Tenancy Rent Expense',
                                 default=0.0)
