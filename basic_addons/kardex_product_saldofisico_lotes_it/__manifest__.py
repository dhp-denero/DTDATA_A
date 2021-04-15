# -*- encoding: utf-8 -*-
{
	'name': 'Saldos Kardex Producto SaldoFisico Lotes IT',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['stock','kardex_it','sales_team'],
	'version': '1.0',
	'description':"""
	Reporte de saldos con numeros de lote. Se recomienda no utilizar Reopen en los albaranes (stock_cancel).
	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_invoice_view.xml'],
	'installable': True
}
