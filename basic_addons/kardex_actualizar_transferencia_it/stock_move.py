# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp import models,fields ,api


datos = []
llaves = {}

class valor_unitario_kardex(models.Model):
	_name='valor.unitario.kardex'
	
	fecha_inicio = fields.Date('Fecha Inicio')
	fecha_final = fields.Date('Fecha Final')
	product = fields.Many2one('product.product','Producto')

	@api.one
	def do_valor(self):
		prods = self.env['product.product'].browse(self.product.id)
		locat = self.env['stock.location'].search([('usage','in',['internal','inventory','transit','procurement','production'])])

		lst_products  = prods.ids
		lst_locations = locat.ids
		productos='{'
		almacenes='{'
		date_ini= self.fecha_inicio.split('-')[0] + '-01-01'
		date_fin= self.fecha_final
		fecha_arr = self.fecha_inicio
		for producto in lst_products:
			productos=productos+str(producto)+','
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
		almacenes=almacenes[:-1]+'}'

		self.env.cr.execute(""" 
			update stock_move set
price_unit = 0
where id in (
select sm.id from stock_move sm
inner join stock_location entrada on entrada.id = sm.location_id
inner join stock_location salida on salida.id = sm.location_dest_id
inner join stock_picking sp on sp.id = sm.picking_id
where entrada.usage = 'internal' and salida.usage = 'internal'
and sp.fecha_kardex >='""" +str(self.fecha_inicio)+ """' and sp.fecha_kardex <='""" +str(self.fecha_final)+ """' and sm.product_id = """ + str(self.product.id) + """
)
""")


		for m in self.env['stock.move'].search([('product_id','=',self.product.id),('location_id.usage','=','internal'),('location_dest_id.usage','=','internal'),('picking_id.fecha_kardex','>=',self.fecha_inicio),('picking_id.fecha_kardex','<=',self.fecha_final),('picking_id.state','=','done')]).sorted(key=lambda r: [r.picking_id.fecha_kardex,r.id]):
			self.env.cr.execute("""  
				drop table if exists tmp_kardexv_veloz;
				create table tmp_kardexv_veloz as 

			select vst_kardex_sunat.*,sp.name as doc_almac,sp.fecha_kardex::date as fecha_albaran, po.name as pedido_compra, pr.name as licitacion,spl.name as lote,
      ''::character varying as ruc,''::character varying as comapnyname, ''::character varying as cod_sunat,ipx.value_text as ipxvalue,
      ''::character varying as tipoprod ,''::character varying as coduni ,''::character varying as metodo, 0::numeric as cu_entrada , 0::numeric as cu_salida, ''::character varying as period_name , 0::integer as correlativovisual 
      from vst_kardex_fisico_valorado as vst_kardex_sunat
left join stock_move sm on sm.id = vst_kardex_sunat.stock_moveid
left join stock_production_lot spl on spl.id = sm.restrict_lot_id
left join stock_picking sp on sp.id = sm.picking_id
left join purchase_order po on po.id = sp.po_id
left join purchase_requisition pr on pr.id = po.requisition_id
left join account_invoice_line ail on ail.id = vst_kardex_sunat.invoicelineid
left join product_product pp on pp.id = vst_kardex_sunat.product_id
left join product_template ptp on ptp.id = pp.product_tmpl_id
LEFT JOIN ir_property ipx ON ipx.res_id::text = ('product.template,'::text || ptp.id) AND ipx.name::text = 'cost_method'::text 
          
       where (fecha_num(vst_kardex_sunat.fecha::date) between """+str(self.fecha_inicio).replace('-','')+""" and """+str(self.fecha_final).replace('-','')+""")    and (vst_kardex_sunat.product_id = """ +str(self.product.id)+ """) 
      order by vst_kardex_sunat.location_id,vst_kardex_sunat.product_id,vst_kardex_sunat.fecha,vst_kardex_sunat.esingreso,vst_kardex_sunat.stock_moveid,vst_kardex_sunat.nro
        	""")

			self.env.cr.execute(""" select * from get_kardex_v_actualizar_veloz("""+ date_ini.replace("-","") + "," + date_fin.replace("-","") + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[],""" +fecha_arr.replace('-','')+ ""","""+str(m.id)+""") """)
		return


	@api.one
	def do_valor_ex(self):
		prods = self.env['product.product'].browse(self.product.id)
		locat = self.env['stock.location'].search([('usage','in',['internal','inventory','transit','procurement','production'])])

		lst_products  = prods.ids
		lst_locations = locat.ids
		productos='{'
		almacenes='{'
		date_ini= self.fecha_inicio.split('-')[0] + '-01-01'
		date_fin= self.fecha_final
		fecha_arr = self.fecha_inicio
		for producto in lst_products:
			productos=productos+str(producto)+','
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
		almacenes=almacenes[:-1]+'}'

		self.env.cr.execute(""" 
			update stock_move set
price_unit = 0
where id in (
select sm.id from stock_move sm
inner join stock_location entrada on entrada.id = sm.location_id
inner join stock_location salida on salida.id = sm.location_dest_id
inner join stock_picking sp on sp.id = sm.picking_id
where entrada.usage = 'internal' and salida.usage = 'internal'
and sp.fecha_kardex >='""" +str(self.fecha_inicio)+ """' and sp.fecha_kardex <='""" +str(self.fecha_final)+ """' and sm.product_id = """ + str(self.product.id) + """
)
""")
		for m in self.env['stock.move'].search([('product_id','=',self.product.id),('location_id.usage','=','internal'),('location_dest_id.usage','=','internal'),('picking_id.fecha_kardex','>=',self.fecha_inicio),('picking_id.fecha_kardex','<=',self.fecha_final),('picking_id.state','=','done')]).sorted(key=lambda r: [r.picking_id.fecha_kardex,r.id]):
			self.env.cr.execute(""" select * from get_kardex_v_actualizar("""+ date_ini.replace("-","") + "," + date_fin.replace("-","") + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[],""" +fecha_arr.replace('-','')+ ""","""+str(m.id)+""") """)
		return
