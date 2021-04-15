# -*- coding: utf-8 -*-
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import time
import odoo.addons.decimal_precision as dp
from openerp.osv import osv
import base64
from odoo import models, fields, api
import codecs
from odoo.exceptions import UserError

class MakeKardexAccountWizard(models.TransientModel):
	_name = "make.kardex.acount.wizard"

	period_id = fields.Many2one('account.period','Periodo')
	fini= fields.Date('Fecha inicial',required=True)
	ffin= fields.Date('Fecha final',required=True)
	products_ids=fields.Many2many('product.product','rel_wiz_kardex_comparation','product_id','kardex_id')
	location_ids=fields.Many2many('stock.location','rel_kardex_location_comparation','location_id','kardex_id','Ubicacion',required=True)
	allproducts=fields.Boolean('Todos los productos',default=True)
	destino = fields.Selection([('csv','CSV'),('crt','Pantalla')],'Destino')
	check_fecha = fields.Boolean('Editar Fecha')
	alllocations = fields.Boolean('Todos los almacenes',default=True)
	fecha_ini_mod = fields.Date('Fecha Inicial')
	fecha_fin_mod = fields.Date('Fecha Final')
	analizador = fields.Boolean('Analizador',compute="get_analizador")

	@api.multi
	def get_analizador(self):
		if 'tipo' in self.env.context:
			if self.env.context['tipo'] == 'valorado':
				self.analizador = True
			else:
				self.analizador = False
		else:
			self.analizador = False

	_defaults={
		'destino':'crt',
		'check_fecha': False,
		'allproducts': True,
		'alllocations': True,
	}

	@api.onchange('fecha_ini_mod')
	def onchange_fecha_ini_mod(self):
		self.fini = self.fecha_ini_mod

	@api.onchange('fecha_fin_mod')
	def onchange_fecha_fin_mod(self):
		self.ffin = self.fecha_fin_mod

	@api.model
	def default_get(self, fields):
		res = super(MakeKardexAccountWizard, self).default_get(fields)
		import datetime
		fecha_hoy = str(datetime.datetime.now())[:10]
		fecha_inicial = fecha_hoy[:4] + '-01-01'
		res.update({'fecha_ini_mod':fecha_inicial})
		res.update({'fecha_fin_mod':fecha_hoy})
		res.update({'fini':fecha_inicial})
		res.update({'ffin':fecha_hoy})

		#locat_ids = self.pool.get('stock.location').search(cr, uid, [('usage','in',('internal','inventory','transit','procurement','production'))])
		locat_ids = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])
		locat_ids = [elemt.id for elemt in locat_ids]
		res.update({'location_ids':[(6,0,locat_ids)]})
		return res

	@api.onchange('alllocations')
	def onchange_alllocations(self):
		if self.alllocations == True:
			locat_ids = self.env['stock.location'].search( [('usage','in',('internal','inventory','transit','procurement','production'))] )
			self.location_ids = [(6,0,locat_ids.ids)]
		else:
			self.location_ids = [(6,0,[])]

	@api.onchange('period_id')
	def onchange_period_id(self):
		self.fini = self.period_id.date_start
		self.ffin = self.period_id.date_stop

	@api.multi
	def do_csvtoexcel(self):
		cad = ""

		s_prod = [-1,-1,-1]
		s_loca = [-1,-1,-1]
		if self.alllocations == True:
			locat_ids = self.env['stock.location'].search( [('usage','in',('internal','inventory','transit','procurement','production'))] )
			lst_locations = locat_ids.ids
		else:
			lst_locations = self.location_ids.ids
		lst_products  = self.products_ids.ids
		productos='{'
		almacenes='{'
		date_ini=self.fini
		date_fin=self.ffin
		if self.allproducts:
			lst_products = self.env['product.product'].with_context(active_test=False).search([]).ids
		else:
			lst_products = self.products_ids.ids
		if len(lst_products) == 0:
			raise osv.except_osv('Alerta','No existen productos seleccionados')

		for producto in lst_products:
			productos=productos+str(producto)+','
			s_prod.append(producto)
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
			s_loca.append(location)
		almacenes=almacenes[:-1]+'}'

		import io
		from xlsxwriter.workbook import Workbook

		def set_format(workbook):
			boldbord = workbook.add_format({'bold': True})
			boldbord.set_border(style=2)
			boldbord.set_align('center')
			boldbord.set_align('vcenter')
			boldbord.set_text_wrap()
			boldbord.set_font_size(10)
			boldbord.set_bg_color('#DCE6F1')
			boldbord.set_font_name('Times New Roman')

			especial1 = workbook.add_format()
			especial1.set_align('center')
			especial1.set_align('vcenter')
			especial1.set_border(style=1)
			especial1.set_text_wrap()
			especial1.set_font_size(10)
			especial1.set_font_name('Times New Roman')

			especial3 = workbook.add_format({'bold': True})
			especial3.set_align('center')
			especial3.set_align('vcenter')
			especial3.set_border(style=1)
			especial3.set_text_wrap()
			especial3.set_bg_color('#DCE6F1')
			especial3.set_font_size(15)
			especial3.set_font_name('Times New Roman')

			numberdos = workbook.add_format({'num_format':'0.00'})
			numberdos.set_border(style=1)
			numberdos.set_font_size(10)
			numberdos.set_font_name('Times New Roman')

			dateformat = workbook.add_format({'num_format':'d-m-yyyy'})
			dateformat.set_border(style=1)
			dateformat.set_font_size(10)
			dateformat.set_font_name('Times New Roman')

			hourformat = workbook.add_format({'num_format':'hh:mm'})
			hourformat.set_align('center')
			hourformat.set_align('vcenter')
			hourformat.set_border(style=1)
			hourformat.set_font_size(10)
			hourformat.set_font_name('Times New Roman')
			return boldbord,especial1,especial3,numberdos,dateformat,hourformat

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		workbook = Workbook(direccion +'account_balance.xlsx')
		boldbord,especial1,especial3,numberdos,dateformat,hourformat = set_format(workbook)
		yellow = workbook.add_format()
		yellow.set_align('center')
		yellow.set_align('vcenter')
		yellow.set_border(style=1)
		yellow.set_text_wrap()
		yellow.set_bg_color('#FFFF00')
		yellow.set_font_size(10)
		yellow.set_font_name('Times New Roman')
		numberyellow = workbook.add_format({'num_format':'0.00'})
		numberyellow.set_border(style=1)
		numberyellow.set_font_size(10)
		numberyellow.set_bg_color('#FFFF00')
		numberyellow.set_font_name('Times New Roman')
		worksheet = workbook.add_worksheet("SALDOS")
		worksheet.set_tab_color('blue')
		self.env.cr.execute("""
			select 
			T.almacen,
			T.code,
			T.name,
			T.ingreso,
			T.salida,
			T.debe,
			T.haber,
			(T.ingreso - T.salida) as saldo_fisico,
			(T.debe - T.haber) as saldo_valorado,
			case when (T.ingreso - T.salida) = 0 then 0 else (T.debe - T.haber)/(T.ingreso - T.salida) end as costo_unitario 
			from (
				select
				min(get_kardex_v.almacen) as almacen,
				min(coalesce(product_product.default_code,product_template.default_code)) as code,
				min(get_kardex_v.name_template) as name,
				sum(get_kardex_v.ingreso) as ingreso,
				sum(get_kardex_v.salida) as salida,
				sum(get_kardex_v.debit) as debe,
				sum(get_kardex_v.credit) as haber
				from get_kardex_v("""+ str(date_ini).replace('-','') + "," + str(date_fin).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[])
				left join stock_move on get_kardex_v.stock_moveid = stock_move.id
				left join product_product on product_product.id = stock_move.product_id
				left join product_template on product_template.id = product_product.product_tmpl_id
				left join stock_picking on stock_move.picking_id = stock_picking.id
				group by get_kardex_v.almacen ||'-'|| coalesce(product_product.default_code,product_template.default_code)
			)T
			where (T.ingreso - T.salida) >= 0
		""")
		result = self.env.cr.dictfetchall()
		x = 0
		worksheet.write(x,0,"Almacen",boldbord)
		worksheet.write(x,1,"Codigo P.",boldbord)
		worksheet.write(x,2,"Producto",boldbord)
		worksheet.write(x,3,"Ingreso",boldbord)
		worksheet.write(x,4,"Salida",boldbord)
		worksheet.write(x,5,"Debe",boldbord)
		worksheet.write(x,6,"Haber",boldbord)
		worksheet.write(x,7,"Saldo Fisico",boldbord)
		worksheet.write(x,8,"Saldo Valorado",boldbord)
		worksheet.write(x,9,"Costo Unitario",boldbord)
		x=1
		for line in result:	
			worksheet.write(x,0,line['almacen'] if line['almacen'] else '',yellow)
			worksheet.write(x,1,line['code'] if line['code'] else '',yellow)
			worksheet.write(x,2,line['name'] if line['name'] else '',especial1)
			worksheet.write(x,3,line['ingreso'] if line['ingreso'] else 0,numberdos)
			worksheet.write(x,4,line['salida'] if line['salida'] else 0,numberdos)
			worksheet.write(x,5,line['debe'] if line['debe'] else 0,numberdos)
			worksheet.write(x,6,line['haber'] if line['haber'] else 0,numberdos)
			worksheet.write(x,7,line['saldo_fisico'] if line['saldo_fisico'] else 0,numberyellow)
			worksheet.write(x,8,line['saldo_valorado'] if line['saldo_valorado'] else 0,numberdos)
			worksheet.write(x,9,line['costo_unitario'] if line['costo_unitario'] else 0,numberyellow)
			x += 1
		tam_col = [30,15,40,10,10,10,10,10,10,10]
		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])
		worksheet.set_column('G:G', tam_col[6])
		worksheet.set_column('H:H', tam_col[7])
		worksheet.set_column('I:I', tam_col[8])
		worksheet.set_column('J:J', tam_col[9])
		f = open(direccion + 'account_balance.xlsx', 'rb')
		vals = {
			'output_name': 'Reporte de Saldos.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),
		}
		sfs_id = self.env['custom.export.file'].create(vals)

		return {
			"type": "ir.actions.act_window",
			"res_model": "custom.export.file",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

	@api.multi
	def do_csv(self):
		cad = ""

		s_prod = [-1,-1,-1]
		s_loca = [-1,-1,-1]
		if self.alllocations == True:
			locat_ids = self.env['stock.location'].search( [('usage','in',('internal','inventory','transit','procurement','production'))] )
			lst_locations = locat_ids.ids
		else:
			lst_locations = self.location_ids.ids
		lst_products  = self.products_ids.ids
		productos='{'
		almacenes='{'
		date_ini=self.fini
		date_fin=self.ffin
		if self.allproducts:
			lst_products = self.env['product.product'].with_context(active_test=False).search([]).ids
		else:
			lst_products = self.products_ids.ids
		if len(lst_products) == 0:
			raise osv.except_osv('Alerta','No existen productos seleccionados')

		for producto in lst_products:
			productos=productos+str(producto)+','
			s_prod.append(producto)
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
			s_loca.append(location)
		almacenes=almacenes[:-1]+'}'
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		self.env.cr.execute("""
				COPY (
					select 
					T.almacen,
					T.code,
					round((T.ingreso - T.salida),2) as saldo_fisico,
					round(case when (T.ingreso - T.salida) = 0 then 0 else (T.debe - T.haber)/(T.ingreso - T.salida) end ,6) as costo_unitario,
					T.name 
					from (
						select
						min(get_kardex_v.almacen) as almacen,
						min(coalesce(product_product.default_code,product_template.default_code)) as code,
						min(product_product.campo_name_get) as name,
						sum(get_kardex_v.ingreso) as ingreso,
						sum(get_kardex_v.salida) as salida,
						sum(get_kardex_v.debit) as debe,
						sum(get_kardex_v.credit) as haber
						from get_kardex_v("""+ str(date_ini).replace('-','') + "," + str(date_fin).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[])
						left join stock_move on get_kardex_v.stock_moveid = stock_move.id
						left join product_product on product_product.id = stock_move.product_id
						left join product_template on product_template.id = product_product.product_tmpl_id
						left join stock_picking on stock_move.picking_id = stock_picking.id
						group by get_kardex_v.almacen ||'-'|| coalesce(product_product.default_code,product_template.default_code)
					)T
					where (T.ingreso - T.salida) >= 0
				) TO '"""+ direccion+ """account_balance.csv' DELIMITER '|' CSV""")

		f = open(direccion + 'account_balance.csv', 'rb')
		vals = {
			'output_name': 'Reporte de Saldos.csv',
			'output_file': base64.encodestring(''.join(f.readlines())),
		}
		sfs_id = self.env['custom.export.file'].create(vals)

		return {
			"type": "ir.actions.act_window",
			"res_model": "custom.export.file",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

	@api.multi
	def do_csv_by_ids(self):
		cad = ""

		s_prod = [-1,-1,-1]
		s_loca = [-1,-1,-1]
		if self.alllocations == True:
			locat_ids = self.env['stock.location'].search( [('usage','in',('internal','inventory','transit','procurement','production'))] )
			lst_locations = locat_ids.ids
		else:
			lst_locations = self.location_ids.ids
		lst_products  = self.products_ids.ids
		productos='{'
		almacenes='{'
		date_ini=self.fini
		date_fin=self.ffin
		if self.allproducts:
			lst_products = self.env['product.product'].with_context(active_test=False).search([]).ids
		else:
			lst_products = self.products_ids.ids
		if len(lst_products) == 0:
			raise osv.except_osv('Alerta','No existen productos seleccionados')

		for producto in lst_products:
			productos=productos+str(producto)+','
			s_prod.append(producto)
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
			s_loca.append(location)
		almacenes=almacenes[:-1]+'}'
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		self.env.cr.execute("""
				COPY (
					select 
					T.almacen,
					T.code,
					round((T.ingreso - T.salida),2) as saldo_fisico,
					round(case when (T.ingreso - T.salida) = 0 then 0 else (T.debe - T.haber)/(T.ingreso - T.salida) end ,6) as costo_unitario,
					T.name,
					T.pp_id,
					T.pt_id
					from (
						select
						min(get_kardex_v.almacen) as almacen,
						min(coalesce(product_product.default_code,product_template.default_code)) as code,
						min(product_product.campo_name_get) as name,
						sum(get_kardex_v.ingreso) as ingreso,
						sum(get_kardex_v.salida) as salida,
						sum(get_kardex_v.debit) as debe,
						sum(get_kardex_v.credit) as haber,
						min(product_product.id) as pp_id,
						min(product_template.id) as pt_id
						from get_kardex_v("""+ str(date_ini).replace('-','') + "," + str(date_fin).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[])
						left join stock_move on get_kardex_v.stock_moveid = stock_move.id
						left join product_product on product_product.id = stock_move.product_id
						left join product_template on product_template.id = product_product.product_tmpl_id
						left join stock_picking on stock_move.picking_id = stock_picking.id
						group by get_kardex_v.almacen ||'-'|| coalesce(product_product.default_code,product_template.default_code)
					)T
					where (T.ingreso - T.salida) >= 0
				) TO '"""+ direccion+ """account_balance.csv' DELIMITER '|' CSV""")

		f = open(direccion + 'account_balance.csv', 'rb')
		vals = {
			'output_name': 'Reporte de Saldos.csv',
			'output_file': base64.encodestring(''.join(f.readlines())),
		}
		sfs_id = self.env['custom.export.file'].create(vals)

		return {
			"type": "ir.actions.act_window",
			"res_model": "custom.export.file",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}