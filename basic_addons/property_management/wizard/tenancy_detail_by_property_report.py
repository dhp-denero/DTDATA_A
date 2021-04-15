# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class TenancyPropertyReport(models.TransientModel):
    _name = 'tenancy.property.report'

    start_date = fields.Date(
        string='Start date',
        required=True)
    end_date = fields.Date(
        string='End date',
        required=True)
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property',
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
    def open_tenancy_by_property_gantt(self):
        """
        This method is used to open record in gantt view between selected dates
        @param self : object pointer
        """
        wiz_form_id = self.env.ref(
            'property_management.view_analytic_gantt').id
        analytic_obj = self.env['account.analytic.account']
        for data_rec in self:
            data = data_rec.read([])[0]
            start_date = data['start_date']
            end_date = data['end_date']
            property_id = data['property_id'][0]
            tenancy_ids = analytic_obj.search(
                [('property_id', '=', property_id),
                 ('date_start', '>=', start_date),
                 ('date_start', '<=', end_date)])
            return {
                'view_type': 'form',
                'view_id': wiz_form_id,
                'view_mode': 'gantt',
                'res_model': 'account.analytic.account',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'context': self._context,
                'domain': [('id', 'in', tenancy_ids.ids)],
            }

    @api.multi
    def open_tenancy_by_property_tree(self):
        """
        This method is used to open record in tree view between selected dates
        @param self : object pointer
        """
        wiz_form_id = self.env.ref(
            'property_management.property_analytic_view_tree').id
        analytic_obj = self.env['account.analytic.account']
        for data_rec in self:
            data = data_rec.read([])[0]
            start_date = data['start_date']
            end_date = data['end_date']
            property_id = data['property_id'][0]
            tenancy_ids = analytic_obj.search(
                [('property_id', '=', property_id),
                 ('date_start', '>=', start_date),
                 ('date_start', '<=', end_date)])
            return {
                'name': 'Tenancy Report By Property',
                'view_type': 'tree',
                'view_id': wiz_form_id,
                'view_mode': 'tree',
                'res_model': 'account.analytic.account',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'context': self._context,
                'domain': [('id', 'in', tenancy_ids.ids)],
            }

    @api.multi
    def print_report(self):
        partner_obj = self.env['account.asset.asset']
        if self._context is None:
            self._context = {}
        for data_rec in self:
            data = data_rec.read([])[0]
            partner_rec = partner_obj.browse(data['property_id'][0])
            data.update({'property_name': partner_rec.name})
        data = {
            'ids': self.ids,
            'model': 'account.asset.asset',
            'form': data
        }
        return self.env['report'].get_action(
            self, 'property_management.report_tenancy_by_property', data=data)
