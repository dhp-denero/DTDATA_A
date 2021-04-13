# -*- encoding: utf-8 -*-
{
	'name': u'Export File Manager IT',
	'category': 'reports',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['base','report'],
	'version': '10.0',
	'description':"""
	Módulo para gestionar la descarga de reportes PDF y Excel a través del objeto export.file.manager.
	- Compatible con la versión 10.0 de Odoo.
	- Descarga directa de reportes.
	- Desarrollo: Leo de Oz
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/templates.xml',
	],
    'qweb':[
        'static/src/xml/export_file_manager_tmpl.xml',
    ],
	'installable': True
}
