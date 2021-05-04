# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
from odoo import api, fields, models


class PropertyPerLocationReport(models.AbstractModel):
    _name = "report.property_management.report_property_per_location1"

    def property_location(self, data, state):
        property_obj = self.env['account.asset.asset']

        if not data:
            if state and state.id:
                domain = [('state_id', '=', state.id)]
            else:
                domain = []
        elif data:
            domain = [('state_id', '=', data['state_id'][0])]

        property_rec = property_obj.search(domain)
        property_list = []
        for property_data in property_rec:
            if property_data.child_ids:
                property_list = [{
                    'name': property_data.name,
                    'child_ids': sub.name,
                    'city': sub.city,
                    'state_id': property_data.state_id.name,
                    'township': sub.township
                }for sub in property_data.child_ids]
            else:
                if property_data.id not in property_data.child_ids.ids:
                    property_dict = {
                        'name': property_data.name,
                        'child_ids': False,
                        'city': property_data.city,
                        'state_id': property_data.state_id.name,
                        'township': property_data.township
                    }
                    property_list.append(property_dict)
        return property_list

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(
            self.env.context.get('active_ids', []))

        state_id = data.get('state_id')[0]

        detail_res = self.with_context(
            data.get('used_context', {})).property_location(data, state_id)
        docargs = {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data,
            'docs': docs,
            'property_location': detail_res,
        }
        return self.env['report'].render(
            'property_management.report_property_per_location1', docargs)
