# -*- coding: utf-8 -*-
# Copyright 2015 Guewen Baconnier <guewen.baconnier@camptocamp.com>
# Copyright 2016 Vicent Cubells <vicent.cubells@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
import datetime
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_utils

class Inventory(models.Model):

	_inherit = "stock.inventory"

	picking_id = fields.Many2one('stock.picking','Tranferencia Interna Salida')
	picking_in_id = fields.Many2one('stock.picking','Tranferencia Interna Ingreso')

	picking_type_id = fields.Many2one('stock.picking.type','Tipo de Transferencia Salida')
	picking_type_in_id = fields.Many2one('stock.picking.type','Tipo de Transferencia Entrada')

	picking_motive_id = fields.Many2one('einvoice.catalog.12','Motivo del Inventario')
	
	picking_in_ids = fields.One2many('stock.inventory.picking.in.link','main_id','Albaranes de Entrada')
	picking_out_ids = fields.One2many('stock.inventory.picking.out.link','main_id','Albaranes de Salida')
	fiscalyear_id = fields.Many2one('account.fiscalyear', u'Saldos al Año:', required=True)

	@api.model
	def default_get(self, default_fields):
		rec = super(Inventory, self).default_get(default_fields)
		a_config_vals = self.env["stock.inventory.config"].search([])
		if len(a_config_vals)<1:
			raise ValidationError(u"No se han ingresado los valores de configuración")
		config_vals= a_config_vals[0]
		rec.update({
			'picking_type_id':config_vals.picking_type_id.id,
			'picking_type_in_id':config_vals.picking_type_in_id.id,
			'picking_motive_id':config_vals.picking_motive_id.id,
			})
		return rec
		
	# @api.multi
	# def post_inventory(self):
		# # The inventory is posted as a single step which means quants cannot be moved from an internal location to another using an inventory
		# # as they will be moved to inventory loss, and other quants will be created to the encoded quant location. This is a normal behavior
		# # as quants cannot be reuse from inventory location (users can still manually move the products before/after the inventory if they want).
		# super(Inventory,self).post_inventory()
		# for act in self:
			# if len(act.move_ids)>0:
				# print len(act.move_ids)
				# input('aaaaa')
				# if not self.picking_type_id.default_location_src_id:
					# raise ValidationError(u"El Tipo de Transferecia seleccionada no tiene un almacèn de origen por defecto")
				# picking = self.env['stock.picking']
				# vals_picking= {
					# 'picking_type_id': self.picking_type_id.id,
					# 'partner_id': False,
					# 'date': self.date,
					# 'min_date':self.accounting_date,
					# 'origin': self.name,
					# 'location_dest_id': self.location_id.id,
					# 'location_id':self.picking_type_id.default_location_src_id.id,
					# 'company_id': self.company_id.id,
					# 'fecha_kardex':self.accounting_date,
					# 'name':self.picking_type_id.sequence_id._next(),
				# }
				# newpicking = picking.create(vals_picking)			
				# act.picking_id=newpicking.id


				# vals_picking= {
					# 'picking_type_id': self.picking_type_in_id.id,
					# 'partner_id': False,
					# 'date': self.date,
					# 'min_date':self.accounting_date,
					# 'origin': self.name ,
					# 'location_dest_id': self.picking_type_in_id.default_location_dest_id.id,
					# 'location_id':self.location_id.id,
					# 'company_id': self.company_id.id,
					# 'fecha_kardex':self.accounting_date,
					# 'name':self.picking_type_in_id.sequence_id._next(),
				# }
				# newpickingin = picking.create(vals_picking)			
				# act.picking_in_id=newpickingin.id

				# for moveact in act.move_ids:
					# if moveact.location_id.id == self.location_id.id:
						# moveact.picking_id = newpickingin.id
					# else:
						# moveact.picking_id = newpicking.id		
		
	
	
	@api.multi
	def post_inventory(self):
		
		super(Inventory,self).post_inventory()
		a_config_vals = self.env["stock.inventory.config"].search([])
		if len(a_config_vals)<1:
			raise ValidationError(u"No se han ingresado los valores de configuración")
		config_vals= a_config_vals[0]
		max_lines = config_vals.limit_detail_picking 
		n=max_lines
		cadsql =""
		id_picking=False
		in_lines = []
		out_lines = []
		partner = 1
		if self.location_id.company_id.partner_id:
			partner = self.location_id.company_id.partner_id.id
		print 1
		for line in self.line_ids:
		
			if float_utils.float_compare(line.theoretical_qty, line.product_qty, precision_rounding=line.product_id.uom_id.rounding) == 0:
				continue
			diff = line.theoretical_qty - line.product_qty
			if diff<0:
				in_lines.append(line)
			else:
				out_lines.append(line)
		print 2,n, max_lines
		for line in in_lines:
			if n==max_lines:
				cadsql="""select * from make_stock_picking("""
				cadsql=cadsql+str(self.picking_type_in_id.id)+""","""
				cadsql=cadsql+str(partner)+""",'"""
				cadsql=cadsql+str(self.date)+"""'::date,'"""
				cadsql=cadsql+self.date+"""'::date,'"""
				cadsql=cadsql+self.name+"""'::character varying,"""
				cadsql=cadsql+str(self.picking_type_in_id.default_location_dest_id.id)+""","""
				cadsql=cadsql+str(self.picking_type_in_id.default_location_src_id.id)+""","""
				cadsql=cadsql+str(self.company_id.id)+""",'"""
				cadsql=cadsql+self.date+"""'::date,'"""
				cadsql=cadsql+self.picking_type_in_id.sequence_id._next()+"""'::character varying,"""
				cadsql=cadsql+str(self.picking_motive_id.id)+""",'draft'::character varying);"""
				# raise ValidationError(cadsql)
				self.env.cr.execute(cadsql)
				data1=self.env.cr.fetchall()
				id_picking = data1[0][0]
				self.env['stock.inventory.picking.in.link'].create({
						'main_id':self.id,
						'picking_id':id_picking
						})
				n=0
			
			diff = line.theoretical_qty - line.product_qty
			qty=abs(diff)
			location=self.picking_type_in_id.default_location_src_id.id
			location_dest=self.picking_type_in_id.default_location_dest_id.id	
			cadsql = """select * from make_stock_move('"""
			cadsql=cadsql+_('INV:') + (self.name or '')+"""'::character varying,"""
			cadsql=cadsql+str(line.product_id.id)+""","""
			cadsql=cadsql+str(line.product_uom_id.id)+""","""
			cadsql=cadsql+str(qty)+""",'"""
			cadsql=cadsql+self.date+"""'::date,"""
			cadsql=cadsql+str(self.company_id.id)+""","""
			cadsql=cadsql+str(self.id)+""",'"""
			cadsql=cadsql+'confirmed'+"""'::character varying,"""
			cadsql=cadsql+str(line.prod_lot_id.id) if line.prod_lot_id.id else cadsql+'null'+""","""
			cadsql=cadsql+str(line.partner_id.id) if line.partner_id.id else cadsql+'null'+""","""
			cadsql=cadsql+str(location)+""","""
			cadsql=cadsql+str(location_dest)+""","""
			cadsql=cadsql+str(id_picking)+""","""
			cadsql=cadsql+"""null,null);"""
			# raise ValidationError(cadsql)
			self.env.cr.execute(cadsql)
			n=n+1
		print 3
		n=max_lines
		for line in out_lines:
			if n==max_lines:
				cadsql="""select * from make_stock_picking("""
				cadsql=cadsql+str(self.picking_type_id.id)+""","""
				cadsql=cadsql+str(partner)+""",'"""
				cadsql=cadsql+str(self.date)+"""'::date,'"""
				cadsql=cadsql+self.date+"""'::date,'"""
				cadsql=cadsql+self.name+"""'::character varying,"""
				cadsql=cadsql+str(self.picking_type_id.default_location_dest_id.id)+""","""
				cadsql=cadsql+str(self.picking_type_id.default_location_src_id.id)+""","""
				cadsql=cadsql+str(self.company_id.id)+""",'"""
				cadsql=cadsql+self.date+"""'::date,'"""
				cadsql=cadsql+self.picking_type_id.sequence_id._next()+"""'::character varying,"""
				cadsql=cadsql+str(self.picking_motive_id.id)+""",'draft'::character varying);"""
				self.env.cr.execute(cadsql)
				id_picking = self.env.cr.fetchall()[0][0]
				self.env['stock.inventory.picking.out.link'].create({
						'main_id':self.id,
						'picking_id':id_picking
						})
				n=0
			
			diff = line.theoretical_qty - line.product_qty
			qty=abs(diff)
			location=self.picking_type_id.default_location_src_id.id
			location_dest=self.picking_type_id.default_location_dest_id.id	
			cadsql = """select * from make_stock_move('"""
			cadsql=cadsql+_('INV:') + (self.name or '')+"""'::character varying,"""
			cadsql=cadsql+str(line.product_id.id)+""","""
			cadsql=cadsql+str(line.product_uom_id.id)+""","""
			cadsql=cadsql+str(qty)+""",'"""
			cadsql=cadsql+self.date+"""'::date,"""
			cadsql=cadsql+str(self.company_id.id)+""","""
			cadsql=cadsql+str(self.id)+""",'"""
			cadsql=cadsql+'confirmed'+"""'::character varying,"""
			cadsql=cadsql+str(line.prod_lot_id.id) if line.prod_lot_id.id else cadsql+'null'+""","""
			cadsql=cadsql+str(line.partner_id.id) if line.partner_id.id else cadsql+'null'+""","""
			cadsql=cadsql+str(location)+""","""
			cadsql=cadsql+str(location_dest)+""","""
			cadsql=cadsql+str(id_picking)+""","""
			cadsql=cadsql+"""null,null);"""
			self.env.cr.execute(cadsql)
			n=n+1
		
		
		
		
			
		# nin=0
		# nout=0
		# for act in self:
			# print len(act.move_ids)
			# for moveact in act.move_ids:
				# if moveact.location_id.id == self.location_id.id:
					# nin=nin+1
				# else:
					# nout=nout+1
		# print nin,nout
		# maxpickin=nin//max_lines
		# if nin % max_lines>0:
			# maxpickin=maxpickin+1
		# maxpickout=nout//max_lines
		# if nout % max_lines>0:
			# maxpickout=maxpickout+1
			
		# print maxpickin,maxpickout
		
		# apick_in = []
		# apick_out = []
		# for act in self:
			# if len(act.move_ids)>0:
				# if not self.picking_type_id.default_location_src_id:
					# raise ValidationError(u"El Tipo de Transferecia seleccionada no tiene un almacèn de origen por defecto")
				# picking = self.env['stock.picking']
				# # salidas
				# for i in range(0,maxpickout):
					# vals_picking= {
						# 'picking_type_id': self.picking_type_id.id,
						# 'partner_id': False,
						# 'date': self.date,
						# 'min_date':self.accounting_date,
						# 'origin': self.name,
						# 'location_dest_id': self.picking_type_id.default_location_src_id.id,
						# 'location_id':self.location_id.id,
						# 'company_id': self.company_id.id,
						# 'fecha_kardex':self.accounting_date,
						# 'name':self.picking_type_id.sequence_id._next(),
						# 'einvoice12':self.picking_motive_id.id,
					# }
					# newpicking = picking.create(vals_picking)
					# apick_out.append(newpicking.id)
					# self.env['stock.inventory.picking.out.link'].create({
						# 'main_id':act.id,
						# 'picking_id':newpicking.id
						# })
					
				
				# # act.picking_id=newpicking.id
				# #ingresos
				# for i in range(0,maxpickin):
					# vals_picking= {
						# 'picking_type_id': self.picking_type_in_id.id,
						# 'partner_id': False,
						# 'date': self.date,
						# 'min_date':self.accounting_date,
						# 'origin': self.name ,
						# 'location_dest_id': self.picking_type_in_id.default_location_dest_id.id,
						# 'location_id':self.location_id.id,
						# 'company_id': self.company_id.id,
						# 'fecha_kardex':self.accounting_date,
						# 'name':self.picking_type_in_id.sequence_id._next(),
						# 'einvoice12':self.picking_motive_id.id,
					# }
					# newpickingin = picking.create(vals_picking)			
					# apick_in.append(newpickingin.id)
					# self.env['stock.inventory.picking.in.link'].create({
						# 'main_id':act.id,
						# 'picking_id':newpickingin.id
						# })

					
					
					
				

					# act.picking_in_id=newpickingin.id
				# n=0
				# posl = 0
				# # print apick_in,apick_out
				# # input('aaaaaaa')
				# for moveact in act.move_ids:
					# # inrgesos
					# if moveact.location_id.id == self.location_id.id:
						# moveact.picking_id = apick_in[posl]
						# n=n+1	
						# if n>=max_lines:
							# posl=posl+1
							# n=0
					
				# n=0
				# posl = 0
				# for moveact in act.move_ids:
					# # salidas
					# if moveact.location_id.id != self.location_id.id:
						# moveact.picking_id = apick_out[posl]
						# n=n+1
						# if n>=max_lines:
							# posl=posl+1		
							# n=0
	@api.multi
	def validacion_pickings(self):
		if self.picking_in_ids:
			for in_picking in self.picking_in_ids:
				in_picking.picking_id.action_confirm()
				in_picking.picking_id.force_assign()
				in_picking.picking_id.do_transfer()
		
		if self.picking_out_ids:
			print('Llego a ppickings de salida')
			for out_picking in self.picking_out_ids:
				out_picking.picking_id.action_confirm()
				out_picking.picking_id.force_assign()
				out_picking.picking_id.do_transfer()
				
	@api.multi
	def action_done(self):
		t = super(Inventory,self).action_done()
		self.validacion_pickings()
		return t
		
		

	@api.multi
	def _get_inventory_lines_values(self):	
		# TDE CLEANME: is sql really necessary ? I don't think so
		locations = self.env['stock.location'].search([('id', 'child_of', [self.location_id.id])])
		s=""
		for l in locations.ids:
			s=s+str(l)+","
		s=s[:-1]
		domain = ' AND ubicacion in ('+s+')'
		

		
		Product = self.env['product.product']
		# Empty recordset of products available in stock_quants
		quant_products = self.env['product.product']
		# Empty recordset of products to filter
		products_to_filter = self.env['product.product']

		# case 0: Filter on company
		if self.company_id:
			domain += ' AND pt.company_id = '+str(self.company_id.id)
			
		
		#case 1: Filter on One owner only or One product for a specific owner
		if self.partner_id:
			domain += ' AND pt.owner_id = '+str(self.partner_id.id)
			
		#case 2: Filter on One Lot/Serial Number
		# NOTA PARA ITGRUPO: NO SE PUEDE SACAR POR LOTES YA QUE EL REPORTE DE SALDOS NO FUNCIONA CON LOTES
		# if self.lot_id:
		#	domain += ' AND lot_id = '+str(self.lot_id.id)
		
		#case 3: Filter on One product
		if self.product_id:
			domain += ' AND product_id = '+str(self.product_id.id)
			products_to_filter |= self.product_id
		#case 4: Filter on A Pack
		# NOTA PARA ITGRUPO: NO SE PUEDE SACAR POR PAQUETES YA QUE EL REPORTE DE SALDOS NO FUNCIONA CON PAQUETES
		# if self.package_id:
		#	domain += ' AND package_id = '
		#	args += (self.package_id.id,)
		
		#case 5: Filter on One product category + Exahausted Products
		if self.category_id:
			categ_products = Product.search([('categ_id', '=', self.category_id.id)])
			if len(categ_products)==0:
				raise ValidationError(u"No existen productos en la categoría seleccionada")
			s=""
			for l in categ_products.ids:
				s=s+str(l)+","
			s=s[:-1]
			domain += ' AND product_id in ('+s+')'
			products_to_filter |= categ_products
		having=""
		if not self.exhausted:
			having = " HAVING sum(saldo_fisico)>0"
		
		self.env.cr.execute("""
			drop view if exists detalle_simple_fisico_total_d_ajustes;
			create view detalle_simple_fisico_total_d_ajustes as (
					select row_number() OVER () AS id,* from (
					select ubicacion as almacen, product_id as producto, pt.categ_id as categoria,
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
					replace(replace(array_agg(id_previsto)::text,'{','['),'}',']') as id_previsto,
					product_uom.id as uom_id

					from vst_kardex_onlyfisico_total
					inner join product_template pt on pt.id = product_tmpl_id
					inner join product_uom on pt.uom_id = product_uom.id
					where vst_kardex_onlyfisico_total.date >= '"""+str(self.fiscalyear_id.name)+"""-01-01'
					and vst_kardex_onlyfisico_total.date <= '"""+str(self.fiscalyear_id.name)+"""-12-31' """
					+domain+"""
					group by ubicacion, product_id, pt.categ_id,product_uom.id""" 
					+having+""" 
					order by ubicacion,product_id, pt.categ_id
					) Todo


			);
			""")
		
		self.env.cr.execute("""select * from detalle_simple_fisico_total_d_ajustes""")
		vals = []
		for line in self.env.cr.dictfetchall():
			l = {
					'product_id':line['producto'],
					'theorical_qty':line['saldo_fisico'],
					'location_id': line['almacen'],
					'prod_lot_id':False,
					'package_id':False,
					'product_qty':line['saldo_fisico'],
					'product_uom_id':line['uom_id'],
					'partner_id':False
				}
			vals.append(l)
		return vals
