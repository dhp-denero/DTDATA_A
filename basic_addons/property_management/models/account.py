# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Account Entry"

    asset_id = fields.Many2one(
        comodel_name='account.asset.asset',
        help='Asset')
    schedule_date = fields.Date(
        string='Schedule Date',
        help='Rent Schedule Date.')
    source = fields.Char(
        string='Source',
        help='Source from where account move created.')

    @api.multi
    def assert_balanced(self):
        prec = self.env['decimal.precision'].precision_get('Account')
        self._cr.execute("""
            SELECT	  move_id
            FROM		account_move_line
            WHERE	   move_id in %s
            GROUP BY	move_id
            HAVING	  abs(sum(debit) - sum(credit)) > %s
            """, (tuple(self.ids), 10 ** (-max(5, prec))))
        if self._cr.fetchall():
            raise UserError(_("Cannot create unbalanced journal entry."))
        return True


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property',
        help='Property Name.')


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy',
        help='Tenancy Name.')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property',
        help='Property Name.')
    amount_due = fields.Monetary(
        comodel_name='res.partner',
        related='partner_id.credit',
        readonly=True,
        default=0.0,
        help='Display Due amount of Customer')

    @api.multi
    def post(self):
        res = super(AccountPayment, self).post()
        invoice_obj = self.env['account.invoice']
        context = dict(self._context or {})
        for rec in self:
            if context.get('return'):
                invoice_browse = invoice_obj.browse(
                    context.get('active_id')).new_tenancy_id
                invoice_browse.write({'amount_return': rec.amount})
        return res

    @api.model
    def create(self, vals):
        res = super(AccountPayment, self).create(vals)
        if res and res.id and res.tenancy_id and res.tenancy_id.id:
            if res.payment_type == 'inbound':
                res.tenancy_id.write({'acc_pay_dep_rec_id': res.id})
            if res.payment_type == 'outbound':
                res.tenancy_id.write({'acc_pay_dep_ret_id': res.id})
        return res

    @api.multi
    def back_to_tenancy(self):
        """
        This method will open a Tenancy form view.
        @param self: The object pointer
        @param context: A standard dictionary for contextual values
        """
        open_move_id = self.env.ref(
            'property_management.property_analytic_view_form').id
        for vou_brw in self:
            tenancy_id = vou_brw.tenancy_id and vou_brw.tenancy_id.id
            if tenancy_id:
                return {
                    'view_type': 'form',
                    'view_id': open_move_id,
                    'view_mode': 'form',
                    'res_model': 'account.analytic.account',
                    'res_id': tenancy_id,
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'context': self._context,
                }
            else:
                return True

    # Gives Credit amount line
    def _get_counterpart_move_line_vals(self, invoice=False):
        rec = super(AccountPayment, self)._get_counterpart_move_line_vals(
            invoice=invoice)
        if rec and self.tenancy_id and self.tenancy_id.id:
            if self.payment_type in ('inbound', 'outbound'):
                rec.update({'analytic_account_id': False})
        return rec

    # Gives Debit amount line
    def _get_liquidity_move_line_vals(self, amount):
        rec = super(
            AccountPayment, self)._get_liquidity_move_line_vals(amount)
        if rec and self.tenancy_id and self.tenancy_id.id:
            if self.payment_type in ('inbound', 'outbound'):
                rec.update({'analytic_account_id': self.tenancy_id.id})
        return rec

    def _create_payment_entry(self, amount):
        move = super(AccountPayment, self)._create_payment_entry(amount)
        if move and move.id and self.property_id and self.property_id.id:
            move.write({'asset_id': self.property_id.id or False,
                        'source': self.tenancy_id.name or False})
        return move


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property',
        help='Property Name.')
    new_tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy')

    @api.multi
    def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()
        for inv_rec in self:
            if inv_rec.move_id and inv_rec.move_id.id:
                inv_rec.move_id.write({
                    'asset_id': inv_rec.property_id.id or False,
                    'ref': 'Maintenance Invoice',
                    'source': inv_rec.property_id.name or False})
        return res
