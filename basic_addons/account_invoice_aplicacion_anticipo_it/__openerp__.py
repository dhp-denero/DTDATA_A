# -*- encoding: utf-8 -*-
{
	'name': 'Aplicacion de Anticipo Power',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['import_base_it','ebill_nf'],
	'version': '1.0',
	'description':"""
			Generar Aplicacion de Anticipo
	""",
	'auto_install': False,
	'demo': [],
	'data':[
		'account_invoice_reemplazar_view.xml'
	],
	'installable': True
}