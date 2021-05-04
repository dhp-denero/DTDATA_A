# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
from datetime import datetime
import time

from odoo import _, api, fields, models
from odoo.exceptions import Warning
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class CommissionInvoiceLine(models.Model):
    _name = "commission.invoice.line"
    _description = "Commission Invoice Line"
    _order = 'date desc, id desc'

    date = fields.Date(
        string='Start Date')
    end_date = fields.Date(
        string='End Date')
    name = fields.Char(
        string="Description")
    commission_type = fields.Selection(
        selection=[('fixed', 'Fixed percentage'),
                   ('fixedcost', 'By Fixed Cost')],
        string='Type')
    rent_amt = fields.Float(
        string='Rent Amount')
    amount = fields.Float(
        store=True,
        string='Commission Amount')
    commission_id = fields.Many2one(
        comodel_name='commission.invoice',
        string='Commission')
    invc_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice')
    inv = fields.Boolean(
        string='INV')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="OwnerCompany")


class CommissionInvoice(models.Model):
    _name = "commission.invoice"
    _rec_name = 'number'
    _description = "Commission Invoice"

    @api.multi
    @api.depends('commission_line.amount')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for rec in self:
            rec.amount_total = sum(line.amount for line in rec.commission_line)

    number = fields.Char(
        string='Commission ID',
        default='/')
    patner_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Partner',
        help='Name of tenant where from commission is taken')
    date = fields.Date(
        String='Commission Date',
        default=lambda *a: time.strftime(DEFAULT_SERVER_DATE_FORMAT))
    tenancy = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy')
    description = fields.Text(
        string='Description')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')
    state = fields.Selection(
        [('draft', 'Open'),
         ('cancel', 'Cancel'),
         ('invoice', 'Invoiced')
         ], 'State', readonly=True,
        default='draft')
    commission_type = fields.Selection(
        selection=[('fixed', 'Fixed percentage'),
                   ('fixedcost', 'By Fixed Cost')],
        string='Type',
        default='fixed')
    commission_line = fields.One2many(
        comodel_name='commission.invoice.line',
        inverse_name='commission_id',
        string='Commission')
    amount_total = fields.Float(
        string='Total',
        store=True,
        readonly=True,
        compute='_amount_all',
        track_visibility='always')
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency")
    agent = fields.Many2one(
        comodel_name='res.partner',
        domain=[('agent', '=', True)])
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'commission.invoice'))
    invc_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice')
    inv = fields.Boolean(
        string='INV')
    color = fields.Integer('Color Index')

    @api.multi
    def create_invoice(self):
        """
        This method is used to create supplier invoice.
        ------------------------------------------------------------
        @param self: The object pointer
        """
        account_jrnl_rec = self.env['account.journal'].search(
            [('type', '=', 'purchase')], limit=1)
        invoice_obj = self.env['account.invoice']
        wiz_form_id = self.env.ref('account.invoice_supplier_form').id
        for data in self:
            inv_line_values = {
                'name': 'Commission For ' + data.number or "",
                'account_analytic_id': data.tenancy.id or False,
                'origin': 'Commission',
                'quantity': 1,
                'account_id': data.property_id.expense_account_id.id or False,
                'price_unit': data.amount_total or 0.00,
            }
            inv_values = {
                'origin': 'Commission For ' + data.number or "",
                'type': 'in_invoice',
                'property_id': data.property_id.id,
                'partner_id': data.agent.id or False,
                'invoice_line_ids': [(0, 0, inv_line_values)],
                'date_invoice': datetime.now().strftime(
                    DEFAULT_SERVER_DATE_FORMAT) or False,
                'account_id':
                data.agent.property_account_payable_id.id or False,
                'journal_id':
                account_jrnl_rec and account_jrnl_rec.id or False,
            }
            acc_id = invoice_obj.create(inv_values)
            data.write({'inv': True, 'invc_id': acc_id.id, 'state': 'invoice'})
        return {
            'view_type': 'form',
            'view_id': wiz_form_id,
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'res_id': self.invc_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': self._context,
        }

    @api.multi
    def open_invoice(self):
        """
        This Method is used to Open invoice .
        ------------------------------------
        @param self: The object pointer
        """
        context = dict(self._context or {})
        wiz_form_id = self.env.ref(
            'account.invoice_supplier_form').id
        return {
            'view_type': 'form',
            'view_id': wiz_form_id,
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'res_id': self.invc_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': context,
        }

    @api.model
    def create(self, vals):
        """
        This Method is used to create sequence for commission.
        ------------------------------------------------------------
        @param self: The object pointer
        """
        res = super(CommissionInvoice, self).create(vals)
        res.number = \
            self.env['ir.sequence'].next_by_code('commission.invoice')
        return res

    @api.multi
    def button_close(self):
        """
        This button method is used to Change commission state to cancel.
        ------------------------------------------------------------
        @param self: The object pointer
        """
        for rec in self:
            if not rec.tenancy.state == 'close' or \
                    rec.tenancy.state == 'cancelled':
                raise Warning(_("Please First close " + str(
                    rec.tenancy.name) + " Tenancy!"))
            rec.state = 'close'


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def post(self):
        """
        This method is used to check if the invoice state is paid then
        the rec will be true.
        ------------------------------------------------------------
        @param self: The object pointer
        """
        res = super(AccountPayment, self).post()
        line_rec = self.env['commission.invoice.line'].search([
            ('invc_id', '=', self._context.get('active_id'))])
        for data in line_rec:
            if data.invc_id.state == 'paid':
                data.rec = True
        return res


