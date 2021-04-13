# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from datetime import *

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	canceled_guide = fields.Boolean(string='Guia Anulada',default=False)
	related_location = fields.Selection(string='Related Location',related='location_id.usage',store=True)
	related_location_dest = fields.Selection(string='Related Location Dest',related='location_dest_id.usage',store=True)
	anulation_line_ids = fields.One2many('stock.picking.anulation.line','picking_id')

	@api.multi
	def get_wizard(self):
		wizard = self.env['stock.picking.wizard'].create({'name':'Cancelar Guia','guide_number':self.numberg})
		if (self.related_location == 'internal' and self.related_location_dest == 'internal') or (self.related_location == 'internal' and self.related_location_dest == 'customer'):
			return {
				'type':'ir.actions.act_window',
				'res_id':wizard.id,
				'view_type':'form',
				'view_mode':'form',
				'res_model':'stock.picking.wizard',
				'views':[[self.env.ref('cancel_guide.stock_view_picking_form_wizard').id,'form']],
				'target':'new',
			}

class StockPickingHistory(models.Model):
	_name = 'stock.picking.anulation.line'

	picking_id = fields.Many2one('stock.picking')
	guide_number = fields.Char(string='Numero de Guia')
	cancel_reason = fields.Selection([('print_error','Error de Impresion'),
									('return','Devolucion')],string='Motivo de Anulacion')
	cancel_date = fields.Date(string='Fecha de Anulacion')
	res_user_id = fields.Many2one('res.users',string='Usuario')

class StockPickingWizard(models.TransientModel):
	_name = 'stock.picking.wizard'

	guide_number = fields.Char(string='Numero de Guia para Anular')	
	cancel_reason = fields.Selection([('print_error','Error de Impresion'),
									('return','Devolucion')],string='Motivo de Anulacion')
	cancel_date = fields.Date(string='Fecha de Anulacion',default=lambda self:date.today())

	@api.multi
	def cancel_guide(self):
		picking = self.env['stock.picking'].browse(self.env.context['active_id'])
		
		self.env['stock.picking.anulation.line'].create({
														'picking_id':picking.id,
														'guide_number':self.guide_number,
														'cancel_reason':self.cancel_reason,
														'cancel_date':self.cancel_date,
														'res_user_id':self._uid
														})
		if picking.serie_guia and self.cancel_reason == 'print_error':
			picking.numberg = picking.serie_guia.next_by_id()
		wizard = self.env['stock.return.picking'].create({'name':'Devolver'})
		context = self._context or {}
		if self.cancel_reason == 'return':
			picking.canceled_guide = True
			return {
				'type':'ir.actions.act_window',
				'res_id':wizard.id,
				'view_type':'form',
				'view_mode':'form',
				'res_model':'stock.return.picking',
				'views':[[self.env.ref('stock.view_stock_return_picking_form').id,'form']],
				'target':'new',
				'context':context
			}