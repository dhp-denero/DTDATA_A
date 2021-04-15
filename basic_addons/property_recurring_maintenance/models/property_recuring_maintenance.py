# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
from odoo import api, fields, models


class MaintenanceType(models.Model):
    _inherit = 'maintenance.type'

    main_cost = fields.Boolean(
        string='Recurring cost',
        help='Check if the recurring cost involve')
    cost = fields.Float(
        string='Maintenance Cost',
        help='insert the cost')


class MaintenanaceCost(models.Model):
    _name = 'maintenance.cost'

    maint_type = fields.Many2one(
        comodel_name='maintenance.type',
        string='Maintenance Type',
        required=True)
    cost = fields.Float(
        string='Maintenance Cost',
        help='insert the cost',
        required=True)
    tenancy = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy')

    @api.onchange('maint_type')
    def onchange_property_id(self):
        """
        This Method is used to set maintenance type related fields value,
        on change of property.
        -----------------------------------------------------------------
        @param self: The object pointer
        """
        for data in self:
            if data.maint_type:
                data.cost = data.maint_type.cost or 0.00


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"
    _order = 'ref'

    @api.multi
    @api.depends('cost_id')
    def _total_cost_maint(self):
        """
        This method is used to calculate total maintenance
        boolean field accordingly to current Tenancy.
        --------------------------------------------------
        @param self: The object pointer
        """
        for data in self:
            total = sum(cost.cost for cost in data.cost_id)
            data.main_cost = total

    cost_id = fields.One2many(
        comodel_name='maintenance.cost',
        inverse_name='tenancy',
        string='cost')
    main_cost = fields.Float(
        string='Maintenance Cost',
        default=0.0,
        compute='_total_cost_maint',
        help="insert maintenance cost")
    recurring = fields.Boolean(
        'Recurring',
        default=True)
