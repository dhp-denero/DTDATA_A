# -*- coding: utf-8 -*-
{
    "name": "Property Management",
    # 'version': '10.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:

    """,

    "category": "Property",
    "depends": ['mail'],
    "images": ['images/main_screenshot.png'],
    "license":"LGPL-3",
    "data": [
        'views/property_menu_view.xml',
        'views/property_config_view.xml',
        'views/property_land_view.xml',
        'views/property_building_view.xml',
        'views/property_room_view.xml',
        'data/data.xml',
        'data/res.country.state.csv',
        'security/ir.model.access.csv'

    ],
    'application': True,
    "active": True,
    "installable": True,
}