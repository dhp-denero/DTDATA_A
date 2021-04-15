# -*- encoding: utf-8 -*-
{
	'name': 'Importar Empleados planilla IT',
	'category': 'account',
	'author': 'ITGRUPO-OPCIONAL-COMPATIBLE-BO',
	'depends': ['planilla'],
	'version': '1.0.0',
	'ITGRUPO_VERSION':1,
	'description':"""
        - importa por primera vez la lista de empleados
	""",
	'auto_install': False,
	'demo': [],
	'data':	['views/planilla_importar_empleados_view.xml','views/menu.xml'],
	'installable': True
}
