# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _
import csv
from tempfile import TemporaryFile
from odoo.exceptions import UserError

class stock_quant(models.Model):
	_inherit = 'stock.quant'

	@api.multi
	def _get_latest_move(self):
		if len(self.history_ids)>0:	    		
			latest_move = self.history_ids[0]
			for move in self.history_ids:
				if move.date > latest_move.date:
					latest_move = move
			return latest_move

	@api.multi
	def _price_update(self, newprice):
		# TDE note: use ACLs instead of sudoing everything
		self.sudo().write({'cost': newprice})
		

class import_rest_inv1(models.Model):
	_name = 'import.rest.inv1'

	file_inv = fields.Binary('Archivo con saldos')
	location_id = fields.Many2one('stock.location',u'Almacén Origen')
	location_dest_id = fields.Many2one('stock.location',u'Almacén Destino')
	date_inv = fields.Date('fecha del inventario')
	picking_type_id = fields.Many2one('stock.picking.type','Tipo de Picking')
	lines = fields.One2many('import.rest.inv.deta1','import_id','Detalle a Importar')
	limit = fields.Integer('Limite')
	by_lot = fields.Boolean('Por Lote',default=False)
	mistakes = fields.Binary('Lineas no importadas')

	def verify_columns(self, data, columns,read_data):
		log = ''
		for c, i in enumerate(data, 1):
			if len(i) != columns:
				log += 'Linea ' + str(c) + '\n'
		if log:
			raise UserError('El archivo debe contener ' + str(columns) + ' columnas en cada fila, las siguientes lineas no cumplen esta condicion: \n' + log)
		else:
			fileobj = TemporaryFile('w+')
			fileobj.write(base64.decodestring(read_data['file_inv']))
			fileobj.seek(0)
			c2=base64.decodestring(read_data['file_inv'])
			fic = csv.reader(fileobj,delimiter='|',quotechar='"')
			return fic
	
	@api.one
	def load_lines(self):
		for line in self.lines:
			if line.lot_ids:
				for l in line.lot_ids:
					l.lot_id.unlink()
				line.lot_ids.unlink()
			line.unlink()
		if self.file_inv:
			self.env.cr.execute("set client_encoding ='UTF8';")
			line_obj = self.env['import.rest.inv.deta1']
			read_data = self.read()[0]
			fileobj = TemporaryFile('w+')
			fileobj.write(base64.decodestring(read_data['file_inv']))
			fileobj.seek(0)
			c2=base64.decodestring(read_data['file_inv'])
			fic = csv.reader(fileobj,delimiter='|',quotechar='"')
			direccion = self.env['main.parameter'].search([],limit=1).dir_create_file
			f = open(direccion+"lineas_no_importadas.csv","w+")
			#Creación de líneas en pantalla.
			aux, array_spol, qty, flag = None, [], 0, False
			if self.by_lot:
				fic = self.verify_columns(fic, 6, read_data)
				for c, data in enumerate(fic):
					if c == 0:
						aux = data[1]
					if aux == data[1]:
						pro = self.env['product.product'].search([('default_code','=',data[1])],limit=1)
						tmpl = self.env['product.template'].browse(pro.product_tmpl_id.id)
						spl = self.env['stock.production.lot'].create({'product_id':pro.id,'name':data[5]})
						spol = self.env['stock.pack.operation.lot'].create({'lot_name':spl.name,'lot_id':spl.id,'qty':data[2]})
						array_spol.append(spol.id)
						qty += float(data[2])
						price_unit = float(data[3])
					else:
						try:
							if pro:
								vals = {
									'product_id':pro.id,
									'product_qty':qty,
									'price_unit':price_unit,
									'import_id':self.id,
									'lot_ids':[(6,0,array_spol)]
								}
								line_obj.create(vals)
								array_spol, qty, aux = [], 0, data[1]
							else:
								flag = True
								f.write("%s|%s|%s|%s|%s|%s\r\n"%(data[0],data[1],data[2],data[3],data[4],data[5]))
						except Exception as e:
							raise UserError(e)
						pro = self.env['product.product'].search([('default_code','=',data[1])],limit=1)
						tmpl = self.env['product.template'].browse(pro.product_tmpl_id.id)
						spl = self.env['stock.production.lot'].create({'product_id':pro.id,'name':data[5]})
						spol = self.env['stock.pack.operation.lot'].create({'lot_name':spl.name,'lot_id':spl.id,'qty':data[2]})
						array_spol.append(spol.id)
						qty += float(data[2])
						price_unit = float(data[3])
				try:
					if pro:
						vals = {
							'product_id':pro.id,
							'product_qty':qty,
							'price_unit':price_unit,
							'import_id':self.id,
							'lot_ids':[(6,0,array_spol)]
						}
						line_obj.create(vals)
						array_spol, qty, aux = [], 0, data[1]
					else:
						flag = True
						f.write("%s|%s|%s|%s|%s|%s\r\n"%(data[0],data[1],data[2],data[3],data[4],data[5]))
				except Exception as e:
					raise UserError(e)
				if flag:
					f.close()
					f = open(direccion+"lineas_no_importadas.csv","rb")
					self.mistakes = base64.encodestring(''.join(f.readlines()))
			else:
				fic = self.verify_columns(fic, 5, read_data)
				for data in fic:
					try:
						pro = self.env['product.product'].search([('default_code','=',data[1])],limit=1)
						tmpl = self.env['product.template'].browse(pro.product_tmpl_id.id)
						# print data[0],pro
						if pro:
							vals = {
								'product_id':pro.id,
								'product_qty':float(data[2]),
								'price_unit':float(data[3]),
								'import_id':self.id,
							}
							line_obj.create(vals)
						else:
							flag = True
							f.write("%s|%s|%s|%s|%s\r\n"%(data[0],data[1],data[2],data[3],data[4]))
					except Exception as e:
						raise UserError(e)
				if flag:
					f.close()
					f = open(direccion+"lineas_no_importadas.csv","r").read()
					self.mistakes = base64.encodestring(f)


	@api.one
	def create_inv(self):
		npicking, array_pickings = 0, [] 
		if not self.location_dest_id.name:
			raise UserError("El almacen de destino seleccionado no tiene ubicacion padre")
		vals_picking = {
			'location_id':self.location_id.id,
			'location_dest_id':self.location_dest_id.id,
			'fecha_kardex':self.date_inv,
			'origin':'Inventario Inicial',
			'date_done':self.date_inv,
			'picking_type_id':self.picking_type_id.id,
			'min_date':self.date_inv,
			'date':self.date_inv,
			'max_date':self.date_inv,
			'name':'Inventario - '+str(npicking)+' - '+self.location_dest_id.name + ' - ' +  str(self.id),
			'einvoice_12':16,
		}
		picking = self.env['stock.picking'].create(vals_picking)
		array_pickings.append(picking)
		count = 1
		for line in self.lines:
			move = self.env['stock.move'].create(self._get_move_values(line.product_id,line.price_unit,line.product_qty,self.location_id.id,self.location_dest_id.id,picking))
			count = count + 1
			if count > self.limit:
				npicking = npicking + 1
				vals_picking.update({'name':'Inventario - '+str(npicking)+' - '+self.location_dest_id.location_id.name+ ' - ' +  str(self.id)})
				picking = self.env['stock.picking'].create(vals_picking)
				array_pickings.append(picking)
				count = 1
		if self.by_lot:
			for picking in array_pickings:
				picking.action_confirm()
				for operation in picking.pack_operation_product_ids:
					line = filter(lambda l:l.product_id == operation.product_id,self.lines)[0]
					for l in line.lot_ids:
						l.operation_id = operation.id
					operation.pack_lot_ids = [(6,0,line.lot_ids.ids)]

	def _get_move_values(self, product,price_unit,qty, location_id, location_dest_id,idmain):
		self.ensure_one()
		cadname = 'importado - '+ str(self.id) +str(product.id)

		return {
			'product_id': product.id,
			'product_uom': product.uom_id.id,
			'product_uom_qty': qty,
			# 'product_qty': qty,
			'price_unit':price_unit,
			'date': self.date_inv,
			'location_id': location_id,
			'location_dest_id': location_dest_id,
			'picking_id':idmain.id,
			'origin':'Inventario Inicial',
			'picking_type_id':self.picking_type_id.id,
			'ordered_qty':qty,
			'date_expected':self.date_inv,
			'name': _('INV:') + (idmain.name or ''),
		}
				
