# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _
from odoo.exceptions import UserError, ValidationError
from datetime import *

class ple_caja_wizard(osv.TransientModel):
	_name='ple.caja.wizard'

	period = fields.Many2one('account.period','Periodo')

	@api.multi
	def do_rebuild(self):
		direccion = self.env['main.parameter'].search([])[0].dir_create_file

		if not direccion:
			raise osv.except_osv('Alerta!','No esta configurado la dirección de Directorio en Parametros')

		otro_periodo = self.period
		if self.period.code.split('/')[0]== '01':
			otro_periodo = self.env['account.period'].search([('code','=','00/' + self.period.code.split('/')[1])])[0] if self.period.code.split('/')[0]== '01' else self.period
		elif self.period.code.split('/')[0]== '12':
			otro_periodo = ( self.env['account.period'].search([('code','=','13/' + self.period.code.split('/')[1])])[0]  if len( self.env['account.period'].search([('code','=','13/' + self.period.code.split('/')[1])]) )>0 else self.period ) if self.period.code.split('/')[0]== '12' else self.period
		
		self.env.cr.execute("""		
		COPY (	
			SELECT substring(ap.code , 4, 4) || substring(ap.code,0,3 ) || '00' as campo1,

CASE WHEN aj.register_sunat = '1' or aj.register_sunat = '2' THEN 
substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name  || ROW_NUMBER() over( partition by substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name)
ELSE  substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name  || ROW_NUMBER() over( partition by substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name) END
as campo2,

CASE WHEN substring(ap.code,0,3)::text = '00'::text THEN 'A' || T.voucher ELSE
'M' || T.voucher END as campo3,

replace(T.cuenta, '.','') as campo4,
''::varchar as campo5,
''::varchar as campo6,
CASE WHEN rc.id is null THEN 'PEN' else rc.name END as campo7,


datos_gen.tipo_doc as campo8,
datos_gen.nro_serie as campo9,
datos_gen.nro_numero as campo10,


CASE WHEN am.date is null THEN '' ELSE (to_char( am.date::date , 'DD/MM/YYYY'))::varchar END  as campo11,
''::varchar as campo12,
CASE WHEN am.date is null THEN '' ELSE (to_char( am.date::date , 'DD/MM/YYYY'))::varchar END  as campo13,
aml.name as campo14,
''::varchar as campo15,
round(aml.debit,2) as campo16,
round(aml.credit,2) as campo17,
''::varchar as campo18,
am.ple_diariomayor as campo19,
'' as campo20

from get_libro_diario(0,219001) AS T
inner join account_period ap on ap.id = T.ap_id
inner join account_move am on am.id = T.am_id
left join account_invoice ai on ai.move_id = am.id
inner join account_move_line aml on aml.id = T.aml_id
left join einvoice_catalog_01 itd on itd.id = ai.it_type_document
inner join account_journal aj on aj.id = am.journal_id
left join account_period ap2 on ap2.date_start <= am.fecha_modify_ple and ap2.date_stop >= am.fecha_modify_ple and am.fecha_special = ap2.special
left join account_analytic_account aaa on aaa.id = aml.analytic_account_id
left join res_currency rc on aml.currency_id = rc.id
left join res_partner rp on rp.id = aml.partner_id
left join einvoice_catalog_06 itdp on itdp.id = rp.type_document_partner_it
left join res_partner rp_nd on rp_nd.id = ai.beneficiario_de_pagos
inner join account_account aa on aa.id = aml.account_id
left join (
	   select  
	   		am.id, 
	   		CASE WHEN min(aml.nro_comprobante) = max(aml.nro_comprobante) THEN max(et1.code) ELSE '00' END as tipo_doc,
	   		CASE WHEN min(aml.nro_comprobante) = max(aml.nro_comprobante) THEN 
	   				CASE WHEN split_part(max(aml.nro_comprobante) ,'-',2) != ''::text THEN split_part(max(aml.nro_comprobante) ,'-',1) else '' end
	   		ELSE '' END as nro_serie,
	   		CASE WHEN min(aml.nro_comprobante) = max(aml.nro_comprobante) THEN 
	   				CASE WHEN split_part(max(aml.nro_comprobante),'-',2) != ''::text THEN split_part(max(aml.nro_comprobante),'-',2) else split_part(max(aml.nro_comprobante),'-',1) end
	   		ELSE '' END as nro_numero

	   from account_move am
	   inner join account_move_line aml on aml.move_id = am.id
	   left join einvoice_catalog_01 et1 on et1.id = aml.type_document_it
	   inner join account_account aa on aa.id = aml.account_id
	   where aa.code not like '101%' 
	   group by am.id
	) datos_gen on datos_gen.id = am.id
where ( ap.id = """ + str(self.period.id) +""" or ap.id = """ + str(otro_periodo.id) +""" )  or ( ap2.id = """ + str(self.period.id) +""" or ap2.id = """ + str(otro_periodo.id) +""" )
and aa.code like '101%'
)
TO '""" + str( direccion + 'plecaja.csv') + """'
with delimiter '|'
""")

		ruc = self.env['res.company'].search([])[0].partner_id.nro_documento
		mond = self.env['res.company'].search([])[0].currency_id.name

		if not ruc:
			raise osv.except_osv('Alerta!', 'No esta configurado el RUC en la compañia')

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		file_name = 'a.txt'
		
		txt_act = None
		corredor = 1
		exp_r = []
		exp_r = open( str( direccion + 'plecaja.csv' ), 'r').readlines()

		exp = ("".join(exp_r) ).replace('\\N','').replace('|0.0|','|0.00|')
		
		nombre_respec = 'LE' + ruc + self.period.code[3:7]+ self.period.code[:2]+'00010100001' +('1' if len(exp)  >0 else '0') + ('1' if mond == 'PEN' else '2') +'1.txt'

		vals = {
			'output_name': nombre_respec,
			'output_file': base64.encodestring(  "-- Sin Registros --" if exp =="" else exp ),
			'respetar':1,	
		}

		sfs_id = self.env['export.file.save'].create(vals)

		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}







