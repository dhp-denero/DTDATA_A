# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
{
    "name": "Property Rent Payment Voucher Report",
    "version": "1.0",
    "author": "Serpent Consulting Services Pvt. Ltd",
    "website": "http://www.serpentcs.com",
    "description": """
    Make report on payment receipt
    """,
    'depends': ['property_management'],
    'data': [
        'views/report_property_rent_templates.xml',
        'views/report_configuration_view.xml'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
