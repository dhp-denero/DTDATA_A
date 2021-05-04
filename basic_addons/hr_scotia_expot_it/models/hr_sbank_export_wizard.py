# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from datetime import date, datetime
from odoo.exceptions import ValidationError, UserError
import base64
import io
from xlsxwriter.workbook import Workbook
import sys
reload(sys)
sys.setdefaultencoding('iso-8859-1')
import os
import copy

import StringIO
import time

import calendar
from datetime import date, datetime
from openerp.osv import osv
from math import modf
from decimal import *
import traceback
from lxml import etree
from StringIO import StringIO
import time


class hr_payslip_run(models.Model):
	_inherit='hr.payslip.run'

	def make_excel_sbank(self):
		ctx = dict(self._context or {})
		defa = self.env['hr.sbank.export.config'].search([])[0]
		ctx.update({
				'default_name':defa.id,
				# 'default_paydate':datetime.now().date,
				'default_type_export':'payslip_run',
				'default_payslip_run_id':self.id,
			})
			
		
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'hr.sbank.export.wizard',
			'view_type': 'form',
			'view_mode': 'form',
			'target': 'new',
			'context':ctx,
		}


class hr_sbank_export_wizard(models.TransientModel):
	_name='hr.sbank.export.wizard'

	name=fields.Many2one('hr.sbank.export.config','Plantilla de configuración')
	pay_date = fields.Date('Fecha de pago')
	type_export = fields.Selection([('payslip_run','Planilla'),('gratif','Gratificaciones'),('cts','CTS')],'Tipo de exportación')
	payslip_run_id = fields.Many2one('hr.payslip.run','Planilla a exportar')

	def make_excel_pla_export(self):
		if self.type_export!='payslip_run':
			raise UserError('El formato seleccionado aun está en desarrollo')			

		self.env['planilla.planilla.tabular.wizard'].reconstruye_tabla(self.payslip_run_id.date_start,self.payslip_run_id.date_end)

		try:
			direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except: 
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		workbook = Workbook(direccion+'planilla_exportar.xlsx')
		worksheet = workbook.add_worksheet(
			str(self.payslip_run_id.id)+'-'+self.payslip_run_id.date_start+'-'+self.payslip_run_id.date_end)
		worksheet.set_landscape()  # Horizontal
		worksheet.set_paper(9)  # A-4
		worksheet.set_margins(left=0.75, right=0.75, top=1, bottom=1)
		worksheet.fit_to_pages(1, 0)  # Ajustar por Columna

		fontSize = 8
		bold = workbook.add_format(
			{'bold': True, 'font_name': 'Arial', 'font_size': fontSize})
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True, 'font_name': 'Arial'})
		# boldbord.set_border(style=1)
		boldbord.set_align('center')
		boldbord.set_align('bottom')
		boldbord.set_text_wrap()
		boldbord.set_font_size(fontSize)
		boldbord.set_bg_color('#99CCFF')
		numberdos = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'right'})
		formatLeft = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'font_size': fontSize})
		formatRight = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'right', 'font_size': fontSize})		
		formatLeftColor = workbook.add_format(
			{'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'bg_color': '#99CCFF', 'font_size': fontSize})
		styleFooterSum = workbook.add_format(
			{'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'right', 'font_size': fontSize, 'top': 1, 'bottom': 2})
		styleFooterSum.set_bottom(6)
		numberdos.set_font_size(fontSize)
		bord = workbook.add_format()
		bord.set_border(style=1)
		bord.set_text_wrap()
		# numberdos.set_border(style=1)

		title = workbook.add_format({'bold': True, 'font_name': 'Arial'})
		title.set_align('center')
		title.set_align('vcenter')
		# title.set_text_wrap()
		title.set_font_size(18)
		company = self.env['res.company'].search([], limit=1)[0]

		x = 0

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		worksheet.merge_range(
			'D1:O1', u"PLANILLA DE SUELDOS Y SALARIOS EXPORTAR", title)
		worksheet.set_row(x, 29)
		x = x+2

		worksheet.write(x, 0, u"Empresa:", bold)
		worksheet.write(x, 1, company.name, formatLeft)


		x = x+3

		header_planilla_tabular = self.env['ir.model.fields'].search(
			[('name', 'like', 'x_%'), ('model', '=', 'planilla.tabular')], order="create_date")
		worksheet.write(x, 0, 'CODIGO EMPLEADO', formatLeftColor)
		worksheet.write(x, 1, 'NOMBRE DEL EMPLEADO', formatLeftColor)
		worksheet.write(x, 2, 'CONCEPTO', formatLeftColor)
		worksheet.write(x, 3, 'FECHA DE PAGO', formatLeftColor)
		worksheet.write(x, 4, 'MONTO A PAGAR', formatLeftColor)
		worksheet.write(x, 5, 'FORMA DE PAGO', formatLeftColor)
		worksheet.write(x, 6, 'CODIGO OFICINA', formatLeftColor)
		worksheet.write(x, 7, 'CODIGO CUENTA', formatLeftColor)
		worksheet.write(x, 8, 'IFT?', formatLeftColor)
		worksheet.write(x, 9, 'DOCUMENTO DE INDENTIDAD', formatLeftColor)
		worksheet.write(x, 10, 'CCI', formatLeftColor)
		x=x+1
		
		for l in self.payslip_run_id.slip_ids:
			if not l.employee_id.bank_account_id.acc_number:
				continue
			valor = 0
			a=False
			a = l.line_ids.filtered(lambda p: p.salary_rule_id.id == self.name.salary_rule_id.id)
			if a:
				valor = a.total
			metodopago = '3'
			cci=''
			codofi=''
			codcta=''
			desde=int(self.name.cod_ofi_pos[0:1])
			hasta=int(self.name.cod_ofi_pos[2:])
			if self.name.bank_id.id!=l.employee_id.bank_account_id.bank_id.id:
				metodopago='4'
				cci=l.employee_id.bank_account_id.acc_icc_number
			else:
				codofi=l.employee_id.bank_account_id.acc_number[desde-1:hasta]
				codcta=l.employee_id.bank_account_id.acc_number[int(self.name.cod_cta_pos)+1:]

			nombresc=l.employee_id.nombres.strip()+' '+l.employee_id.a_paterno.strip()+' '+l.employee_id.a_materno.strip()

			worksheet.write(x,0,l.employee_id.identification_id,formatLeft)
			worksheet.write(x,1,nombresc,formatLeft)
			worksheet.write(x,2,self.name.text_concep,formatLeft)
			worksheet.write(x,3,self.pay_date,formatLeft)
			worksheet.write(x,4,valor,formatRight)
			worksheet.write(x,5,metodopago)
			worksheet.write(x,6,codofi,formatLeft)
			worksheet.write(x,7,codcta,formatLeft)
			worksheet.write(x,8,'',formatLeft)
			worksheet.write(x,9,l.employee_id.identification_id,formatLeft)
			worksheet.write(x,10,cci,formatLeft)
			x=x+1


		workbook.close()

		f = open(direccion+'planilla_exportar.xlsx', 'rb')

		vals = {
			'output_name': 'planilla_exportar.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),
		}

		sfs_id = self.env['planilla.export.file'].create(vals)

		return {
			"type": "ir.actions.act_window",
			"res_model": "planilla.export.file",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}