class ple_banco_wizard(osv.TransientModel):
	_name='ple.banco.wizard'

	period = fields.Many2one('account.period','Periodo')

	@api.multi
	def do_rebuild(self):
		direccion = self.env['main.parameter'].search([])[0].dir_create_file

		if not direccion:
			raise osv.except_osv('Alerta!','No esta configurado la dirección de Directorio en Parametros')

		otro_periodo = self.period
		if self.period.code.split('/')[0]== '01':
			otro_periodo = self.env['account.period'].search([('code','=','00/' + self.period.code.split('/')[1])])[0] if self.period.code.split('/')[0]== '01' else self.period
		elif self.period.code.split('/')[0]== '12':
			otro_periodo = ( self.env['account.period'].search([('code','=','13/' + self.period.code.split('/')[1])])[0]  if len( self.env['account.period'].search([('code','=','13/' + self.period.code.split('/')[1])]) )>0 else self.period ) if self.period.code.split('/')[0]== '12' else self.period
		
		self.env.cr.execute("""		
		COPY (	
			SELECT substring(ap.code , 4, 4) || substring(ap.code,0,3 ) || '00' as campo1,

CASE WHEN aj.register_sunat = '1' or aj.register_sunat = '2' THEN 
substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name  || ROW_NUMBER() over( partition by substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name)
ELSE  substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name  || ROW_NUMBER() over( partition by substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name) END
as campo2,

CASE WHEN substring(ap.code,0,3)::text = '00'::text THEN 'A' || T.voucher ELSE
'M' || T.voucher END as campo3,

replace(T.cuenta, '.','') as campo4,
aa.cashbank_financy as campo5,
CASE WHEN am.date is null THEN '' ELSE (to_char( am.date::date , 'DD/MM/YYYY'))::varchar END  as campo6,
emp.code as campo7,
aml.name as campo8,
itdp.code as campo9,
rp.nro_documento as campo10,
rp.name as campo11,
aml.nro_comprobante as campo12,
round(aml.debit,2) as campo13,
round(aml.credit,2) as campo14,
am.ple_diariomayor as campo15,
'' as campo16

from get_libro_diario(0,219001) AS T
inner join account_period ap on ap.id = T.ap_id
inner join account_move am on am.id = T.am_id
left join account_invoice ai on ai.move_id = am.id
inner join account_move_line aml on aml.id = T.aml_id
left join einvoice_catalog_01 itd on itd.id = ai.it_type_document
inner join account_journal aj on aj.id = am.journal_id
left join account_period ap2 on ap2.date_start <= am.fecha_modify_ple and ap2.date_stop >= am.fecha_modify_ple and am.fecha_special = ap2.special
left join account_analytic_account aaa on aaa.id = aml.analytic_account_id
left join res_currency rc on aml.currency_id = rc.id
left join res_partner rp on rp.id = aml.partner_id
left join einvoice_catalog_06 itdp on itdp.id = rp.type_document_partner_it
left join res_partner rp_nd on rp_nd.id = ai.beneficiario_de_pagos
inner join account_account aa on aa.id = aml.account_id
left join einvoice_means_payment emp on emp.id = am.means_payment_it
left join (
	   select  
	   		am.id, 
	   		CASE WHEN min(aml.nro_comprobante) = max(aml.nro_comprobante) THEN max(et1.code) ELSE '00' END as tipo_doc,
	   		CASE WHEN min(aml.nro_comprobante) = max(aml.nro_comprobante) THEN 
	   				CASE WHEN split_part(max(aml.nro_comprobante) ,'-',2) != ''::text THEN split_part(max(aml.nro_comprobante) ,'-',1) else '' end
	   		ELSE '' END as nro_serie,
	   		CASE WHEN min(aml.nro_comprobante) = max(aml.nro_comprobante) THEN 
	   				CASE WHEN split_part(max(aml.nro_comprobante),'-',2) != ''::text THEN split_part(max(aml.nro_comprobante),'-',2) else split_part(max(aml.nro_comprobante),'-',1) end
	   		ELSE '' END as nro_numero

	   from account_move am
	   inner join account_move_line aml on aml.move_id = am.id
	   left join einvoice_catalog_01 et1 on et1.id = aml.type_document_it
	   inner join account_account aa on aa.id = aml.account_id
	   where aa.code not like '104%' 
	   group by am.id
	) datos_gen on datos_gen.id = am.id
where ( ap.id = """ + str(self.period.id) +""" or ap.id = """ + str(otro_periodo.id) +""" )  or ( ap2.id = """ + str(self.period.id) +""" or ap2.id = """ + str(otro_periodo.id) +""" )
and aa.code like '104%'
)
TO '""" + str( direccion + 'plebanco.csv') + """'
with delimiter '|'
""")

		ruc = self.env['res.company'].search([])[0].partner_id.nro_documento
		mond = self.env['res.company'].search([])[0].currency_id.name

		if not ruc:
			raise osv.except_osv('Alerta!', 'No esta configurado el RUC en la compañia')

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		file_name = 'a.txt'
		
		txt_act = None
		corredor = 1
		exp_r = []
		exp_r = open( str( direccion + 'plebanco.csv' ), 'r').readlines()

		exp = ("".join(exp_r) ).replace('\\N','').replace('|0.0|','|0.00|')
		
		nombre_respec = 'LE' + ruc + self.period.code[3:7]+ self.period.code[:2]+'00010200001' +('1' if len(exp)  >0 else '0') + ('1' if mond == 'PEN' else '2') +'1.txt'

		vals = {
			'output_name': nombre_respec,
			'output_file': base64.encodestring(  "-- Sin Registros --" if exp =="" else exp ),
			'respetar':1,	
		}

		sfs_id = self.env['export.file.save'].create(vals)

		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

