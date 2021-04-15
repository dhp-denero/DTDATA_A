# -*- encoding: utf-8 -*-
{
	'name': 'Exportar Planilla a Excel ScotiaBank',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['planilla','account_payment_bank_export_it'],
	'version': '1.0.0',
	'ITGRUPO_VERSION':2,
	'description': """
	Exportar Planilla a Excel ScotiaBank
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/hr_sbank_export_wizard.xml',
		'views/scotia_export_config.xml',
	],
	'installable': True
}
