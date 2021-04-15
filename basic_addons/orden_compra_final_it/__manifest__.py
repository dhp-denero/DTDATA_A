# -*- coding: utf-8 -*-
{
    'name': "Orden Compra Moliplast",

    'description': """
        
    """,

    'author': "ITGRUPO-COMPATIBLE-BO",
    'website': "http://www.itgrupo.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': '',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['purchase','import_base_it'],
    # always loaded
    'data': ['report_purchase_moliplast.xml',
            'report_purchase_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'auto_install': False,
    'installable': True,
    'application': True
}
