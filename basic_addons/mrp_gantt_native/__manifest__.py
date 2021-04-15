# -*- coding: utf-8 -*-
{
    "name": """Gantt Native view for MRP - Manufacture""",
    "summary": """MRP - MAnufacture - Gantt""",
    "category": "Project",
    "images": ['static/description/icon.png'],
    "version": "10.19.06.16.0",
    "description": """
        Update 1: Done on Gantt, Ghosts bar on Gantt. Manufacture support.
        Update 2:
        Removed: required for that "Deadline Gantt" 
        Update: date_planned_finished make visible
        Update: Gantt in Dashboard
        Update: Fix MRP readonly
        Update: Sorting and Deadline

""",
    "author": "Viktor Vorobjov",
    "license": "OPL-1",
    "website": "https://straga.github.io",
    "support": "vostraga@gmail.com",
    "live_test_url": "https://demo.garage12.eu",

    "depends": [
        "mrp",
        "web_gantt_native",
    ],
    "external_dependencies": {"python": [], "bin": []},
    "data": [
        'views/mrp_production_view.xml',
        'views/mrp_workorder_view.xml',
        'views/mrp_workcenter_views.xml',
        'views/mrp_workcenter_productivity.xml',
    ],
    "qweb": [],
    "demo": [],

    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,
    "installable": True,
    "auto_install": False,
    "application": False,
}