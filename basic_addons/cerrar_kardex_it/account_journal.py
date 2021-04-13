# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp import models, fields, api  , exceptions , _

class kardex_cerrado_config(models.Model):
	_name = 'kardex.cerrado.config'

	name = fields.Char('Nombre',required=True)
	fecha_inicio = fields.Date('Fecha Inicio',required=True)
	fecha_fin = fields.Date('Fecha Final',required=True)
	listado_locaciones = fields.Many2many('stock.location','kardex_cerrador_locaciones_rel','kardex_cc_id','location_id','Ubicaciones')


class gastos_vinculados_it(models.Model):
	_inherit = 'gastos.vinculados.it'


	@api.model
	def create(self,vals):		

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
			
		t = super(gastos_vinculados_it,self).create(vals)

		if True:
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(t.date_invoice if t.tomar_valor == 'factura' else t.date_purchase)[:10] >= i.fecha_inicio and str(t.date_invoice if t.tomar_valor == 'factura' else t.date_purchase)[:10] <= i.fecha_fin:
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return t

		return t

	@api.one
	def copy(self,default=None):
		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		t = super(gastos_vinculados_it,self).copy(default)

		if True:			
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(t.date_invoice if t.tomar_valor == 'factura' else t.date_purchase)[:10] >= i.fecha_inicio and str(t.date_invoice if t.tomar_valor == 'factura' else t.date_purchase)[:10] <= i.fecha_fin:
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return t

		return t


	@api.one
	def write(self,vals):
		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		

		t = super(gastos_vinculados_it,self).write(vals)
		self.refresh()

		if True:
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(self.date_invoice if self.tomar_valor == 'factura' else self.date_purchase)[:10] >= i.fecha_inicio and str(self.date_invoice if self.tomar_valor == 'factura' else self.date_purchase)[:10] <= i.fecha_fin:
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return m

		return m

	@api.one
	def unlink(self):

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		if True:
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(self.date_invoice if self.tomar_valor == 'factura' else self.date_purchase)[:10] >= i.fecha_inicio and str(self.date_invoice if self.tomar_valor == 'factura' else self.date_purchase)[:10] <= i.fecha_fin:
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return super(gastos_vinculados_it,self).unlink()
		return super(gastos_vinculados_it,self).unlink()





class account_invoice(models.Model):
	_inherit = 'account.invoice'



	@api.model
	def create(self,vals):		

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
			
		t = super(account_invoice,self).create(vals)

		flag = False
		for linea in t.invoice_line_ids:
			if self.env['main.parameter'].search([])[0].etiqueta_analitica.id and len(linea.analytic_tag_ids) >0:
				if linea.analytic_tag_ids[0].id == self.env['main.parameter'].search([])[0].etiqueta_analitica.id:
					flag = True

		if flag:			
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(t.date)[:10] >= i.fecha_inicio and str(t.date)[:10] <= i.fecha_fin:
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return t

		return t

	@api.one
	def copy(self,default=None):
		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		

		t = super(account_invoice,self).copy(default)

		flag = False
		for linea in t.invoice_line_ids:
			if self.env['main.parameter'].search([])[0].etiqueta_analitica.id and len(linea.analytic_tag_ids) >0:
				if linea.analytic_tag_ids[0].id == self.env['main.parameter'].search([])[0].etiqueta_analitica.id:
					flag = True

		if flag:			
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(t.date)[:10] >= i.fecha_inicio and str(t.date)[:10] <= i.fecha_fin:
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return t

		return t


	@api.one
	def write(self,vals):
		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		

		t = super(account_invoice,self).write(vals)
		self.refresh()
		flag = False

		for linea in self.invoice_line_ids:
			if self.env['main.parameter'].search([])[0].etiqueta_analitica.id and len(linea.analytic_tag_ids) >0:
				if linea.analytic_tag_ids[0].id == self.env['main.parameter'].search([])[0].etiqueta_analitica.id:
					flag = True
		
		
		if flag:
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(self.date)[:10] >= i.fecha_inicio and str(self.date)[:10] <= i.fecha_fin:
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
		return t

	@api.one
	def unlink(self):

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		flag = False

		for linea in self.invoice_line_ids:
			if self.env['main.parameter'].search([])[0].etiqueta_analitica.id and len(linea.analytic_tag_ids) >0:
				if linea.analytic_tag_ids[0].id == self.env['main.parameter'].search([])[0].etiqueta_analitica.id:
					flag = True
		
		if flag:
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(self.date)[:10] >= i.fecha_inicio and str(self.date)[:10] <= i.fecha_fin:
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return super(account_invoice,self).unlink()
		return super(account_invoice,self).unlink()






