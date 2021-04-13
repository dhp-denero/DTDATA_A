# -*- coding: utf-8 -*-
{
    "name": """Modulo Bloomcker""",
    "summary": """Bloomcker""",
    "description": """Modulo de Corrección""",
    "author": "Luis Millan",
    "depends": [
        "base",
        "report",
        "sale",
        "project",
        "sale_crm"
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/crm_lead_ext_view.xml',
        'views/project_task_ext_view.xml',
        'views/project_project_ext_view.xml',
        'views/sale_order_ext.xml',
        'reports/project_sinerge_bl.xml',
        'reports/sale_order_sinerge_bl.xml',
        'reports/reports_data_bl.xml',
        'reports/compare_report_crm_lead.xml',
        'reports/crossovered_budget_sinerge_report.xml',
    ],
    "application": True,
}
