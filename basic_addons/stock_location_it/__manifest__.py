# -*- coding: utf-8 -*-
{
    'name': u"Almacén Power",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "ITGRUPO-POWER",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock','product','kardex_product_saldofisico_it'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_product_form.xml',
        'views/stock_location_it_views.xml',
        'views/extended_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
