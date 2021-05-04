# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import fields, models, tools


class InvestmentAnalysisReport(models.Model):
    _name = "investment.analysis.report"
    _auto = False

    active = fields.Boolean('Active')
    parent_id = fields.Many2one('account.asset.asset', 'Parent Property')
    type_id = fields.Many2one('property.type', 'Property Type')
    date = fields.Date('Purchase Date')
    purchase_price = fields.Float('Purchase Price')
    roi = fields.Float('ROI')
    return_period = fields.Float('Return Period')
    name = fields.Char('Property Name')

    def init(self):
        tools.drop_view_if_exists(self._cr, 'investment_analysis_report')
        self._cr.execute(
            """CREATE or REPLACE VIEW investment_analysis_report as
            SELECT id,name,active,type_id,parent_id,purchase_price,
                date,roi,return_period
            FROM account_asset_asset""")
