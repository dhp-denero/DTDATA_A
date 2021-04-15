# -*- encoding: utf-8 -*-
{
	'name': 'Fix: Precio unitario en stock-move de P.C.',
	'version': '2.0',
	'category': '',
	'description': """
		- Problema resolver: Cuando se asigna una cantida mayor a la cantidad predeterminada en un stock.pack.operation, asigna el standard.price del producto. El comportamiento esperado es que aisgne el precio unitario asignado en la línea de pedido de compra del cual proviene.
		- Asignación de precio según pedido de compra en stock-moves generados a partir de un 
			albarán de pedido de venta.
	""",
	'author': "ITGRUPO-COMPATIBLE-BO",
	'website': "https://www.itgrupo.net",
	'depends': ['base','purchase'],
	
	'data': [],
	'demo': [],
	'installable': True,
	'auto_install': False,
	'application': True,
}