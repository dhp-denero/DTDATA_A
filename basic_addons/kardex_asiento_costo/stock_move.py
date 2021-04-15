# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp import models,fields ,api
from odoo.exceptions import UserError, ValidationError

class detalle_costo_produccion(models.Model):
	_name = 'detalle.costo.produccion'

	almacen = fields.Many2one('stock.location','Almacen')
	producto = fields.Many2one('product.product','Producto')
	cta_analitica = fields.Many2one('account.analytic.account','Cta. Analitica')
	debe = fields.Float('Debe')
	haber = fields.Float('Haber')
	costo_consumo = fields.Float('Costo Consumo')
	cuenta_valuacion = fields.Many2one('account.account','Cuenta Valuacion')
	cuenta_salida = fields.Many2one('account.account','Cuenta Salida')

class main_parameter(models.Model):
	_inherit = 'main.parameter'

	operacion_salida_prod = fields.Many2one('einvoice.catalog.12','Operacion de Salida')
	operacion_devolucion_prod = fields.Many2one('einvoice.catalog.12','Operacion de Devolucion')


class asiento_costo_produccion(models.Model):
	_name='asiento.costo.produccion'
	
	period_id = fields.Many2one('account.period','Periodo',required=True)


	@api.multi
	def ver_informe(self):
		param = self.env['main.parameter'].search([])[0]
		new_param = self.env['main.parameter'].search([])[0]

		self.env.cr.execute("""
			drop table if exists detalle_costo_produccion cascade;
			create table detalle_costo_produccion as
			(

		select row_number() OVER () AS id,almacen_id as almacen, cuenta_salida, cuenta_valuacion , product_id as producto,sum(credit) as haber,sum(debit) as debe,sum(credit-debit) as costo_consumo, """ +str(self.period_id.id)+ """ as period_id, cta_analitica as cta_analitica from (	
select periodo,fecha,almacen,debit,credit,t1.product_id,t1.location_id as almacen_id,ubicacion_origen,ubicacion_destino,aa4.id as cuenta_salida, aa5.id as cuenta_valuacion, aaa.id as cta_analitica from (	
-- aca se selecciona hasta que periodo se ejecuta el kardex ,  con los resultados se filtra solo el mes cuyo costo de ventas queremos calcular	
select * from get_kardex_v(""" +str(param.fiscalyear)+ """0101,""" +str(param.fiscalyear)+ """1231, (select array_agg(id) from product_product), (select array_agg(id) from stock_location ) ))t1	
left join stock_move sm on sm.id = t1.stock_moveid
left join account_analytic_account aaa on aaa.id = sm.analytic_account_id
left join stock_location t2 on t2.id=t1.location_id
inner join stock_location ori on ori.id = t1.ubicacion_destino
inner join stock_location dest on dest.id = t1.ubicacion_origen

inner join product_product pp on pp.id = t1.product_id
inner join product_template pt on pt.id = pp.product_tmpl_id
left outer join product_category  pc on pc.id = pt.categ_id

left outer join ir_property ip4a on (ip4a.res_id = 'product.category,' || COALESCE(pc.id,-1) ) and ip4a.name = 'property_stock_account_output_categ_id'
left outer join ir_property ip4 on (ip4.res_id is Null) and ip4.name = 'property_stock_account_output_categ_id'
left outer join account_account aa4 on aa4.id = (CASE WHEN ip4a.value_reference is not null then COALESCE( substring(ip4a.value_reference from 17)::int8, -1) else COALESCE( substring(ip4.value_reference from 17)::int8, -1) end )

left outer join ir_property ip5a on (ip5a.res_id = 'product.category,' || COALESCE(pc.id,-1) ) and ip5a.name = 'property_stock_valuation_account_id'
left outer join ir_property ip5 on ( ip5.res_id is Null) and ip5.name = 'property_stock_valuation_account_id'
left outer join account_account aa5 on aa5.id = ( CASE WHEN ip5a.value_reference is not null then COALESCE( substring(ip5a.value_reference from 17)::int8, -1) else COALESCE( substring(ip5.value_reference from 17)::int8, -1) end )

where 	
-- colocar aca la ubicacion de clientes que esta configurada en parametros de contabilidad pestan kardex tanto para origen como para el destino	
t1.operation_type in ('"""+ (new_param.operacion_salida_prod.code if new_param.operacion_salida_prod.id else '99494949') +"""','"""+ (new_param.operacion_devolucion_prod.code if new_param.operacion_devolucion_prod.id else '99494949') +"""')

--  colocar aca el periodo para el cual se quiere sacar el costo de ventas	
and periodo='""" +self.period_id.code+ """'	
)ab	
group by almacen_id,product_id, cuenta_salida,cta_analitica, cuenta_valuacion	

			)

			""")

		return {
				'type': 'ir.actions.act_window',
				'res_model': 'detalle.costo.produccion',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}
		

	@api.multi
	def crear_asiento(self):
		param = self.env['main.parameter'].search([])[0]
		new_param = self.env['main.parameter'].search([])[0]

		self.env.cr.execute("""
			drop table if exists detalle_costo_produccion cascade;
			create table detalle_costo_produccion as
			(

		select row_number() OVER () AS id,almacen_id as almacen, cuenta_salida, cuenta_valuacion , product_id as producto,round(sum(credit),2) as haber,round(sum(debit),2) as debe,round(sum(credit),2) - round(sum(debit),2) as costo_consumo, """ +str(self.period_id.id)+ """ as period_id, cta_analitica as cta_analitica from (	
select periodo,fecha,almacen,debit,credit,t1.product_id,t1.location_id as almacen_id,ubicacion_origen,ubicacion_destino,aa4.id as cuenta_salida, aa5.id as cuenta_valuacion, aaa.id as cta_analitica from (	
-- aca se selecciona hasta que periodo se ejecuta el kardex ,  con los resultados se filtra solo el mes cuyo costo de ventas queremos calcular	
select * from get_kardex_v(""" +str(param.fiscalyear)+ """0101,""" +str(param.fiscalyear)+ """1231, (select array_agg(id) from product_product), (select array_agg(id) from stock_location ) ))t1	
left join stock_move sm on sm.id = t1.stock_moveid
left join account_analytic_account aaa on aaa.id = sm.analytic_account_id
left join stock_location t2 on t2.id=t1.location_id
inner join stock_location ori on ori.id = t1.ubicacion_destino
inner join stock_location dest on dest.id = t1.ubicacion_origen

inner join product_product pp on pp.id = t1.product_id
inner join product_template pt on pt.id = pp.product_tmpl_id
left outer join product_category  pc on pc.id = pt.categ_id

left outer join ir_property ip4a on (ip4a.res_id = 'product.category,' || COALESCE(pc.id,-1) ) and ip4a.name = 'property_stock_account_output_categ_id'
left outer join ir_property ip4 on (ip4.res_id is Null) and ip4.name = 'property_stock_account_output_categ_id'
left outer join account_account aa4 on aa4.id = (CASE WHEN ip4a.value_reference is not null then COALESCE( substring(ip4a.value_reference from 17)::int8, -1) else COALESCE( substring(ip4.value_reference from 17)::int8, -1) end )

left outer join ir_property ip5a on (ip5a.res_id = 'product.category,' || COALESCE(pc.id,-1) ) and ip5a.name = 'property_stock_valuation_account_id'
left outer join ir_property ip5 on ( ip5.res_id is Null) and ip5.name = 'property_stock_valuation_account_id'
left outer join account_account aa5 on aa5.id = ( CASE WHEN ip5a.value_reference is not null then COALESCE( substring(ip5a.value_reference from 17)::int8, -1) else COALESCE( substring(ip5.value_reference from 17)::int8, -1) end )

where 	
-- colocar aca la ubicacion de clientes que esta configurada en parametros de contabilidad pestan kardex tanto para origen como para el destino	
t1.operation_type in ('"""+ (new_param.operacion_salida_prod.code if new_param.operacion_salida_prod.id else '99494949') +"""','"""+ (new_param.operacion_devolucion_prod.code if new_param.operacion_devolucion_prod.id else '99494949') +"""')

--  colocar aca el periodo para el cual se quiere sacar el costo de ventas	
and periodo='""" +self.period_id.code+ """'	
)ab	
group by almacen_id,product_id, cuenta_salida,cta_analitica, cuenta_valuacion	

			)

			""")

		
		param = self.env['main.parameter'].search([])[0]
		cabezado = {
			'journal_id':param.diario_destino.id,
			'date':self.period_id.date_stop,
			'ref':'COSTO VENTAS '+ self.period_id.code,
			'fecha_contable':self.period_id.date_stop,
			'ple_diariomayor':'1',
		}
		asiento = self.env['account.move'].create(cabezado)

		detalle = self.env['detalle.costo.produccion'].search([])

		if len(detalle) == 0:
			raise UserError('No hay detalle para generar el asiento.')


		self.env.cr.execute("""
				select almacen,cuenta_salida,cta_analitica, sum(costo_consumo) from detalle_costo_produccion
				group by almacen,cuenta_salida	,cta_analitica
			""")

		for i in self.env.cr.fetchall():
			if i[3]<0:
				raise UserError('Existe Negativos.')
			linea = {
				'name':'COSTO VENTAS '+self.period_id.code + ' ,almacen: ' + self.env['stock.location'].browse(i[0]).name,
				'account_id':i[1],
				'analytic_account_id':i[2],
				'debit':abs( i[3]),
				'credit':0,
				'move_id':asiento.id,
			}
			self.env['account.move.line'].create(linea)


		self.env.cr.execute("""
				select almacen,cuenta_valuacion, sum(costo_consumo) from detalle_costo_produccion
				group by almacen,cuenta_valuacion	
			""")

		for i in self.env.cr.fetchall():
			if i[2]<0:
				raise UserError('Existe Negativos.')

			linea = {
				'name':'COSTO VENTAS '+self.period_id.code + ' ,almacen: ' + self.env['stock.location'].browse(i[0]).name,
				'account_id':i[1],
				'debit':0,
				'credit':abs(i[2]),
				'move_id':asiento.id,
			}
			self.env['account.move.line'].create(linea)


		return {
				'type': 'ir.actions.act_window',
				'res_model': 'account.move',
				'view_mode': 'form',
				'view_type': 'form',
				'views': [(False, 'form')],
				'res_id':asiento.id,
			}		
