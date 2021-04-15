# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import fields, models, tools


class PropertyFinanceReport(models.Model):
    _name = "property.finance.report"
    _auto = False

    type_id = fields.Many2one('property.type', 'Property Type')
    date = fields.Date('Purchase Date')
    parent_id = fields.Many2one('account.asset.asset', 'Parent Property')
    name = fields.Char("Parent Property")
    purchase_price = fields.Float('Purchase Price')

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute(
            """CREATE or REPLACE VIEW property_finance_report as
            SELECT id,name,type_id,purchase_price,date
            FROM account_asset_asset""")