class InventoryLine(models.Model):
	_inherit = "stock.inventory.line"		
	
	
	def _generate_moves(self):
		return False

	@api.one
	@api.depends('location_id', 'product_id', 'package_id', 'product_uom_id', 'company_id', 'prod_lot_id', 'partner_id')
	def _compute_theoretical_qty(self):
		if not self.product_id:
			self.theoretical_qty = 0
			return
		self.env.cr.execute("""
			drop view if exists detalle_simple_fisico_total_d_ajustes;
			create view detalle_simple_fisico_total_d_ajustes as (
					select row_number() OVER () AS id,* from (
					select ubicacion as almacen, product_id as producto, pt.categ_id as categoria,
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
					replace(replace(array_agg(id_previsto)::text,'{','['),'}',']') as id_previsto,
					product_uom.id as uom_id

					from vst_kardex_onlyfisico_total
					inner join product_template pt on pt.id = product_tmpl_id
					inner join product_uom on pt.uom_id = product_uom.id
					where vst_kardex_onlyfisico_total.date >= '"""+str(self.inventory_id.fiscalyear_id.name)+"""-01-01'
					and vst_kardex_onlyfisico_total.date <= '"""+str(self.inventory_id.fiscalyear_id.name)+"""-12-31'
					and ubicacion ="""+str(self.inventory_id.location_id.id)+""" 
					and product_id = """+str(self.product_id.id)+""" 
					group by ubicacion, product_id, pt.categ_id,product_uom.id
					order by ubicacion,product_id, pt.categ_id
					) Todo


			);
			""")
		self.env.cr.execute("""select * from detalle_simple_fisico_total_d_ajustes""")
		data = self.env.cr.dictfetchall()
		if len(data)>0:
			self.theoretical_qty = data[0]['saldo_fisico']
		else:
			self.theoretical_qty = 0
		
		
						
class InventoryConfig(models.Model):
	_name="stock.inventory.config"
	
	name=fields.Char("Configuración")
	picking_type_id = fields.Many2one('stock.picking.type','Tipo de Transferencia Salida')
	picking_type_in_id = fields.Many2one('stock.picking.type','Tipo de Transferencia Entrada')
	picking_motive_id = fields.Many2one('einvoice.catalog.12','Motivo del Inventario')
	limit_detail_picking = fields.Integer(u'Máximo Nro. de filas por albarán')
	
class InventoryPickingInLink(models.Model):
	_name = 'stock.inventory.picking.in.link'
	
	main_id = fields.Many2one('stock.inventory','Main')
	picking_id = fields.Many2one('stock.picking','Movimiento de ingreso')

	
class InventoryPickingOutLink(models.Model):
	_name = 'stock.inventory.picking.out.link'
	
	main_id = fields.Many2one('stock.inventory','Main')
	picking_id = fields.Many2one('stock.picking','Movimiento de Salida')
