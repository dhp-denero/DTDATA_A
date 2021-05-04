# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

import time

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning
from odoo import SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class CrmLead(models.Model):
    _inherit = "crm.lead"

    facing = fields.Char(
        string='Facing')
    demand = fields.Boolean(
        string='Is Demand')
    max_price = fields.Float(
        string='Max Price')
    min_price = fields.Float(
        string='Min. Price')
    is_buy = fields.Boolean(
        string='Is Buy',
        default=False)
    is_rent = fields.Boolean(
        string='Is Rent',
        default=False)
    max_bedroom = fields.Integer(
        string='Max Bedroom Require')
    min_bedroom = fields.Integer(
        string='Min. Bedroom Require')
    max_bathroom = fields.Integer(
        string='Max Bathroom Require')
    min_bathroom = fields.Integer(
        string='Min. Bathroom Require')
    furnished = fields.Char(
        string='Furnishing',
        help='Furnishing')
    type_id = fields.Many2one(
        comodel_name='property.type',
        string='Property Type',
        help='Property Type')
    email_send = fields.Boolean(
        string='Email Send',
        help="it is checked when email is send")
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')

    @api.model
    def _lead_create_contact(self, name, is_company, parent_id=False):
        """
        This method is used to create customer
        when lead convert to opportunity.
        @param self: The object pointer
        @param lead: The current user’s ID for security checks,
        @param name: Contact name from current Lead,
        @param is_company: Boolean field, checked if company's lead,
        @param parent_id: Linked partner from current Lead,
        @return: Newly created Partner id,
        """
        if not self.contact_name or not self.email_from:
            raise ValidationError(_('Sorry! Can not Convert to opportunity because\
                                    Contact Name or Email is Missing!'))
        vals = {
            'name': self.contact_name,
            'user_id': self.user_id.id,
            'comment': self.description,
            'team_id': self.team_id.id or False,
            'parent_id': parent_id,
            'phone': self.phone,
            'mobile': self.mobile,
            'email': self.email_from,
            'fax': self.fax,
            'title': self.title and self.title.id or False,
            'function': self.function,
            'street': self.street,
            'street2': self.street2,
            'zip': self.zip,
            'city': self.city,
            'country_id':
            self.country_id and self.country_id.id or False,
            'state_id': self.state_id and self.state_id.id or False,
            'is_company': is_company,
            'type': 'contact',
        }

        company_id = self.env['res.users'].browse(SUPERUSER_ID).company_id.id
        paypal_ids = self.env['payment.acquirer'].search(
            [('name', 'ilike', 'paypal'),
             ('company_id', '=', company_id), ], limit=1)
        if paypal_ids:
            if not self.country_id:
                raise Warning(_(' Please select country!'))
        if self.is_rent:
            vals.update({'tenant': True})
            tenant_id = self.env['tenant.partner'].create(vals)
            tenant_id.parent_id.write({'tenant': True})
            return tenant_id.parent_id.id
        else:
            return self.env['res.partner'].create(vals).id


class CrmMakeContract(models.TransientModel):
    _name = "crm.make.contract"
    _description = "Make sales"

    @api.model
    def _selectPartner(self):
        """
        This function gets default value for partner_id field.
        @param self: The object pointer
        @return: default value of partner_id field.
        """
        if self._context is None:
            self._context = {}
        active_id = self._context and self._context.get(
            'active_id', False) or False
        if not active_id:
            return False
        lead_brw = self.env['crm.lead'].browse(active_id)
        lead = lead_brw.read(['partner_id'])[0]
        return lead['partner_id'][0] if lead['partner_id'] else False

    date = fields.Date(
        string='End Date')
    date_start = fields.Date(
        string='Start Date',
        default=lambda *a: time.strftime(DEFAULT_SERVER_DATE_FORMAT))
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        default=_selectPartner,
        required=True,
        domain=[('customer', '=', True)])
    close = fields.Boolean(
        string='Mark Won',
        default=False,
        help='Check this to close the opportunity after having created the \
        sales order.')

    @api.multi
    def makecontract(self):
        """
        This function create Quotation on given case.
        @param self: The object pointer
        @return: Dictionary value of created sales order.
        """
        context = dict(self._context or {})
        context.pop('default_state', False)
        data = context and context.get('active_ids', []) or []
        lead_obj = self.env['crm.lead']
        for make in self:
            partner = make.partner_id
            new_ids = []
            view_id = self.env.ref(
                'property_management.property_analytic_view_form').id
            for case in lead_obj.browse(data):
                if not partner and case.partner_id:
                    partner = case.partner_id
                vals = {
                    'name': case.name,
                    'partner_id': partner.id,
                    'property_id': case.property_id.id,
                    'tenant_id': self.env['res.users'].search([
                        ('partner_id', '=', case.partner_id.id)]).tenant_id.id,
                    'company_id': partner.company_id.id,
                    'date_start': make.date_start or False,
                    'date': make.date or False,
                    'type': 'contract',
                    'is_property': True,
                    'rent': case.property_id.ground_rent,
                }
                if self._context.get('is_tenancy_rent'):
                    vals.update({'prop_ids': case.property_id.id})
                new_id = self.env['account.analytic.account'].create(vals)
                case.write({'ref': 'account.analytic.account,%s' % new_id})
                new_ids.append(new_id.id)
                message = _(
                    "Opportunity has been <b>converted</b> to the \
                    Contract <em>%s</em>.") % (new_id.name)
                case.message_post(body=message)
            if make.close:
                case.action_set_won()
            if not new_ids:
                return {'type': 'ir.actions.act_window_close'}
            value = {
                'domain': str([('id', 'in', new_ids)]),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.analytic.account',
                # 'view_id': False,
                'view_id': view_id,
                'type': 'ir.actions.act_window',
                'name': _('Contract'),
                'res_id': new_ids
            }

            if len(new_ids) <= 1:
                value.update(
                    {'view_mode': 'form', 'res_id': new_ids and new_ids[0]})
            return value
