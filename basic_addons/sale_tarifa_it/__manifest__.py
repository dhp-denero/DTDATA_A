# -*- coding: utf-8 -*-
{
    'name': "Elementos de Tarifa",


    'description': """
        Long description of module's purpose
    """,

    'author': "ITGRUPO-OPCIONAL-TPV-COMPATIBLE-BO",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/sale_tarifa_form.xml',
    ],
}
