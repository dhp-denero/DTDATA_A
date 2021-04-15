# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import Warning
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    is_tenancy_rent = fields.Boolean(
        string='Is Tenancy Rent?')
    prop_ids = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property',
        help="Name of property")
    property_owner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Owner',
        help="Owner of property.")

    @api.onchange('property_id')
    def onchange_property_id(self):
        """
        This Method is used to set property related fields value,
        on change of property.
        ------------------------------------------------------------
        @param self: The object pointer
        """
        if self.property_id:
            self.rent = self.property_id.ground_rent or False
            self.rent_type_id = self.property_id.rent_type_id and \
                self.property_id.rent_type_id.id or False

    @api.onchange('prop_ids')
    def onchange_prop_ids(self):
        """
        This Method is used to set property related fields value,
        on change of property.
        ----------------------------------------------------------
        @param self: The object pointer
        """
        if self._context.get('is_tenancy_rent') and self.prop_ids:
            self.rent = self.prop_ids.ground_rent or False
            self.property_owner_id = self.prop_ids.property_manager.id or \
                False
            self.rent_type_id = self.prop_ids.rent_type_id and \
                self.prop_ids.rent_type_id.id or False

    @api.model
    def create(self, vals):
        """
        This Method is used to overrides orm create method,
        to change state and tenant of related property.
        ---------------------------------------------------
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        res = super(AccountAnalyticAccount, self).create(vals)
        if self._context.get('is_tenancy_rent'):
            res.ref = self.env['ir.sequence'].next_by_code(
                'tenancy.rent')
            if res.is_tenancy_rent:
                res.write({'is_property': False})
            if res.prop_ids:
                res.prop_ids.stage = 'book'
        return res

    @api.multi
    def write(self, vals):
        """
        This Method is used to overrides orm write method,
        to change state and tenant of related property.
        ------------------------------------------------
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        rec = super(AccountAnalyticAccount, self).write(vals)
        for tenancy_rec in self:
            if tenancy_rec.is_tenancy_rent:
                if vals.get('state'):
                    if vals['state'] == 'open':
                        tenancy_rec.prop_ids.write({'state': 'normal'})
                    if vals['state'] == 'close':
                        tenancy_rec.prop_ids.write(
                            {'state': 'draft'})
        return rec

    # @api.multi
    # def button_starts(self):
    #     """
    #     This button method is used to Change Tenancy state to Open.
    #     ------------------------------------------------------------
    #     @param self: The object pointer
    #     """
    #     if self._context.get('is_tenancy_rent'):
    #         user_obj = self.env['res.users']
    #         for current_rec in self:
    #             if current_rec.prop_ids.property_manager and \
    #                     current_rec.prop_ids.property_manager.id:
    #                 releted_user = current_rec.prop_ids.property_manager.id
    #                 partner_rec = user_obj.search(
    #                     [('partner_id', '=', releted_user)])
    #                 if releted_user and partner_rec and partner_rec.ids:
    #                     partner_rec.write(
    #                         {'tenant_ids': [(4, current_rec.tenant_id.id)]})
    #             current_rec.write({'state': 'open', 'rent_entry_chck': False})

    @api.multi
    def unlink(self):
        """
        Overrides orm unlink method,
        ------------------------------
        @param self: The object pointer
        @return: True/False.
        """
        if self._context.get('is_tenancy_rent'):
            rent_obj = self.env['tenancy.rent.schedule']
            analytic_obj = self.env['account.analytic.line']
            for tenancy_rec in self:
                rent_ids = []
                analytic_ids = analytic_obj.search(
                    [('account_id', '=', tenancy_rec.id)])
                if analytic_ids and analytic_ids.ids:
                    analytic_ids.unlink()
                rent_ids = rent_obj.search(
                    [('tenancy_id', '=', tenancy_rec.id)])
                post_rent = [
                    rent.id for rent in rent_ids if rent.move_check]
                if post_rent:
                    raise Warning(
                        _('You cannot delete Tenancy record, if any related \
                        Rent Schedule entries are in posted.'))
                else:
                    rent_ids.unlink()
                # if tenancy_rec.prop_ids.property_manager and \
                #         tenancy_rec.prop_ids.property_manager.id:
                #     releted_user = tenancy_rec.prop_ids.property_manager.id
                    # new_ids = self.env['res.users'].search(
                    #     [('partner_id', '=', releted_user)])
                tenancy_rec.prop_ids.write(
                    {'state': 'draft'})
        return super(AccountAnalyticAccount, self).unlink()

    @api.multi
    def button_return(self):
        """
        This method create supplier invoice for returning deposit
        amount.
        -----------------------------------------------------------
        @param self: The object pointer
        """
        if self._context.get('is_tenancy_rent'):
            invc_obj = self.env['account.invoice']
            wiz_form_id = self.env.ref('account.invoice_supplier_form').id
            for data in self:
                inv_line_values = {
                    'name': 'Deposit Return' or "",
                    'origin': 'account.analytic.account' or "",
                    'quantity': 1,
                    'account_id': data.prop_ids.income_acc_id.id or False,
                    'price_unit': data.deposit or 0.00,
                    'account_analytic_id': data.id or False,
                }
                inv_values = {
                    'origin': 'Deposit Return For ' + data.name or "",
                    'type': 'in_invoice',
                    'property_id': data.prop_ids.id,
                    'partner_id': data.property_owner_id.id or False,
                    'account_id':
                    data.property_owner_id.property_account_payable_id.id or
                    False,
                    'invoice_line_ids': [(0, 0, inv_line_values)],
                    'date_invoice': datetime.now().strftime(
                        DEFAULT_SERVER_DATE_FORMAT) or False,
                    'new_tenancy_id': data.id,
                }
                acc_id = invc_obj.create(inv_values)
                data.write({'invc_id': acc_id.id})
                return {
                    'view_type': 'form',
                    'view_id': wiz_form_id,
                    'view_mode': 'form',
                    'res_model': 'account.invoice',
                    'res_id': data.invc_id.id,
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'context': self._context,
                }
        return super(AccountAnalyticAccount, self).button_return()

    @api.multi
    def button_receive(self):
        """
        This button method is used to open the related
        account payment form view.
        ------------------------------------------------
        @param self: The object pointer
        @return: Dictionary of values.
        """
        if self._context.get('is_tenancy_rent'):
            acc_pay_form_rec = \
                self.env.ref('account.view_account_payment_form')
            for tenancy_rec in self:
                if tenancy_rec.acc_pay_dep_rec_id and \
                        tenancy_rec.acc_pay_dep_rec_id.id:
                    return {
                        'view_type': 'form',
                        'view_id': acc_pay_form_rec.id,
                        'view_mode': 'form',
                        'res_model': 'account.payment',
                        'res_id': tenancy_rec.acc_pay_dep_rec_id.id,
                        'type': 'ir.actions.act_window',
                        'target': 'current',
                        'context': self._context,
                    }
                if tenancy_rec.deposit == 0.00:
                    raise Warning(_('Please Enter Deposit amount.'))
                if not tenancy_rec.prop_ids.income_acc_id.id:
                    raise Warning(
                        _('Please Configure Income Account from Property.'))
                return {
                    'view_mode': 'form',
                    'view_id': acc_pay_form_rec.id,
                    'view_type': 'form',
                    'res_model': 'account.payment',
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'current',
                    'domain': '[]',
                    'context': {
                        'default_partner_id': tenancy_rec.property_owner_id.id,
                        'default_partner_type': 'customer',
                        'default_journal_id': 6,
                        'default_payment_type': 'inbound',
                        'default_communication': 'Deposit Received',
                        'default_tenancy_id': tenancy_rec.id,
                        'default_amount': tenancy_rec.deposit,
                        'default_property_id': tenancy_rec.prop_ids.id,
                        'close_after_process': True,
                    }
                }
        return super(AccountAnalyticAccount, self).button_receive()

    @api.multi
    def create_rent_schedule(self):
        """
        This button method is used to create rent schedule Lines.
        ------------------------------------------------------------
        @param self: The object pointer
        """
        rent_obj = self.env['tenancy.rent.schedule']
        for tenancy_rec in self:
            if tenancy_rec.rent_type_id.renttype == 'Weekly':
                d1 = datetime.strptime(
                    tenancy_rec.date_start, DEFAULT_SERVER_DATE_FORMAT)
                d2 = datetime.strptime(
                    tenancy_rec.date, DEFAULT_SERVER_DATE_FORMAT)
                interval = int(tenancy_rec.rent_type_id.name)
                if d2 < d1:
                    raise Warning(
                        _('End date must be greater than start date.'))
                wek_diff = (d2 - d1)
                wek_tot1 = (wek_diff.days) / (interval * 7)
                wek_tot = (wek_diff.days) % (interval * 7)
                if wek_diff.days == 0:
                    wek_tot = 1
                if wek_tot1 > 0:
                    for wek_rec in range(wek_tot1):
                        rent_obj1 = rent_obj.create({
                            'start_date': d1.strftime
                            (DEFAULT_SERVER_DATE_FORMAT),
                            'amount': tenancy_rec.rent * interval
                            or 0.0,
                            'property_id': tenancy_rec.property_id
                            and tenancy_rec.property_id.id or False,
                            'tenancy_id': tenancy_rec.id,
                            'currency_id': tenancy_rec.currency_id.id or False,
                            'rel_tenant_id': tenancy_rec.tenant_id.id
                        })
                        if self._context.get('is_tenancy_rent') or \
                                tenancy_rec.is_tenancy_rent:
                            rent_obj1.update({
                                'property_id':
                                tenancy_rec.prop_ids
                                and tenancy_rec.prop_ids.id or False})
                        d1 = d1 + relativedelta(days=(7 * interval))
                if wek_tot > 0:
                    one_day_rent = 0.0
                    if tenancy_rec.rent:
                        one_day_rent = (tenancy_rec.rent) / (7 * interval)
                    rent_obj2 = rent_obj.create({
                        'start_date': d1.strftime
                        (DEFAULT_SERVER_DATE_FORMAT),
                        'amount': (one_day_rent * (wek_tot)) or 0.0,
                        'property_id': tenancy_rec.property_id
                        and tenancy_rec.property_id.id or False,
                        'tenancy_id': tenancy_rec.id,
                        'currency_id': tenancy_rec.currency_id.id
                        or False,
                        'rel_tenant_id': tenancy_rec.tenant_id.id
                    })
                    if self._context.get('is_tenancy_rent') or \
                            tenancy_rec.is_tenancy_rent:
                        rent_obj2.update({
                            'property_id':
                            tenancy_rec.prop_ids
                            and tenancy_rec.prop_ids.id or False})
            elif tenancy_rec.rent_type_id.renttype != 'Weekly':
                if tenancy_rec.rent_type_id.renttype == 'Monthly':
                    interval = int(tenancy_rec.rent_type_id.name)
                if tenancy_rec.rent_type_id.renttype == 'Yearly':
                    interval = int(tenancy_rec.rent_type_id.name) * 12
                d1 = datetime.strptime(
                    tenancy_rec.date_start, DEFAULT_SERVER_DATE_FORMAT)
                d2 = datetime.strptime(
                    tenancy_rec.date, DEFAULT_SERVER_DATE_FORMAT)
                diff = abs((d1.year - d2.year) * 12 + (d1.month - d2.month))
                tot_rec = diff / interval
                tot_rec2 = diff % interval
                if abs(d1.month - d2.month) >= 0 and d1.day < d2.day:
                    tot_rec2 += 1
                if diff == 0:
                    tot_rec2 = 1
                if tot_rec > 0:
                    for rec in range(tot_rec):
                        rent_obj3 = rent_obj.create({
                            'start_date': d1.strftime
                            (DEFAULT_SERVER_DATE_FORMAT),
                            'amount': tenancy_rec.rent * interval
                            or 0.0,
                            'property_id': tenancy_rec.prop_ids
                            and tenancy_rec.prop_ids.id or False,
                            'tenancy_id': tenancy_rec.id,
                            'currency_id': tenancy_rec.currency_id.id or False,
                            'rel_tenant_id': tenancy_rec.tenant_id.id
                        })
                        if self._context.get('is_tenancy_rent') or \
                                tenancy_rec.is_tenancy_rent:
                            rent_obj3.update({
                                'property_id':
                                tenancy_rec.prop_ids
                                and tenancy_rec.prop_ids.id or False})
                        d1 = d1 + relativedelta(months=interval)
                if tot_rec2 > 0:
                    rent_obj4 = rent_obj.create({
                        'start_date': d1.strftime(DEFAULT_SERVER_DATE_FORMAT),
                        'amount': tenancy_rec.rent * tot_rec2 or 0.0,
                        'property_id': tenancy_rec.prop_ids and
                        tenancy_rec.prop_ids.id or False,
                        'tenancy_id': tenancy_rec.id,
                        'currency_id': tenancy_rec.currency_id.id or False,
                        'rel_tenant_id': tenancy_rec.tenant_id.id
                    })
                    if self._context.get('is_tenancy_rent') or \
                            tenancy_rec.is_tenancy_rent:
                        rent_obj4.update(
                            {'property_id': tenancy_rec.prop_ids and
                                tenancy_rec.prop_ids.id or False})
            tenancy_rec.rent_entry_chck = True


