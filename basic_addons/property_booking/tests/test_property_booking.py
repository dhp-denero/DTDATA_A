# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
from odoo.tests import common


class PropertyBookingTestCase(common.TransactionCase):

    def setup(self):
        super(PropertyBookingTestCase, self).setup()

    def test_property_booking(self):
        # Property Created
        self.property_type = self.browse_ref(
            'property_management.property_type2')
        self.partner = self.browse_ref('base.res_partner_2')
        self.property_demo = self.browse_ref("property_management.property1")
        self.booking = self.env['property.created'].sudo().create(
            {
                'is_sub_property': True,
                'name': 'Radhika Recidency Booking',
                'parent_id':  self.property_demo.id,
                'category_id': self.property_demo.category_id.id,
                'property_manager': self.property_demo.property_manager.id,
                'type_id': self.property_type.id,
                'prefix3': '2',
                'floor': 5,
                'value': 1500000.00,
                'no_of_property': 4,
            }
        )
        self.booking.create_property()
