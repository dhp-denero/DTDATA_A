# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api, _
import codecs
from datetime import *
from odoo.exceptions import UserError, ValidationError


class saldos_iniciales(models.Model):

	_name='saldos.iniciales'

	periodo = fields.Char('Periodo')
	fecha_emision = fields.Date('Fecha Emisión')
	fecha_venci = fields.Date('Fecha Venci')
	ruc = fields.Char('ruc')
	empresa = fields.Char('Empresa')
	tipo_cuenta = fields.Char('Tipo Cuenta')
	code = fields.Char('Cuenta')
	tipo = fields.Char('Tipo Documento')
	nro_comprobante = fields.Char('Nro. Comprobante')
	debe = fields.Float('Debe',digits=(12,2))
	haber = fields.Float('Haber',digits=(12,2))
	saldo = fields.Float('Saldo',digits=(12,2))
	divisa = fields.Char('Divisa')
	amount_currency = fields.Float('Importe',digits=(12,2))



class invoice_saldoinicial_exportar(osv.TransientModel):
	_name='invoice.saldoinicial.exportar'
	
	tipo = fields.Selection([('1','Por Cobrar'),('2','A Pagar')],'Tipo')

	@api.multi
	def do_rebuild(self):

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		docname = 'SaldoInicialopt.csv'
		

		self.env.cr.execute("""			
			COPY (			
			select 

				COALESCE(rp.nro_documento,'000000') as n_ruc,
				COALESCE(rp.name,'SALDO INICIAL') as n_razonsoc,
				am.date as n_fecha_emision,				
				f_final.fin as n_fecha_vencimiento,
				null::varchar as n_vendedor,
				CASE WHEN COALESCE(itd.code,'00'::varchar) = '' then '00' else COALESCE(itd.code,'00'::varchar) end as n_tipo_doc,
				CASE WHEN COALESCE(TRIM(aml.nro_comprobante),'00000000') = '' then '00000000' else COALESCE(TRIM(aml.nro_comprobante),'00000000') end as n_numero,
				COALESCE(rc.name,'PEN') as n_moneda,				
				CASE WHEN abs(T.saldo) < 0.01 then 0 else T.saldo end as n_saldo_mn,
				T.amount_currency  as n_saldo_me,
				aa.code as n_cuenta,
				aml.tc as n_tipo_cambio
				from (
				select concat(account_move_line.partner_id,'-',account_id,'-',type_document_it,'-',TRIM(nro_comprobante) ) as identifica,min(account_move_line.id),sum(debit)as debe,sum(credit) as haber, sum(debit)-sum(credit) as saldo, sum(amount_currency) as amount_currency, array_agg(account_move_line.id) as aml_ids from account_move_line
				inner join account_move ami on ami.id = account_move_line.move_id
				inner JOIN account_period api ON api.date_start <= ami.fecha_contable and api.date_stop >= ami.fecha_contable  and api.special = ami.fecha_special

				left join account_account on account_account.id=account_move_line.account_id
				left join account_account_type aat on aat.id = account_account.user_type_id
				where --account_account.reconcile = true and 
				( """ +( "aat.type='receivable'" if self.tipo == '1' else "aat.type='payable'")+ """   ) and ami.state != 'draft'
				and periodo_num(api.code) >= periodo_num('00/""" + str(self.env['main.parameter'].search([])[0].fiscalyear) + """') and periodo_num(api.code) <= periodo_num('12/""" + str(self.env['main.parameter'].search([])[0].fiscalyear) + """')
				group by identifica) as T
				inner join account_move_line aml on aml.id = T.min
				inner join account_move am on am.id = aml.move_id
				inner JOIN account_period ap ON ap.date_start <= am.fecha_contable and ap.date_stop >= am.fecha_contable  and ap.special = am.fecha_special
				left join (
select concat(aml.partner_id,'-',aml.account_id,'-',aml.type_document_it,'-',TRIM(aml.nro_comprobante) )as ide, max(aml.date_maturity) as fin, am.id from
account_move am 
inner join account_move_line aml on aml.move_id = am.id 
group by am.id,concat(aml.partner_id,'-',aml.account_id,'-',aml.type_document_it,'-',TRIM(aml.nro_comprobante) )
) as f_final on f_final.ide = T.identifica and am.id = f_final.id

				left join res_partner rp on rp.id = aml.partner_id
				left join einvoice_catalog_01 itd on itd.id = aml.type_document_it
				left join account_account aa on aa.id = aml.account_id
				left join res_currency rc on rc.id = aa.currency_id
				left join account_account_type aat on aat.id = aa.user_type_id
				left join (select concat(partner_id,account_id,it_type_document,TRIM(reference) ) as identifica,date,date_due from account_invoice) facturas on facturas.identifica=t.identifica
				where abs(T.saldo) >= 0.01
				order by n_ruc, n_tipo_doc, n_numero


		)TO '"""+direccion+docname+"""'   WITH DELIMITER ',' CSV HEADER			
		""")

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		f = open(direccion + docname, 'rb')			
		vals = {
			'output_name': docname,
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}
		sfs_id = self.env['export.file.save'].create(vals)
		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

