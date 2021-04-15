# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp import models,fields ,api
from odoo.exceptions import UserError, ValidationError

class contenedor_guardado_kardex(models.Model):
	_name = 'contenedor.guardado.kardex'

	almacen = fields.Integer('Almacen')
	producto = fields.Integer('Producto')
	ingreso  = fields.Float('Periodo')
	salida = fields.Float('Periodo')
	saldofisico = fields.Float('Periodo')
	haber = fields.Float('Periodo')
	debe = fields.Float('Periodo')
	saldo = fields.Float('Periodo')
	period_id = fields.Integer('Periodo')

class guardado_kardex(models.Model):
	_name='guardado.kardex'
	
	period_id = fields.Many2one('account.period','Periodo',required=True)


	@api.multi
	def ver_informe(self):
		param = self.env['main.parameter'].search([])[0]
		new_param = self.env['main.parameter'].search([])[0]

		self.env.cr.execute("""
			delete from contenedor_guardado_kardex where period_id = """ +str(self.period_id.id)+ """;

			insert into contenedor_guardado_kardex			
		select row_number() OVER () AS id,almacen_id as almacen, product_id as producto,sum(ingreso) as ingreso, sum(salida) as salida, sum(ingreso-salida) as saldofisico, sum(credit) as haber, sum(debit) as debe,sum(debit-credit) as saldo, """ +str(self.period_id.id)+ """ as period_id from (	
select periodo,fecha,almacen,debit,credit,ingreso,salida,t1.product_id,t1.location_id as almacen_id,ubicacion_origen,ubicacion_destino,aa4.id as cuenta_salida, aa5.id as cuenta_valuacion, aaa.id as cta_analitica from (	
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
--  colocar aca el periodo para el cual se quiere sacar el costo de ventas	
periodo='""" +self.period_id.code+ """'	
)ab	
group by almacen_id,product_id;
			
			""")