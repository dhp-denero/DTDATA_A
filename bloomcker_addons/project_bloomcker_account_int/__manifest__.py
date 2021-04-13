# -*- coding: utf-8 -*-
{
    "name": """Modulo Bloomcker Cuentas Interbancarias""",
    "summary": """Bloomcker""",
    "description": """Modulo para incluir funsiones de Cuentas Interbancarias""",
    "author": "Luis Millan",
    "depends": [
        "base",
        "account"
    ],
    "data": [
        'views/inter_account_bank_views.xml',
        'views/hr_employee_ext_views.xml',
        'security/ir.model.access.csv',
    ],
    "application": True,
}