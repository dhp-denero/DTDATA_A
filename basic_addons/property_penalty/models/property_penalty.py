# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    penalty = fields.Float(
        string='Penalty (%)')
    penalty_day = fields.Integer(
        string='Penalty Count After Days')
    penalty_a = fields.Boolean(
        'Penalty',
        default=True)


class TenancyRentSchedule(models.Model):
    _inherit = "tenancy.rent.schedule"
    _rec_name = "tenancy_id"
    _order = 'start_date'

    penalty_amount = fields.Float(
        string='Penalty',
        store=True)

    @api.multi
    def calculate_penalty(self):
        """
        This Method is used to calculate penalty.
        -----------------------------------------
        @param self: The object pointer
        """
        for one_payment_line in self:
            today_date = datetime.today().date()
            if not one_payment_line.paid:
                ten_date = datetime.strptime(
                    one_payment_line.start_date,
                    DEFAULT_SERVER_DATE_FORMAT).date()
                if one_payment_line.tenancy_id.penalty_day != 0:
                    ten_date = ten_date + \
                        relativedelta(
                            days=int(one_payment_line.tenancy_id.penalty_day))
                if ten_date < today_date:
                    if (today_date - ten_date).days:
                        line_amount_day = \
                            (one_payment_line.tenancy_id.rent *
                             one_payment_line.tenancy_id.penalty) / 100
                        one_payment_line.write(
                            {'penalty_amount': line_amount_day})
        return True
