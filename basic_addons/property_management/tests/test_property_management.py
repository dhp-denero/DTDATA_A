# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
from datetime import datetime
from odoo.tests import common


class PropertyManagementTestCase(common.TransactionCase):

    def setup(self):
        super(PropertyManagementTestCase, self).setup()

    def test_property_action(self):
        # Property Created
        self.property_type = self.browse_ref(
            'property_management.property_type1')
        self.partner = self.browse_ref('base.res_partner_2')
        self.property_demo = self.browse_ref("property_management.property1")
        self.rent_type = self.browse_ref("property_management.rent_type1")
        self.asset = self.env['account.asset.asset'].sudo().create(
            {
                'name': 'Radhika Recidency',
                'type_id': self.property_type,
                'state': self.property_demo.state,
                'street': self.property_demo.street,
                'city': self.property_demo.city,
                'country_id': self.property_demo.country_id.id,
                'state_id': self.property_demo.state_id.id,
                'zip': self.property_demo.zip,
                'age_of_property': self.property_demo.age_of_property,
                'category_id': self.property_demo.category_id.id,
                'value': self.property_demo.value,
                'value_residual': self.property_demo.value_residual,
                'ground_rent': self.property_demo.ground_rent,
                'sale_price': self.property_demo.sale_price,
                'furnished': self.property_demo.furnished,
                'facing': self.property_demo.facing,
                'type_id': self.property_demo.type_id.id,
                'floor': self.property_demo.floor,
                'bedroom': self.property_demo.bedroom,
                'bathroom': self.property_demo.bathroom,
                'gfa_meter': self.property_demo.gfa_meter,
                'gfa_feet': self.property_demo.gfa_feet,
                'parent_id': self.property_demo.parent_id,
                'property_manager': self.property_demo.property_manager.id,
                'income_acc_id': self.property_demo.income_acc_id.id,
                'expense_account_id': self.property_demo.expense_account_id.id,
                'rent_type_id': self.rent_type.id,
            }
        )

        # Tenant Create
        self.tenant = self.browse_ref('property_management.tenant2')
        self.tenant_partner = self.env['tenant.partner'].sudo().create(
            {
                'name': 'HET',
                'email': 'het@gmail.com',
                'country_id': self.property_demo.country_id.id,
                'tenant': True
            })
        # Tenancy/Tenancy Rent Schedule
        self.details = self.browse_ref(
            'property_management.property_tenancy_t0')
        self.property_id = self.browse_ref('property_management.property_8')
        self.date_today = datetime.today()
        self.tenancy = self.env['account.analytic.account'].sudo().create(
            {
                'name': 'Tenancy for Radhika Recidency',
                'property_id': self.asset.id,
                'state': 'draft',
                'is_property': True,
                'tenant_id': self.tenant_partner.id,
                'deposit': 5000.00,
                'rent': 8000.00,
                'rent_entry_chck': False,
                'date_start': datetime.today(),
                'date': datetime.today(),
                'rent_type_id': self.rent_type.id,
            })
        self.tenancy.button_start()
        self.tenancy.create_rent_schedule()
        self.tenancy.button_receive()
        self.tenancy.button_return()
        self.tenancy.button_close()
        # Create Mintenance
        self.maint_type = self.browse_ref(
            'property_management.maintenance_type1')
        self.worker = self.browse_ref('property_management.worker1')
        self.maint = self.env['property.maintenance'].sudo().create(
            {
                'property_id': self.asset.id,
                'type': self.maint_type.id,
                'date': datetime.today(),
                'name': 'Repair',
                'cost': 250,
                'assign_to': self.worker.id,
            })