class import_rest_inv_deta1(models.Model):
	_name = 'import.rest.inv.deta1'

	product_id = fields.Many2one('product.product','Producto')
	product_qty = fields.Float('Cantidad',digits=(20,6))
	price_unit = fields.Float('Precio',digits=(20,6))
	import_id = fields.Many2one('import.rest.inv1','Cabecera importador')
	lot_ids = fields.Many2many('stock.pack.operation.lot','import_pack_operation_rel','import_id','operation_lot_id',string="Lotes")

class stock_picking(models.Model):
	_inherit = "stock.picking"

	@api.model
	def create(self, vals):
		# TDE FIXME: clean that brol
		
		defaults = self.default_get(['name', 'picking_type_id'])
		if vals.get('name', '/') == '/' and defaults.get('name', '/') == '/' and vals.get('picking_type_id', defaults.get('picking_type_id')):
			vals['name'] = self.env['stock.picking.type'].browse(vals.get('picking_type_id', defaults.get('picking_type_id'))).sequence_id.next_by_id()

		# TDE FIXME: what ?
		# As the on_change in one2many list is WIP, we will overwrite the locations on the stock moves here
		# As it is a create the format will be a list of (0, 0, dict)
		if vals.get('move_lines') and vals.get('location_id') and vals.get('location_dest_id'):
			for move in vals['move_lines']:
				if len(move) == 3:
					move[2]['location_id'] = vals['location_id']
					move[2]['location_dest_id'] = vals['location_dest_id']
		
		if 'origin' in vals:
			if vals['origin']=='Inventario Inicial':
				if 'message_follower_ids' in vals:
					vals['message_follower_ids']= False
		return super(stock_picking, self).create(vals)