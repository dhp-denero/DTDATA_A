# -*- coding: utf-8 -*-
{
    'name': "delete option forzar",

    'description': """
        
    """,

    'author': "ITGRUPO-POWER",
    'website': "http://www.itgrupo.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': '',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['import_base_it','stock_picking_mass_action'],
    # always loaded
    'data': ['delete_option_forzar.xml'],
    # only loaded in demonstration mode
    'demo': [],
    'auto_install': False,
    'installable': True,
    'application': True
}
