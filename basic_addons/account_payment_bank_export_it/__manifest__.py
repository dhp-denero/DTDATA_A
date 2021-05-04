# -*- encoding: utf-8 -*-
{
	'name': 'Exportador de pagos multiples a telebanco',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['account_multipayment_invoices_it_advance','payment'],
	'version': '1.0',
	'description':"""
		Exportador de pagos multiples a telebanco
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/config_export_values.xml',
		'views/res_partner_bank.xml',
		'views/mulltipayment_advance_invoice.xml',
		'wizard/export_multipayment_bank_wizard.xml',
		'wizard/view_makedata.xml',
		],
	'installable': True
}