class main_parameter(models.Model):
	_inherit = 'main.parameter'

	cta_perdida_resultado_si = fields.Many2one('account.account','Cuenta Resultados AC. Perdida')
	cta_ganancia_resultado_si = fields.Many2one('account.account','Cuenta Resultados AC. Ganancia')

class account_sheet_work_wizard_exportar(osv.TransientModel):
	_name='account.sheet.work.wizard.exportar'


	@api.multi
	def do_rebuild(self):

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		docname = 'AsientoApertura.csv'
		
		ti_fin_compra = 0
		ti_fin_venta = 0
		tipo_cam = self.env['exchange.diff.config.line'].search( [('period_id.code','=', '12/' + str(self.env['main.parameter'].search([])[0].fiscalyear)) ] )
		if len(tipo_cam)>0:
			ti_fin_compra = tipo_cam[0].compra
			ti_fin_venta = tipo_cam[0].venta

		if not self.env['main.parameter'].search([])[0].cta_ganancia_resultado_si.id or not self.env['main.parameter'].search([])[0].cta_perdida_resultado_si.id:
			raise UserError(u'No se ha configurado las cuentas de resultado para redondeo en Contabilidad/Configuracion/Parametros/')

		self.env.cr.execute("""			
			COPY (

			select name,account_id, CASE WHEN sum(debit-credit)>0 THEN sum(debit-credit) else 0 end as debit,
			CASE WHEN sum(debit-credit)<0 THEN sum(credit-debit) else 0 end as credit,max(currency_id) as currency_id,max(tc) as tc,CASE WHEN max(currency_id) is null then null::numeric else sum(amount_currency) end as amount_currency
			from (
			select 'ASIENTO DE APERTURA'::varchar as name,case when aa.cuenta_saldo_contable is null then cuenta else aa_contable.code end as account_id,saldodeudor as debit, saldoacredor as credit,rc.name as currency_id, 
			CASE WHEN rc.name is null then null::numeric else  CASE WHEN aati.group_balance in ('B1','B2') THEN """+str(ti_fin_compra)+"""::numeric
			WHEN aati.group_balance in ('B3','B4','B5') THEN """+str(ti_fin_venta)+"""::numeric
			ELSE  0::numeric END END as tc,
			amount_currency as amount_currency
			from get_hoja_trabajo_simple_registro_reporte(false,periodo_num('00/""" + str(self.env['main.parameter'].search([])[0].fiscalyear) + """'),periodo_num('12/""" + str(self.env['main.parameter'].search([])[0].fiscalyear) + """')) as get_hoja_trabajo_simple_registro			
			inner join account_account aa on aa.code = get_hoja_trabajo_simple_registro.cuenta
			left join account_account aa_contable on aa_contable.id = aa.cuenta_saldo_contable
			left join res_currency rc on rc.id = aa.currency_id
			left join account_account_type_it aati on aati.id = aa.type_it
			where aa.clasification_sheet = '1' and (get_hoja_trabajo_simple_registro.saldodeudor != 0 or get_hoja_trabajo_simple_registro.saldoacredor != 0)
			) total 
			group by name, account_id


			union all

			select 'ASIENTO DE APERTURA'::varchar as name, 

			CASE when sum(debit-credit)>0 then '"""+self.env['main.parameter'].search([])[0].cta_ganancia_resultado_si.code+"""'  else  '"""+self.env['main.parameter'].search([])[0].cta_perdida_resultado_si.code+"""'  end as account_id,
			CASE when sum(debit-credit)>0 then 0 else abs(sum(debit-credit)) end as debit,
			CASE when sum(debit-credit)<0 then 0 else abs(sum(debit-credit)) end as credit,
			null::varchar as currency_id,
			null::numeric as tc,
			null::numeric as amount_currency

			  from (

				select name,account_id, CASE WHEN sum(debit-credit)>0 THEN sum(debit-credit) else 0 end as debit,
				CASE WHEN sum(debit-credit)<0 THEN sum(credit-debit) else 0 end as credit,max(currency_id) as currency_id,max(tc) as tc,CASE WHEN max(currency_id) is null then null::numeric else sum(amount_currency) end as amount_currency
				from (
				select 'ASIENTO DE APERTURA'::varchar as name,case when aa.cuenta_saldo_contable is null then cuenta else aa_contable.code end as account_id,saldodeudor as debit, saldoacredor as credit,rc.name as currency_id, 
				CASE WHEN aati.group_balance in ('B1','B2') THEN """+str(ti_fin_compra)+"""::numeric
				WHEN aati.group_balance in ('B3','B4','B5') THEN """+str(ti_fin_venta)+"""::numeric
				ELSE  0::numeric END as tc,
				amount_currency as amount_currency
				from get_hoja_trabajo_simple_registro_reporte(false,periodo_num('00/""" + str(self.env['main.parameter'].search([])[0].fiscalyear) + """'),periodo_num('12/""" + str(self.env['main.parameter'].search([])[0].fiscalyear) + """')) as get_hoja_trabajo_simple_registro			
				inner join account_account aa on aa.code = get_hoja_trabajo_simple_registro.cuenta
				left join account_account aa_contable on aa_contable.id = aa.cuenta_saldo_contable
				left join res_currency rc on rc.id = aa.currency_id
				left join account_account_type_it aati on aati.id = aa.type_it
				where aa.clasification_sheet = '1' and (get_hoja_trabajo_simple_registro.saldodeudor != 0 or get_hoja_trabajo_simple_registro.saldoacredor != 0)
				) total 
				group by name, account_id
			) as X


		)TO '"""+direccion+docname+"""'   WITH DELIMITER ',' CSV HEADER			
		""")

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		f = open(direccion + docname, 'rb')			
		vals = {
			'output_name': docname,
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}
		sfs_id = self.env['export.file.save'].create(vals)
		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

