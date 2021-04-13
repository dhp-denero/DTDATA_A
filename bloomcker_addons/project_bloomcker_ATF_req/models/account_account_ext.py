# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging


class AccountAccountExt(models.Model):
    _inherit = 'account.account'

    analytic_account_id = fields.Many2one('account.analytic.account','Cuenta Analítica')



class AccountInvoiceLineExt(models.Model):
    _inherit = 'account.invoice.line'

    @api.onchange('account_id')
    def _onchange_account_id(self):
        try:
            self.account_analytic_id = self.account_id.analytic_account_id
        except:
            pass


class AccountAnalyticExt(models.Model):
    _inherit = 'account.analytic.distribution.it'

    cuenta_contable = fields.Many2one('account.account',string ="Cta. Contable", related="analytic_line_id.account_account_moorage_id")