# class TenancyRentSchedule(models.Model):
#     _inherit = "tenancy.rent.schedule"
#     _description = "Commission Invoice"


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    @api.multi
    @api.depends('commission_type', 'fix_qty', 'fix_cost', 'total_rent')
    def calculate_commission(self):
        """
        This method is used to calculate commission as per commission type
        -----------------------------------------------------------------
        @param self: The object pointer
        """
        for data in self:
            if data.commission:
                if data.commission_type == 'fixed':
                    data.total_commission = data.total_rent * (
                        data.fix_qty / 100.0)
                if data.commission_type == 'fixedcost':
                    data.total_commission = data.fix_cost

    commission_type = fields.Selection(
        selection=[('fixed', 'Fixed percentage'),
                   ('fixedcost', 'By Fixed Cost')],
        string='Type')
    fix_qty = fields.Float(
        string='Fixed Percentage(%)')
    fix_cost = fields.Float(
        string='Fixed Cost')
    agent = fields.Many2one(
        comodel_name='res.partner',
        domain=[('agent', '=', True)])
    commission = fields.Boolean(
        'Commission')
    commission_create = fields.Boolean(
        'Create')
    total_commission = fields.Float(
        string="Total Commission",
        compute="calculate_commission")

    @api.multi
    def create_commission(self):
        """
        This button method is used to Change Tenancy state to Open.
        -----------------------------------------------------------
        @param self: The object pointer
        """
        invoice_obj = self.env['commission.invoice']
        for data in self:
            if data.total_commission == 0.00:
                raise Warning(
                    _('Total Commission must be grater than zero.'))
            line_vlas = {
                'name': 'Commission',
                'commission_type': data.commission_type,
                'rent_amt': data.total_rent,
                'date': data.date_start,
                'end_date': data.date,
                'amount': data.total_commission,
            }
            vals = {
                'patner_id': data.tenant_id.id,
                'tenancy': data.id,
                'property_id': data.property_id.id,
                'agent': data.agent.id,
                'commission_line': [(0, 0, line_vlas)],
            }
            if self._context.get('is_tenancy_rent'):
                vals.update({
                    'property_id': data.prop_ids.id
                })
            invoice_obj.create(vals)
            data.write({'commission_create': True})

    @api.onchange('commission')
    def onchange_property_id(self):
        """
        This method is used to check if the commission field False than
        othe field value will be null or zero or false.
        ---------------------------------------------------------------
        @param self: The object pointer
        """
        if not self.commission:
            self.agent = 0
            self.commission_type = ''
            self.fix_qty = 0.00
            self.fix_cost = 0.00
