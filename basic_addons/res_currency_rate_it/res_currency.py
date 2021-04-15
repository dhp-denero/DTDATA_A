# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class res_currency_rate(models.Model):
	_inherit = 'res.currency.rate'

	period_name = fields.Char("Periodo", size=50 )

	@api.multi
	def write(self,vals):
		if not vals:
			vals = {}

		date_tmp = "Indefinido"
		if 'name' in vals:
			date_tmp = str(vals['name'])[:7].replace("-","/")

		if self.name:
			date_tmp = str(self.name)[:7].replace("-","/")
		vals['period_name'] = date_tmp
		t = super(res_currency_rate,self).write(vals)

		return t

	@api.model
	def create(self,vals):
		if not vals:
			vals={}
		t = super(res_currency_rate,self).create(vals)
		if t.name:
			t.period_name = str(t.name)[:7].replace("-","/")
		else:
			t.period_name = "Indefinido"

		return t






class res_currency_wizard_optional(models.Model):
	_name="res.currency.wizard.optional"

	check_type = fields.Selection([('auto', 'Automático'),
                                   ('manual', 'Manual')], 'Modalidad')
	fecha_ini = fields.Date("Fecha Inicio")
	fecha_fin = fields.Date("Fecha Final")
	fecha_unica= fields.Date("Fecha")
	type_compra = fields.Float("Valor de Compra", digits=(12,3))
	type_venta = fields.Float("Valor de Venta",digits=(12,3))

	@api.onchange('fecha_ini')
	def _onchange_type_account(self):
		import datetime
		if self.fecha_ini:
			if self.fecha_ini > str(datetime.datetime.now()):
				self.fecha_ini =""
		if self.fecha_ini:
			self.fecha_fin = self.fecha_ini



	@api.onchange('fecha_fin')
	def _onchange_type_fin_account(self):
		import datetime
		if self.fecha_fin:
			if self.fecha_fin > str(datetime.datetime.now()):
				self.fecha_fin =""

	@api.multi
	def do_rebuild(self):
		if self.check_type == 'auto':
			self.do_auto()
		else:
			self.do_manual()

		return {
			'domain' : [('currency_id.name','=', 'USD')],
			'type': 'ir.actions.act_window',
			'res_model': 'res.currency.rate',
			'view_mode': 'tree',
			'view_type': 'form',
		}


	@api.multi
	def do_manual(self):
		currency_extra = self.env['res.currency'].search([('name','=','USD')])[0]

		tmp_fn = self.env['res.currency.rate'].search([('currency_id','=',currency_extra.id),('name','=',str(self.fecha_unica))])

		if len(tmp_fn)>0:
			tmp_fn.type_purchase =  float(self.type_compra)
			tmp_fn.type_sale = float(self.type_venta)
			tmp_fn.rate = 1 /float(self.type_venta)
		else:

			import datetime
			date_sunat_obj = datetime.datetime.strptime(str(self.fecha_unica),'%Y-%m-%d')

			data = {
				'name':self.fecha_unica,
				'type_purchase' :  float(self.type_compra),
				'type_sale' : float(self.type_venta),
				'rate' : 1 /float(self.type_venta),
				'tipo' : 'Manual',
			}
			print data
			new_rate= self.env['res.currency.rate'].create(data)
			print new_rate
			currency_extra.write({'rate_ids':[(4,new_rate.id)]})

	@api.multi
	def do_auto(self):
		import urllib, urllib2
		import datetime
		import pprint
		import requests
		import pandas as pd
		from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


		fecha_inicial = str(datetime.datetime.strptime(self.fecha_ini, '%Y-%m-%d'))[0:10]
		fecha_final = str(datetime.datetime.strptime(self.fecha_fin, '%Y-%m-%d'))[0:10]
		inicio = fecha_inicial[8:] + "/" + fecha_inicial[5:7] + "/" + fecha_inicial[:4]
		fin = fecha_final[8:] + "/" + fecha_final[5:7] + "/" + fecha_final[:4]
		url = "https://www.sbs.gob.pe/app/stats/seriesH-tipo_cambio_moneda_excel.asp?fecha1="+inicio+"&fecha2="+fin+"&moneda=02&cierre="

		try:
			res = requests.get(url).content
			df_list = pd.read_html(url, index_col=0)
			df = df_list[-1]
		except:
			raise UserError('No se puede conectar a la página de Sunat!')

		currency_extra = self.env['res.currency'].search([('name','=','USD')])[0]
		j = 0
		for i in df.index:
			if str(i) != "FECHA":
				format_datetime = str(i)[6:10]+"-"+str(i)[3:5]+"-"+str(i)[:2]+" 00:00:00"
				date = fields.Datetime.from_string(format_datetime)
				registro = self.env['res.currency.rate'].search([('currency_id','=',currency_extra.id),('name','=',date.date())], limit=1)
				if len(registro) != 0:
					registro.type_purchase = float(df.iloc[j,1])
					registro.type_sale = float(df.iloc[j,2])
					registro.tipo = "Automatico"

				elif len(registro) == 0:
					data = {
						'name':date.date(),
						'type_purchase':df.iloc[j,1],
						'type_sale':df.iloc[j,2],
						'period_name':str(date.date()),
						'tipo':'Automatico',
						'currency_id':currency_extra.id,
						}
					registro= self.env['res.currency.rate'].create(data)

			j += 1

		return 0