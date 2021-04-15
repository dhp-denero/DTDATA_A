# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import api, fields, models


class PropertyPerLocation(models.TransientModel):
    _name = 'property.per.location'

    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='State')

    @api.multi
    def print_report(self):
        for data1 in self:
            data = data1.read([])[0]
        return self.env['report'].get_action(
            self, 'property_management.report_property_per_location1',
            data=data)
