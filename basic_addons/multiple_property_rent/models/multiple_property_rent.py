# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
from odoo import api, fields, models


class Recurring(models.Model):
    _name = 'property.rent'

    property_ids = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property',
        help='Property name')
    ground = fields.Float(
        string='Ground Rent',
        help='Rent of property', )
    ten = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Ten')

    @api.onchange('property_ids')
    def ground_rent(self):
        """
        This method is used to get rent when select the property
        """
        val = 0.0
        if self.property_ids:
            val = float(self.property_ids.ground_rent)
        self.ground = val


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    # @api.one
    @api.onchange('prop_id', 'multi_prop')
    def _total_prop_rent(self):
        """
        This method calculate total rent of all the selected property.
        @param self: The object pointer
        """
        if self._context.get('is_tenancy_rent'):
            prop_val = self.prop_ids.ground_rent or 0.0
        else:
            prop_val = self.property_id.ground_rent or 0.0
        for pro_record in self:
            if pro_record.multi_prop:
                tot = sum(prope_ids.ground for prope_ids in pro_record.prop_id)
                pro_record.rent = tot + prop_val
            else:
                pro_record.rent = prop_val

    prop_id = fields.One2many(
        comodel_name='property.rent',
        inverse_name='ten',
        string="Property")
    # rent = fields.Float(
    #     string='Rent',
    #     # compute='_total_prop_rent',
    #     # readonly=True,
    #     store=True)
    multi_prop = fields.Boolean(
        string='Multiple Property',
        help="Check this box Multiple property.")

    @api.onchange('multi_prop')
    def onchange_multi_prop(self):
        """
        If the context is get is_tenanacy_rent then property id is 0
        or if get than prop_ids is zero
        @param self: The object pointer
        """
        if self.multi_prop:
            if not self._context.get('is_tenancy_rent'):
                self.property_id = 0
            elif self._context.get('is_tenancy_rent'):
                self.prop_ids = 0
