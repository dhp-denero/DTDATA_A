# -*- coding: utf-8 -*-
{
    "name": """Modulo Bloomcker Requerimientos de Paino""",
    "summary": """Bloomcker""",
    "description": """Requerimientos Especificos de Paino""",
    "author": "Luis Millan",
    "depends": [
        "base",
        "planilla",
        "hr_payroll"
    ],
    "data": [
        'views/hr_employee_form_view_ext.xml',
        'views/hr_payslip_run_views_ext.xml',
        'views/hr_loan_view_ext.xml',
        'views/hr_payslip_run_wizard.xml',
        'views/hr_planilla_cts_line_ext.xml',
        'data/cron_ext.xml',
        'report/contract.xml',
        'wizards/hr_payslip_run_wizard.xml',
    ],
    "application": True,
}
