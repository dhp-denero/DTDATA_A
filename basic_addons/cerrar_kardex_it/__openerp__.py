# -*- encoding: utf-8 -*-
{
	'name': 'Aprobaciones IT',
	'category': 'account',
	'author': 'ITGRUPO-OBSOLETO',
	'depends': ['import_base_it','gastos_vinculados_it'],
	'version': '1.0',
	'description':"""
		Permisos para Aprobar en los modulos contables y de gestion
	""",
	'auto_install': False,
	'demo': [],
	'data':	['security/purchase_national_security.xml','account_journal_view.xml'],
	'installable': True
}
