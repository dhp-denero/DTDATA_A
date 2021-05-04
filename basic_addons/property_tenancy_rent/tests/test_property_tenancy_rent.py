# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
from odoo.tests import common
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class PropertyTenancyRent(common.TransactionCase):

    def setup(self):
        super(PropertyTenancyRent, self).setup()

    def test_property_action(self):
        # Tenancy/Tenancy Rent Schedule
        self.partner = self.env.ref('base.res_partner_2')
        self.property_demo = self.browse_ref("property_management.property3")
        self.rent_type = self.browse_ref("property_management.rent_type1")
        self.date_today = datetime.today()
        self.tenancy = self.env['account.analytic.account'].sudo().create(
            {
                'name': 'Tenancy for Glohork Villa',
                'prop_ids': self.property_demo.id,
                'state': 'draft',
                'is_tenancy_rent': True,
                'property_owner_id': self.partner.id,
                'deposit': 5000.00,
                'rent': 8000.00,
                'rent_entry_chck': False,
                'date_start': datetime.today(),
                'date': datetime.today(),
            })
        self.cur = self.browse_ref('base.in')
        self.rent = self.env['tenancy.rent.schedule'].sudo().create(
            {
                'start_date': datetime.today(),
                'amount': 8000.00,
                'currency_id': self.cur.id,
            })
