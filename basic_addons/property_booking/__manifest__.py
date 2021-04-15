# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
{
    'name': 'Property Booking',
    'version': '2.1',
    'category': 'Real Estate',
    'description': """
    Property Management System

    This module gives the features for create property
    with gross value, number of towers, ground rent etc.
    also create sub property. where you can mentions Parent
    Property,number of floors , properties per floor,etc.
    and show sub property status either it's available or
    booked or any other states.
     """,
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'depends': ['property_management'],
    'data': ['security/ir.model.access.csv',
             'wizard/merge_property_wizard_view.xml',
             'wizard/property_book_wizard.xml',
             "views/property_booking_view.xml"],
    'demo': ['data/property_booking_data.xml'],

    'auto_install': False,
    'installable': True,
    'application': True,
}
