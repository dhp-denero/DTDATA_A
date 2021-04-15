# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
import datetime
from openerp import models, fields, api , exceptions, _

class Detalle_simple_fisico_total_d(models.Model):
	_inherit = 'detalle.simple.fisico.total.d'
	location_id = fields.Char('Ubicación')

class Detalle_simple_fisico_total_d_wizard(models.TransientModel):
	_inherit = 'detalle.simple.fisico.total.d.wizard'

	@api.multi
	def do_rebuild(self):
		self.env.cr.execute(""" 
			drop view if exists detalle_simple_fisico_total_d;
			create view detalle_simple_fisico_total_d as (

					select row_number() OVER () AS id,* from (
					
select almacen,producto,categoria,st.name as location_id,saldo,saldo_fisico,
	por_ingresar,transito,salida_espera,reservas,saldo_virtual,
	id_stock_disponible,
	 id_saldo_fisico,
	 id_por_ingresar,
	 id_transito,
	 id_salida_espera,
	 id_reservas,
	 id_previsto
	from (select ubicacion as almacen, product_id as producto, pt.categ_id as categoria, 
	sum(stock_disponible) as saldo,
	sum(saldo_fisico) as saldo_fisico,
	sum(por_ingresar) as por_ingresar,
	sum(transito) as transito,
	sum(salida_espera) as salida_espera,
	sum(reservas) as reservas, 
	sum(previsto) as saldo_virtual,

	replace(replace(array_agg(id_stock_disponible)::text,'{','['),'}',']') as id_stock_disponible,
	replace(replace(array_agg(id_saldo_fisico)::text,'{','['),'}',']') as id_saldo_fisico,
	replace(replace(array_agg(id_por_ingresar)::text,'{','['),'}',']') as id_por_ingresar,
	replace(replace(array_agg(id_transito)::text,'{','['),'}',']') as id_transito,
	replace(replace(array_agg(id_salida_espera)::text,'{','['),'}',']') as id_salida_espera,
	replace(replace(array_agg(id_reservas)::text,'{','['),'}',']') as id_reservas,
	replace(replace(array_agg(id_previsto)::text,'{','['),'}',']') as id_previsto

	from vst_kardex_onlyfisico_total
	inner join product_template pt on pt.id = product_tmpl_id
	where vst_kardex_onlyfisico_total.date >= '"""+str(self.fiscalyear_id.name)+"""-01-01'
	and vst_kardex_onlyfisico_total.date <= '"""+str(self.fiscalyear_id.name)+"""-12-31'
	group by ubicacion, product_id, pt.categ_id
	
	order by ubicacion,product_id, pt.categ_id)
	T 
	left join stock_location_it st on (st.product_id = product_id)

		) Todo
			); 
			""")
		view_id = self.env.ref('kardex_product_saldofisico_it.view_kardex_fisico_d',False)
		return {
			'type'     : 'ir.actions.act_window',
			'res_model': 'detalle.simple.fisico.total.d',
			# 'res_id'   : self.id,
			'view_id'  : view_id.id,
			'view_type': 'form',
			'view_mode': 'tree',
			'name': 'Saldos',
			'views'    : [(view_id.id, 'tree')],
			#'target'   : 'new',
			#'flags'    : {'form': {'action_buttons': True}},
			#'context'  : {},
		}