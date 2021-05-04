# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
{
    'name': 'Multiple Property Rent',
    'version': '2.0',
    'category': 'Real Estate',
    'description': """
    Property Management System

    Odoo Property Management System will help you to manage your real estate
    portfolio with Property valuation, Maintenance, Insurance, Utilities and
    Rent management with reminders for each KPIs. ODOO's easy to use Content
    management system help you to display available property on website with
    its gallery and other details to reach easily to end users. With the help
    of inbuilt Business Intelligence system it will be more easy to get various
    analytical reports and take strategical decisions.
     """,
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'depends': ['property_management'],
    'data': ['security/ir.model.access.csv',
             'views/multiple_property_rent_view.xml'],
    'auto_install': False,
    'installable': True,
    'application': True,
}
