# -*- coding: utf-8 -*-
{
    "name": """Modulo Bloomcker Quinta""",
    "summary": """Bloomcker""",
    "description": """Modulo para las Reparaciones de Quinta""",
    "author": "Luis Millan",
    "depends": [
        "base",
        "planilla"
    ],
    "data": [
        'views/quinta_ext_view.xml',
        'views/payslip_ext.xml',
        'views/planilla_liquidacion_view.xml',
        'wizard/certificate_quinta_wizard.xml',
        'reports/report_certificate_quinta.xml',
        'reports/report_data.xml',
        'security/ir.model.access.csv'
    ],
    "application": True,
}
