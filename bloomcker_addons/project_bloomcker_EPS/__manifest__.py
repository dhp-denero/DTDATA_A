# -*- coding: utf-8 -*-
{
    "name": """Modulo Bloomcker EPS""",
    "summary": """Bloomcker""",
    "description": """Modulo para incluir funsiones EPS""",
    "author": "Luis Millan",
    "depends": [
        "base",
        "planilla"
    ],
    "data": [
        'views/eps_base.xml',
        'views/hr_employee_ext_views.xml',
        'views/payslip_ext.xml',
        'views/eps_base.xml',
        'security/ir.model.access.csv',
    ],
    "application": True,
}