class TenancyRentSchedule(models.Model):
    _inherit = "tenancy.rent.schedule"
    _rec_name = "tenancy_id"

    @api.multi
    def create_invoice(self):
        """
        Create invoice for Rent Schedule.
        ------------------------------------
        @param self: The object pointer
        """
        inv_obj = self.env['account.invoice']
        wiz_form_id = self.env.ref('account.invoice_supplier_form').id
        for rec in self:
            if rec.tenancy_id.is_tenancy_rent:
                inv_lines_values = {
                    'origin': 'tenancy.rent.schedule',
                    'name': 'Tenancy(Rent) Cost for' + rec.tenancy_id.name,
                    'quantity': 1,
                    'price_unit': rec.amount or 0.00,
                    'account_id':
                    rec.tenancy_id.prop_ids.expense_account_id.id or False,
                    'account_analytic_id': rec.tenancy_id.id or False,
                }
                if rec._context.get('penanlty') == 0:
                    rec.calculate_penalty()
                    if rec.tenancy_id.penalty < 00:
                        raise Warning(_('The Penalty% must be \
                                        strictly positive.'))
                    if rec.tenancy_id.penalty_day < 00:
                        raise Warning(_('The Penalty Count After Days must be \
                        strictly positive.'))
                    amt = rec.amount + rec.penalty_amount
                    inv_lines_values.update({'price_unit': amt or 0.00})
                if rec.tenancy_id.multi_prop:
                    for data in rec.tenancy_id.prop_id:
                        for account in data.property_ids.expense_account_id:
                            account_id = account.id
                    inv_lines_values.update({'account_id': account_id})
                if rec.tenancy_id.main_cost >= 0.00:
                    if rec.tenancy_id.main_cost:
                        inv_line_main = {
                            'origin': 'tenancy.rent.schedule',
                            'name': 'Maintenance cost',
                            'price_unit': rec.tenancy_id.main_cost or 0.00,
                            'quantity': 1,
                            'account_id':
                            rec.tenancy_id.prop_ids.expense_account_id.id or
                            False,
                            'account_analytic_id': rec.tenancy_id.id or False,
                        }
                        if rec.tenancy_id.multi_prop:
                            for data in rec.tenancy_id.prop_id:
                                for account in \
                                        data.property_ids.expense_account_id:
                                    inv_line_main.update(
                                        {'account_id': account.id})
                property_owner = rec.tenancy_id.property_owner_id
                invo_values = {
                    'partner_id': property_owner.id or False,
                    'type': 'in_invoice',
                    'invoice_line_ids': [(0, 0, inv_lines_values)],
                    'property_id': rec.tenancy_id.prop_ids.id or False,
                    'date_invoice': datetime.now().strftime(
                        DEFAULT_SERVER_DATE_FORMAT) or False,
                    'account_id':
                    property_owner.property_account_payable_id.id,
                }
                if rec.tenancy_id.main_cost:
                    invo_values.update(
                        {'invoice_line_ids': [(0, 0, inv_lines_values),
                                              (0, 0, inv_line_main)]})
                else:
                    invo_values.update(
                        {'invoice_line_ids': [(0, 0, inv_lines_values)]})

                acc_id = inv_obj.create(invo_values)
                rec.write({'invc_id': acc_id.id, 'inv': True})
                return {
                    'view_type': 'form',
                    'view_id': wiz_form_id,
                    'view_mode': 'form',
                    'res_model': 'account.invoice',
                    'res_id': rec.invc_id.id,
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'context': rec._context,
                }
            return super(TenancyRentSchedule, rec).create_invoice()

    @api.multi
    def open_invoice(self):
        """
        Description:
            This method is used to open invoice which is created.

        Decorators:
            api.multi
        """
        if self.tenancy_id.is_tenancy_rent:
            context = dict(self._context or {})
            wiz_form_id = self.env.ref('account.invoice_supplier_form').id
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
        return super(TenancyRentSchedule, self).open_invoice()
