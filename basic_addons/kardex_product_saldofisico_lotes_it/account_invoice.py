# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv
from odoo.tools.misc import formatLang

import datetime

class detalle_simple_fisico_total_d_wizard_lotes(models.TransientModel):
	_name = 'detalle.simple.fisico.total.d.wizard.lotes'

	fiscalyear_id = fields.Many2one('account.fiscalyear', u'Año fiscal', required=True)

	@api.model
	def default_get(self, fields):
		res = super(detalle_simple_fisico_total_d_wizard_lotes,self).default_get(fields)
		n = str(datetime.datetime.now().year)
		af = self.env['account.fiscalyear'].search([('name','=',n)])
		res['fiscalyear_id'] = af[0].id if len(af) else False
		return res

	@api.multi
	def do_rebuild(self):
		self.env.cr.execute("""
			drop view if exists detalle_simple_fisico_total_d_lotes;
			create view detalle_simple_fisico_total_d_lotes as (



					select row_number() OVER () AS id,* from (
					select ubicacion as almacen, product_id as producto, pt.categ_id as categoria, lote as lote,
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

					from vst_kardex_onlyfisico_total_lotes
					inner join product_template pt on pt.id = product_tmpl_id
					where vst_kardex_onlyfisico_total_lotes.date >= '"""+str(self.fiscalyear_id.name)+"""-01-01'
					and vst_kardex_onlyfisico_total_lotes.date <= '"""+str(self.fiscalyear_id.name)+"""-12-31'
					and pt.tracking != 'none'
					group by ubicacion, product_id, lote, pt.categ_id
					order by ubicacion,product_id, lote, pt.categ_id
					) Todo


			);
			""")

		view_id = self.env.ref('kardex_product_saldofisico_it_acero.view_kardex_fisico_d_lotes',False)
		return {
			'type'     : 'ir.actions.act_window',
			'res_model': 'detalle.simple.fisico.total.d.lotes',
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

class detalle_simple_fisico_total_d_lotes(models.Model):
	_name = 'detalle.simple.fisico.total.d.lotes'

	producto = fields.Many2one('product.product','Producto')
	categoria = fields.Many2one('product.category',u'Categoría')
	almacen = fields.Many2one('stock.location','Almacen')
	saldo = fields.Float('Stock Disponible',digits=(15,3))
	saldo_fisico = fields.Float('Stock Fisico',digits=(15,3))
	por_ingresar = fields.Float('Por Ingresar',digits=(15,3))
	transito = fields.Float('Ingresos Transito',digits=(15,3))
	salida_espera = fields.Float('Salida Espera',digits=(15,3))
	reservas = fields.Float('Reservas',digits=(15,3))
	saldo_virtual = fields.Float('Previsto',digits=(15,3))

	id_stock_disponible = fields.Text('ids')
	id_saldo_fisico = fields.Text('ids')
	id_por_ingresar = fields.Text('ids')
	id_transito = fields.Text('ids')
	id_salida_espera = fields.Text('ids')
	id_reservas = fields.Text('ids')
	id_previsto = fields.Text('ids')



	@api.multi
	def get_stock_disponible(self):
		t = eval(self.id_stock_disponible.replace('None','0').replace('NULL','0'))
		elem = []
		for i in t:
			if i!= 0:
				data = {
					'move_id': i,
				}
				tmp = self.env['detalle.saldo.fisico'].create(data)
				elem.append(tmp.id)

		return {
			'domain' : [('id','in',elem)],
			'type': 'ir.actions.act_window',
			'res_model': 'detalle.saldo.fisico',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
			'target': 'new',
		}


	@api.multi
	def get_saldo_fisico(self):
		t = eval(self.id_saldo_fisico.replace('None','0').replace('NULL','0'))
		elem = []
		for i in t:
			if i!= 0:
				data = {
					'move_id': i,
				}
				tmp = self.env['detalle.saldo.fisico'].create(data)
				elem.append(tmp.id)

		return {
			'domain' : [('id','in',elem)],
			'type': 'ir.actions.act_window',
			'res_model': 'detalle.saldo.fisico',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
			'target': 'new',
		}

	@api.multi
	def get_por_ingresar(self):
		t = eval(self.id_por_ingresar.replace('None','0').replace('NULL','0'))
		elem = []
		for i in t:
			if i!= 0:
				data = {
					'move_id': i,
				}
				tmp = self.env['detalle.saldo.fisico'].create(data)
				elem.append(tmp.id)

		return {
			'domain' : [('id','in',elem)],
			'type': 'ir.actions.act_window',
			'res_model': 'detalle.saldo.fisico',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
			'target': 'new',
		}

	@api.multi
	def get_transito(self):
		t = eval(self.id_transito.replace('None','0').replace('NULL','0'))
		elem = []
		for i in t:
			if i!= 0:
				data = {
					'move_id': i,
				}
				tmp = self.env['detalle.saldo.fisico'].create(data)
				elem.append(tmp.id)

		return {
			'domain' : [('id','in',elem)],
			'type': 'ir.actions.act_window',
			'res_model': 'detalle.saldo.fisico',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
			'target': 'new',
		}

	@api.multi
	def get_salida_espera(self):
		t = eval(self.id_salida_espera.replace('None','0').replace('NULL','0'))
		elem = []
		for i in t:
			if i!= 0:
				data = {
					'move_id': i,
				}
				tmp = self.env['detalle.saldo.fisico'].create(data)
				elem.append(tmp.id)

		return {
			'domain' : [('id','in',elem)],
			'type': 'ir.actions.act_window',
			'res_model': 'detalle.saldo.fisico',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
			'target': 'new',
		}

	@api.multi
	def get_reservas(self):
		t = eval(self.id_reservas.replace('None','0').replace('NULL','0'))
		elem = []
		for i in t:
			if i!= 0:
				data = {
					'move_id': i,
				}
				tmp = self.env['detalle.saldo.fisico'].create(data)
				elem.append(tmp.id)

		return {
			'domain' : [('id','in',elem)],
			'type': 'ir.actions.act_window',
			'res_model': 'detalle.saldo.fisico',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
			'target': 'new',
		}

	@api.multi
	def get_saldo_virtual(self):
		t = eval(self.id_previsto.replace('None','0').replace('NULL','0'))
		elem = []
		for i in t:
			if i!= 0:
				data = {
					'move_id': i,
				}
				tmp = self.env['detalle.saldo.fisico'].create(data)
				elem.append(tmp.id)

		return {
			'domain' : [('id','in',elem)],
			'type': 'ir.actions.act_window',
			'res_model': 'detalle.saldo.fisico',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
			'target': 'new',
		}




	lote = fields.Many2one('stock.production.lot','lote')

	_order = 'producto,lote,categoria,almacen'
	_auto = False
