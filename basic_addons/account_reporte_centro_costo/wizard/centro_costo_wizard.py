# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api, _
import codecs
from datetime import *
from odoo.exceptions import UserError, ValidationError


class centro_costo_reporte_wizard(osv.TransientModel):
	_name='centro.costo.reporte.wizard'

	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end = fields.Many2one('account.period','Periodo Final',required=True)
	tipo = fields.Selection((('1','Cuentas de Balance'),
									('2','Etiquetas de las Cuentas')
									),'Nivel',required=True)



	@api.multi
	def do_rebuild(self):
		txt_aaa = ""
		cuentas_analiticas = []
		data = []
		self.env.cr.execute("""
					select distinct aaa.id, aaa.name from account_move_line aml
					inner join account_move am on am.id = aml.move_id
					inner join account_account aa on aa.id = aml.account_id
					inner join account_account aa_dos on aa_dos.id = aa.parent_id
					inner join account_analytic_account aaa on aaa.id = aml.analytic_account_id
					inner join account_period ap on ap.date_start <= am.fecha_contable and ap.date_stop >= am.fecha_contable and ap.special = am.fecha_special
					where periodo_num(ap.code) >= periodo_num('"""+self.period_ini.code+"""') and periodo_num(ap.code) <= periodo_num('"""+self.period_end.code+"""')
					and am.state != 'draft' and (aa_dos.code like '6%' or  aa_dos.code like '7%' ) and (aa_dos.code not like '79%' and aa_dos.code not like '78%')
		""")
		for i in self.env.cr.fetchall():
			cuentas_analiticas.append(i[1])
			txt_aaa += "SUM(CASE WHEN aaa.id = '" + str(i[0]) + "' then debit-credit else 0 end),  "


		if self.tipo == '1':
			self.env.cr.execute("""
						select aa_dos.code, 
						""" +txt_aaa+ """
						sum(CASE WHEN aaa.id is null then debit-credit else 0 end)

						 from account_move_line aml
						inner join account_move am on am.id = aml.move_id
						inner join account_account aa on aa.id = aml.account_id
						inner join account_account aa_dos on aa_dos.id = aa.parent_id
						left join account_analytic_account aaa on aaa.id = aml.analytic_account_id
						inner join account_period ap on ap.date_start <= am.fecha_contable and ap.date_stop >= am.fecha_contable and ap.special = am.fecha_special
						where periodo_num(ap.code) >= periodo_num('"""+self.period_ini.code+"""') and periodo_num(ap.code) <= periodo_num('"""+self.period_end.code+"""')
						and am.state != 'draft' and (aa_dos.code like '6%' or  aa_dos.code like '7%' )  and (aa_dos.code not like '79%' and aa_dos.code not like '78%')
						group by aa_dos.code
			""")

			data = self.env.cr.fetchall()
		else:
			self.env.cr.execute("""
						select aat.name, 
						""" +txt_aaa+ """
						sum(CASE WHEN aaa.id is null then debit-credit else 0 end)

						 from account_move_line aml
						inner join account_move am on am.id = aml.move_id
						inner join account_account aa on aa.id = aml.account_id
						inner join account_account aa_dos on aa_dos.id = aa.parent_id
						left join account_account_account_tag aaat on aaat.account_account_id = aa.id
						inner join account_account_tag aat on aat.id = aaat.account_account_tag_id
						left join account_analytic_account aaa on aaa.id = aml.analytic_account_id
						inner join account_period ap on ap.date_start <= am.fecha_contable and ap.date_stop >= am.fecha_contable and ap.special = am.fecha_special
						where periodo_num(ap.code) >= periodo_num('"""+self.period_ini.code+"""') and periodo_num(ap.code) <= periodo_num('"""+self.period_end.code+"""')
						and am.state != 'draft' and (aa_dos.code like '6%' or  aa_dos.code like '7%' )  and (aa_dos.code not like '79%' and aa_dos.code not like '78%')
						group by aat.name
			""")

			data = self.env.cr.fetchall()

	

		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})

		direccion = self.env['main.parameter'].search([])[0].dir_create_file

		workbook = Workbook(direccion +'tmpCentroCosto.xlsx')
		worksheet = workbook.add_worksheet("Centro costo")

		bold = workbook.add_format({'bold': True})
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		boldbord.set_text_wrap()
		boldbord.set_font_size(9)
		boldbord.set_bg_color('#DCE6F1')
		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		
		numberdosbold = workbook.add_format({'num_format':'0.00','bold': True})
		bord = workbook.add_format()
		bord.set_border(style=1)
		numberdos.set_border(style=1)
		numbertres.set_border(style=1)          
		x= 4
		tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		tam_letra = 1.2
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		worksheet.write(1,0, u"Periodo:", bold)
		worksheet.write(1,1, self.period_ini.name+ ' - '+ self.period_end.name, normal)
		
		worksheet.write(3,0, "Cuenta Balance" if self.tipo == '1' else 'Etiqueta',boldbord)
		yt =1 
		for i in cuentas_analiticas:
			worksheet.write(3,yt, i,boldbord)
			yt+= 1
		worksheet.write(3,yt, "Vacio",boldbord)

		for i in data:
			worksheet.write(x,0, i[0],bord)

			yb =1 
			for ww in cuentas_analiticas:
				worksheet.write(x,yb, i[yb],numberdos)
				yb+= 1
			worksheet.write(x,yb, i[yb],numberdos)

			x = x+1


		tam_col = [18,25,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14]


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
		worksheet.set_column('K:K', tam_col[10])
		worksheet.set_column('L:L', tam_col[11])
		worksheet.set_column('M:M', tam_col[12])
		worksheet.set_column('N:N', tam_col[13])
		worksheet.set_column('O:O', tam_col[14])
		worksheet.set_column('P:P', tam_col[15])
		worksheet.set_column('Q:Q', tam_col[16])
		worksheet.set_column('R:R', tam_col[17])
		worksheet.set_column('S:S', tam_col[18])
		worksheet.set_column('T:T', tam_col[19])

		workbook.close()
		
		f = open(direccion + 'tmpCentroCosto.xlsx', 'rb')
		
		
		sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
		vals = {
			'output_name': 'CentroCosto.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),     
		}

		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		sfs_id = self.env['export.file.save'].create(vals)

		#import os
		#os.system('c:\\eSpeak2\\command_line\\espeak.exe -ves-f1 -s 170 -p 100 "Se Realizo La exportación exitosamente Y A EDWARD NO LE GUSTA XDXDXDXDDDDDDDDDDDD" ')

		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

