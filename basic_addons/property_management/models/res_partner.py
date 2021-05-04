# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    tenant = fields.Boolean(
        string='Tenant',
        help="Check this box if this contact is a tenant.")
    occupation = fields.Char(
        string='Occupation',
        size=20)
    agent = fields.Boolean(
        string='Agent',
        help="Check this box if this contact is a Agent.")
    is_worker = fields.Boolean(
        string='Worker',
        help="Check this box if this contact is a worker.")
    prop_manintenance_ids = fields.One2many(
        comodel_name='property.maintenance',
        inverse_name='assign_to',
        string="Property Maintenance")
    worker_maintenance_ids = fields.Many2many(
        comodel_name='maintenance.type',
        relation='rel_worker_maintenance',
        column1='partner_id',
        column2='maintenance_id',
        string='Maintenance Type',
        help="Select the types of work the worker does.")
    mobile = fields.Char(
        string='Mobile',
        size=15)

    @api.multi
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        tenant_group = \
            self.env.ref('property_management.group_property_user')
        agent_group = \
            self.env.ref('property_management.group_property_agent')
        for partner in self:
            if 'tenant' in vals:
                if not partner.tenant:
                    if partner.user_ids.has_group(
                            'property_management.group_property_user'):
                        partner.user_ids.write(
                            {'groups_id': [(3, tenant_group.id)]})
                else:
                    partner.user_ids.write(
                        {'groups_id': [(4, tenant_group.id)]})
            if 'agent' in vals:
                if not partner.agent:
                    if partner.user_ids.has_group(
                            'property_management.group_property_agent'):
                        partner.user_ids.write(
                            {'groups_id': [(3, agent_group.id)]})
                else:
                    partner.user_ids.write(
                        {'groups_id': [(4, agent_group.id)]})
        return res

    @api.constrains('mobile')
    def _check_value(self):
        """
        Check the mobile number in special formate if you enter wrong
        mobile formate then raise ValidationError
        """
        for val in self:
            if val.mobile:
                if re.match(
                        "^\+|[1-9]{1}[0-9]{3,14}$", val.mobile) is not None:
                    pass
                else:
                    raise ValidationError('Please Enter Valid Mobile Number!')

    @api.constrains('email')
    def _check_values(self):
        """
        Check the email address in special formate if you enter wrong
        mobile formate then raise ValidationError
        """
        for val in self:
            if val.email:
                if re.match("^[a-zA-Z0-9._+-]+@[a-zA-Z0-9]+\.[a-zA-Z0-9.]*\.*[a-zA-Z]{2,4}$", val.email) is not None:
                    pass
                else:
                    raise ValidationError('Please Enter Valid Email Id!')


class ResUsers(models.Model):
    _inherit = "res.users"

    tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Related Tenant')
    tenant_ids = fields.Many2many(
        comodel_name='tenant.partner',
        relation='rel_ten_user',
        column1='user_id',
        column2='tenant_id',
        string='All Tenants')


class ResCompany(models.Model):
    _inherit = 'res.company'

    default_password = fields.Char(
        string='Default Password')