class stock_picking(models.Model):
	_inherit = 'stock.picking'


	@api.one
	def _get_estate_kardex_closed(self):
		texto_rpt = 'Sin Procesar'
		for i in self.env['kardex.cerrado.config'].search([]):
			if str(self.fecha_kardex)[:10] >= i.fecha_inicio and str(self.fecha_kardex)[:10] <= i.fecha_fin:
				texto_rpt = 'Cerrado / Procesado'	
		self.is_closed_kardex = texto_rpt

	is_closed_kardex = fields.Char('Estado del Kardex',compute="_get_estate_kardex_closed")

	fecha_ingreso_lote = fields.Date('Fecha Ingreso Lote')

	@api.one
	def nohacernada(self):
		return

	@api.model
	def create(self,vals):		

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
				
		if True:
			t = super(stock_picking,self).create(vals)
			if len(vals.keys() )== 1:
				if vals.keys()[0] == 'invoice_id':
					return t
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(t.fecha_kardex)[:10] >= i.fecha_inicio and str(t.fecha_kardex)[:10] <= i.fecha_fin:
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return t

		return super(stock_picking,self).create(vals)

	@api.one
	def copy(self,default=None):
		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		

		if True:
			t = super(stock_picking,self).copy(default)
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(t.fecha_kardex)[:10] >= i.fecha_inicio and str(t.fecha_kardex)[:10] <= i.fecha_fin:
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return t

		return super(stock_picking,self).copy(default)

	@api.one
	def write(self,vals):
		m = super(stock_picking,self).write(vals)

		if len(vals.keys() )== 1:
			if vals.keys()[0] == 'invoice_id':
				return m

		self.refresh()

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']		
		
		if True:
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(self.fecha_kardex)[:10] >= i.fecha_inicio and str(self.fecha_kardex)[:10] <= i.fecha_fin:
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return m

		return m

	@api.one
	def unlink(self):

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		if True:
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(self.fecha_kardex)[:10] >= i.fecha_inicio and str(self.fecha_kardex)[:10] <= i.fecha_fin:
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return super(stock_picking,self).unlink()
		return super(stock_picking,self).unlink()




class stock_move(models.Model):
	_inherit = 'stock.move'


	@api.model
	def create(self,vals):		

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		if True:
			t = super(stock_move,self).create(vals)
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(t.picking_id.fecha_kardex)[:10] >= i.fecha_inicio and str(t.picking_id.fecha_kardex)[:10] <= i.fecha_fin:
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return t

		return super(stock_move,self).create(vals)

	@api.one
	def copy(self,default=None):
		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		if True:
			t = super(stock_move,self).copy(default)
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(t.picking_id.fecha_kardex)[:10] >= i.fecha_inicio and str(t.picking_id.fecha_kardex)[:10] <= i.fecha_fin:
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
		return super(stock_move,self).copy(default)

	@api.one
	def write(self,vals):
		m = super(stock_move,self).write(vals)

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		if True:
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(self.picking_id.fecha_kardex)[:10] >= i.fecha_inicio and str(self.picking_id.fecha_kardex)[:10] <= i.fecha_fin:
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return m

		return m

	@api.one
	def unlink(self):

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		if True:
			for i in self.env['kardex.cerrado.config'].search([]):
				if str(self.picking_id.fecha_kardex)[:10] >= i.fecha_inicio and str(self.picking_id.fecha_kardex)[:10] <= i.fecha_fin:
					raise osv.except_osv('Alerta!', u"El kardex fue cerrado para este fecha y Ubicación")
			return super(stock_move,self).unlink()
		return super(stock_move,self).unlink()
