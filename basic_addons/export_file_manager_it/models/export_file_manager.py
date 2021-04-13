# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging,os

_logger = logging.getLogger(__name__)

class ExportFileManager(models.TransientModel):
	_name = 'export.file.manager'
	
	file_name = fields.Char(string='Name',required=True)
	file = fields.Binary(string='file',required=True)
	content_type = fields.Char('Content-Type')
	
	def export_file(self,clear=True,path=None,options=None):
		""" Exporta archivos .pdf y .xlsx
		param clear bool: bool clear: Intenta limpiar el archivo temporal del sistema.
		param path str: ruta absoluta del archivo temporal generado.
		param options dict: Opciones adicionales (acepta: msg_success_notify)
		returns type: ir.actions.report.xml action
		"""
		if clear and path:
			if os.path.exists(path):
				os.remove(path)
			else:
				_logger.warning(u'Path file "%s" does not exist !'%path)
		return {
			'res_id': self.id,
			'type': 'ir.actions.report.xml',
			'model': self._name,
			'report_type': 'efm_reports',
			'name': 'direct_download',
			'efm_report_options':options or {}
		}

	@api.model
	def call_object_method(self,model,method,ids,**kwargs):
		try:
			model = self.env[model]
		except KeyError:
			return
		objs = model.browse(ids)
		method = getattr(objs,method,None)
		if method and callable(method):
			#Debería retornar un dict de tipo efm_reports
			return method(**kwargs)

		# optional alternatives:		
		# return {
		# 	'uid' : self.id,
		# 	'type': 'ir.actions.act_url',
		# 	'url' : '/web/content/%s/%s/file/%s?download=true'%(self._name,self.id,self.file_name),}
		# return {
		# 	'uid' : self.id,
		# 	'type': 'ir.actions.act_url',
		# 	'url' : '/download/file/%i'%self.id,
		# 	}