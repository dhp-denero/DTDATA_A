# -*- coding: utf-8 -*-
{
    "name": """Gantt Native Web view""",
    "summary": """Added support Gantt Chart Widget View""",
    "category": "Project",
    "images": ['static/description/icon.png'],
    "version": "10.19.12.02.0",
    "description": """
        Update 1: Add Milestone icon on Gantt bar.
        Update 2: Add Progress Bar and Task Nanme on Gantt.
        Update 3: Add New Scale.
        Update 4: link between tasks with arrows.
        Update 5: Gantt for Sub-task View.
        Update 6: Done on Gantt, Ghosts bar on Gantt. Manufacture support.
        fix: Sorted if more that 10.
        Update 7: Autosheduling support and constraint for tasks.
        fix: Can't change project if predecessor exist.
        Update 8: Progress bar get name from model.
        Update 9: Autosheduling support with Predecessor Lag and Summary Task.
        fix: some Gui layout.
        Update 10: Custom Color for Task.
        Update 11: Start Date for Project.
        Update 12: Today and Scale button in Odoo Native place.
        Frozen Header and horizontal - vertical scroll.
        fix: small fix about hint and tip.
        Update 13: In project you can set' humanized duration scale for tasks.
        Update 14: humanized duration scale for tasks add round: true.
        fix: momentjs fix
        Update 15: Calendar
        Update: Info bar before and after Gantt Bar (it can use for addition info)
        Update: Project manual start - and date, sorting from kanban / stage, small fix.
        fix: sort problem
        Update: Drag UI.
        Update: bug fix group by date
        Update: Folding
        Update: Remove Canvas and Draw Line by div.
        Update: version and remove js canvas
        Fix: arrow FF position for UI, readonly check
        Fix: Edge horizonal scroll
        UI: improve
        UI: improve more
        UI: Fix horizonatal scroll.
        Update: Taks info and Critocal path
        Update: UI not need to much block
        Update: Detail plan, fix ghost bar, fix default start time: allow neagative value..
        Fix: mouse flicker. 
        Update: UI - new arrows designe.
        Update: added - bar load.
        Fix: some fix gantt bar
        Update: Loop Detect.
        Update: Add subtask in group, from tree
        Fix: Model load
        Update: Sorting and Deadline
        FIX: UI el sorted
        Update: UI tree update
        FIX: calendar, Tree save
        Update: Fold Save and List view
    """,

    "author": "Viktor Vorobjov",
    "license": "OPL-1",
    "website": "https://straga.github.io",
    "support": "vostraga@gmail.com",
    "price": 299.00,
    "currency": "EUR",
    "live_test_url": "https://demo.garage12.eu",

    "depends": [
        "web", "web_widget_time_delta"
    ],
    "external_dependencies": {"python": [], "bin": []},
    "data": [
        'views/web_gantt_src.xml',
    ],
    "qweb": [
        'static/src/xml/*.xml',

    ],
    "demo": [],

    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,
    "installable": True,
    "auto_install": False,
    "application": False,
}
