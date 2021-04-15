# -*- coding: utf-8 -*-
{
    'name': "Sale Report Moliplast",

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
    'depends': ['import_base_it','new_sale_order_it'],
    # always loaded
    'data': ['report_sale_moliplast.xml'],
    # only loaded in demonstration mode
    'demo': [],
    'auto_install': False,
    'installable': True,
    'application': True
}