class account_sheet_work_wizard(osv.TransientModel):
	_name='account.sheet.work.wizard'
	
	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end = fields.Many2one('account.period','Periodo Final',required=True)
	wizrd_level_sheet = fields.Selection((('1','Cuentas de Balance'),
									('2','Cuentas de Registro')						
									),'Nivel',required=True)

	def get_fiscalyear(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		id_year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1).id
		if not id_year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			return id_year

	fiscalyear_id = fields.Many2one('account.fiscalyear','Año Fiscal',required=True,default=lambda self: self.get_fiscalyear(),readonly=True)

	@api.model
	def get_wizard(self):
		return self.env['automatic.fiscalyear'].get_wizard('B. Comprobacion',self.id,'account.sheet.work.wizard','account_sheet_work.view_account_sheet_work_wizard_form','default_period_ini','default_period_end')
		
	@api.onchange('fiscalyear_id')
	def onchange_fiscalyear(self):
		if self.fiscalyear_id:
			return {'domain':{'period_ini':[('fiscalyear_id','=',self.fiscalyear_id.id )], 'period_end':[('fiscalyear_id','=',self.fiscalyear_id.id )]}}
		else:
			return {'domain':{'period_ini':[], 'period_end':[]}}


	@api.multi
	def do_rebuild(self):
		period_ini = self.period_ini
		period_end = self.period_end
		has_currency = False
		
		filtro = []
		
		currency = False
			
		
		if self.wizrd_level_sheet == '1':
			self.env.cr.execute("""
			DROP VIEW IF EXISTS account_sheet_work_simple cascade;
			CREATE OR REPLACE view account_sheet_work_simple as (
				select * from get_hoja_trabajo_simple_balance("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))
				union all 
				select  
				1000001 as id,
				Null::varchar as cuenta,
				'Total' as descripcion,
				sum(debe) as debe,
				sum(haber) as haber,
				sum(saldodeudor) as saldodeudor,
				sum(saldoacredor) as saldoacredor
				from 
				get_hoja_trabajo_simple_balance("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))

				 
			)""")	
		else:
			self.env.cr.execute("""
				
			DROP VIEW IF EXISTS account_sheet_work_simple cascade;
			CREATE OR REPLACE view account_sheet_work_simple as (
				select * from get_hoja_trabajo_simple_registro("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))
				union all 
				select  
				1000001 as id,
				Null::varchar as cuenta,
				'Total' as descripcion,
				sum(debe) as debe,
				sum(haber) as haber,
				sum(saldodeudor) as saldodeudor,
				sum(saldoacredor) as saldoacredor
				from 
				get_hoja_trabajo_simple_registro("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))

				 
			)""")	

		

				
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']

		
		result = mod_obj.get_object_reference('account_sheet_work', 'action_account_sheet_work_simple')
		
		id = result and result[1] or False
		print id
		return {
			'domain' : filtro,
			'type': 'ir.actions.act_window',
			'res_model': 'account.sheet.work.simple',
			'view_mode': 'tree',
			'view_type': 'form',
			'res_id': id,
			'views': [(False, 'tree')],
		}
	