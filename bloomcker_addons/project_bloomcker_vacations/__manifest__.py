# -*- coding: utf-8 -*-
{
    "name": """Modulo Bloomcker Vacaciones""",
    "summary": """Bloomcker""",
    "description": """Modulo para la Gestión de Vacaciones""",
    "author": "Luis Millan",
    "depends": [
        "base",
        "planilla"
    ],
    "data": [
        'views/vacations_bl_view.xml',
        'views/hr_nomina_ext.xml',
        'views/break_bl_view.xml',
        'views/payslip_ext.xml',
        'data/data_config.xml',
        'security/ir.model.access.csv',
    ],
    "application": True,
}
