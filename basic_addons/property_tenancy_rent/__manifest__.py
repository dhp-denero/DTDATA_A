# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
{
    'name': 'Property Tenancy Rent',
    'version': '2.1',
    'category': 'Real Estate',
    'description': """
        Property Management System

        This module gives the features for create property with gross value,
        number of towers, ground rent etc. also create sub property.
        where you can mentions Parent Property,number of floors , properties
        per floor,etc. and show sub property status either it's available or
        booked or any other states.
     """,
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'depends': ['property_management'],
    'data': [
        'data/tenancy_rent_sequence.xml',
        'views/analytic_account_view.xml',
        'views/asset_view.xml',
    ],
    'demo': ['data/tenancy_rent_demo.xml'],
    'auto_install': False,
    'installable': True,
    'application': True,
}
