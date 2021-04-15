# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ContractReport(models.TransientModel):
    _name = 'contract.report'

    start_date = fields.Date(
        string='Start date',
        required=True)
    end_date = fields.Date(
        string='End date',
        required=True)

    @api.constrains('start_date', 'end_date')
    def check_date_overlap(self):
        """
        This is a constraint method used to check the from date smaller than
        the Exiration date.
        @param self : object pointer
        """
        for ver in self:
            if ver.start_date and ver.end_date:
                dt_from = datetime.strptime(
                    ver.start_date, DEFAULT_SERVER_DATE_FORMAT)
                dt_to = datetime.strptime(
                    ver.end_date, DEFAULT_SERVER_DATE_FORMAT)
                if dt_to < dt_from:
                    raise ValidationError(
                        'End date should be greater than Start Date!')

    @api.multi
    def open_contract_expiry_tree(self):
        """
        This method is used to open record in tree view between selected dates
        @param self : object pointer
        """
        analytic_obj = self.env["account.analytic.account"]
        wiz_form_id = self.env.ref(
            'property_management.property_analytic_view_tree').id
        for data1 in self:
            data = data1.read([])[0]
            start_date = data['start_date']
            end_date = data['end_date']
            tenancy_ids = analytic_obj.search(
                [('date', '>=', start_date), ('date', '<=', end_date)])
        return {'name': 'Tenancy Contract Expiary',
                'view_mode': 'tree',
                'view_id': wiz_form_id,
                'view_type': 'tree',
                'res_model': 'account.analytic.account',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'context': self._context,
                'domain': [('id', 'in', tenancy_ids.ids)],
                }

    @api.multi
    def print_report(self):
        """
        This method is used to printng a report
        @param self : object pointer
        """
        if self._context is None:
            self._context = {}
        data = {
            'ids': self.ids,
            'model': 'account.asset.asset',
            'form': self.read(['start_date', 'end_date'])[0]
        }
        return self.env['report'].get_action(
            self, 'property_management.report_contract_expiry', data=data)
