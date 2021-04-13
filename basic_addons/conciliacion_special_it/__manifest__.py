# -*- coding: utf-8 -*-
{
    'name': "Exchange Diff IT",

    'summary': """
        Modulo de diferencias de cambio""",

    'description': """
        Modulo de diferencias de cambio
    """,
    'author': "ITGRUPO-COMPATIBLE-BO",
    'category': 'account',
    'version': '1.0',

    'depends': ['account','res_currency_rate_it','import_base_it'],

    'data': [
        'views/exchange_diff_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
