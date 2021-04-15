# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv
import base64

class flujo_caja_it(models.Model):
	_name='flujo.caja.it'
	
	codigo = fields.Char('Codigo')
	rubro = fields.Char('Rubro')
	grupo = fields.Char('Grupo')
	orden = fields.Integer('Orden')

	_rec_name = 'codigo'

class account_move_line(models.Model):
	_inherit = 'account.move.line'

	flujo_caja_id = fields.Many2one('flujo.caja.it','Flujo de Caja')

class account_payment(models.Model):
	_inherit = 'account.payment'

	flujo_caja_id = fields.Many2one('flujo.caja.it','Flujo de Caja')



	@api.multi
	def post(self):
		for inv in self:
			super(account_payment,inv).post()
			for i in inv.move_line_ids[0].move_id.line_ids:
				i.flujo_caja_id = inv.flujo_caja_id.id
					

class MultipaymentInvoice(models.Model):
	_inherit='multipayment.invoice'

	flujo_caja_id = fields.Many2one('flujo.caja.it','Flujo de Caja')


	@api.one
	def crear_asiento(self):
		t = super(MultipaymentInvoice,self).crear_asiento()
		self.refresh()
		for i in self.asiento.line_ids:
			i.flujo_caja_id = inv.flujo_caja_id.id
		return t

class MultipaymentadvanceInvoice(models.Model):
	_inherit='multipayment.advance.invoice'

	flujo_caja_id = fields.Many2one('flujo.caja.it','Flujo de Caja')


	@api.one
	def crear_asiento(self):
		t = super(MultipaymentadvanceInvoice,self).crear_asiento()
		self.refresh()
		for i in self.asiento.line_ids:
			i.flujo_caja_id = self.flujo_caja_id.id
		return t

class account_bank_statement_line(models.Model):
	_inherit='account.bank.statement.line'

	flujo_caja_id = fields.Many2one('flujo.caja.it','Flujo de Caja')

	def process_reconciliation(self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None):
		t = super(account_bank_statement_line,self).process_reconciliation(counterpart_aml_dicts, payment_aml_rec, new_aml_dicts)
		for i in t:
			for elem in i.line_ids:
				i.flujo_caja_id = self.flujo_caja_id.id
		return t


class reporte_flujo_caja_wizard(models.Model):
	_name = 'reporte.flujo.caja.wizard'

	@api.model
	def _getCuentas(self):
		self.env.cr.execute(""" select id from account_account where code like '10%' """)
		arrays = []
		for i in self.env.cr.fetchall():
			arrays.append(i[0])
		return [('id','in',arrays)]

	anio_fiscal = fields.Many2one('account.fiscalyear','Año Fiscal')
	cuentas = fields.Many2many('account.account','cuentas_flujo_caja_rel','cuenta_id','flujo_id_reporte','Cuenta', domain=_getCuentas)

	@api.multi
	def do_rebuild(self):
		ctas_txt = [0,0,0,0,0]
		for i in self.cuentas:
			ctas_txt.append(i.id)
		ctas_txt = str(tuple(ctas_txt))
		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})
		direccion = self.env['main.parameter'].search([])[0].dir_create_file

		workbook = Workbook( direccion + 'tempo_account_move_lineflujocaja.xlsx')
		worksheet = workbook.add_worksheet("Reporte Flujo Caja")
		bold = workbook.add_format({'bold': True})
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		numberdosbold = workbook.add_format({'num_format':'0.00','bold':True})
		bord = workbook.add_format()
		bord.set_border(style=1)
		numberdos.set_border(style=1)
		numbertres.set_border(style=1)			
		x= 6				
		tam_col = [12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		tam_letra = 1.1
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		worksheet.merge_range(0,1,0,13, "Flujos de Caja", bold)

		worksheet.write(1,1, "RUC",boldbord)
		worksheet.write(2,1, "Empresa",boldbord)
		worksheet.write(3,1, "Ejercicio Fiscal",boldbord)

		worksheet.write(1,2, self.env['res.company'].search([])[0].partner_id.nro_documento ,boldbord)
		worksheet.write(2,2, self.env['res.company'].search([])[0].partner_id.name ,boldbord)
		worksheet.write(3,2, self.anio_fiscal.name ,boldbord)


		worksheet.write(5,1, "Rubro",boldbord)
		worksheet.write(5,2, "Enero",boldbord)
		worksheet.write(5,3, "Febrero",boldbord)
		worksheet.write(5,4, "Marzo",boldbord)
		worksheet.write(5,5, "Abril",boldbord)
		worksheet.write(5,6, "Mayo",boldbord)
		worksheet.write(5,7, "Junio",boldbord)
		worksheet.write(5,8, "Julio",boldbord)
		worksheet.write(5,9, "Agosto",boldbord)
		worksheet.write(5,10, "Septiembre",boldbord)
		worksheet.write(5,11, "Octubre",boldbord)
		worksheet.write(5,12, "Noviembre",boldbord)
		worksheet.write(5,13, "Diciembre",boldbord)

		meses = ['01/','02/','03/','04/','05/','06/','07/','08/','09/','10/','11/','12/']
		anio = str(self.anio_fiscal.name)

		todos_los_elementos = [['SALDO INICIAL','']]

		y = 1
		x=7
		worksheet.write(6,y, 'Saldo Inicial' ,normal)

		for il in self.env['flujo.caja.it'].search([]).sorted(key=lambda r: r.orden):
			todos_los_elementos.append([il.rubro,il.grupo])
			worksheet.write(x,y, il.rubro ,normal)
			x+=1

		for line in meses:
			x = 6
			y+=1
			all_sum = 0

			for elementos in todos_los_elementos:

				total_line = 0				
				if elementos[0] == 'SALDO INICIAL':
					self.env.cr.execute("""
						select sum(total) from (
						select sum(aml.debit - aml.credit) as total from
						account_move am
						inner join account_move_line aml on aml.move_id = am.id
						LEFT join flujo_caja_it fc on fc.id = aml.flujo_caja_id
						inner join account_account aa on aa.id = aml.account_id
						inner join account_period ap on coalesce(ap.special,false) = coalesce(am.fecha_special,false) and am.fecha_contable >= ap.date_start and am.fecha_contable <= ap.date_stop
						where aa.id in """+str(ctas_txt)+""" and am.state = 'posted'
						and periodo_num(ap.code) = periodo_num('""" + '00/' + anio  + """')

						union all 

						select sum(aml.debit - aml.credit) as total from
						account_move am
						inner join account_move_line aml on aml.move_id = am.id
						inner join flujo_caja_it fc on fc.id = aml.flujo_caja_id
						inner join account_account aa on aa.id = aml.account_id
						inner join account_period ap on coalesce(ap.special,false) = coalesce(am.fecha_special,false) and am.fecha_contable >= ap.date_start and am.fecha_contable <= ap.date_stop
						where aa.id in """+str(ctas_txt)+""" and am.state = 'posted'
						and periodo_num(ap.code) < periodo_num('""" + line + anio  + """') and periodo_num(ap.code) > periodo_num('""" + '00/' + anio  + """')
						)T

						""")
				else:
					self.env.cr.execute("""

						select sum(aml.debit - aml.credit) as total,fc.id, fc.codigo, fc.rubro, fc.grupo, fc.orden, sum(aml.debit - aml.credit) as total from
						account_move am
						inner join account_move_line aml on aml.move_id = am.id
						inner join flujo_caja_it fc on fc.id = aml.flujo_caja_id
						inner join account_account aa on aa.id = aml.account_id
						inner join account_period ap on coalesce(ap.special,false) = coalesce(am.fecha_special,false) and am.fecha_contable >= ap.date_start and am.fecha_contable <= ap.date_stop
						where aa.id in """+str(ctas_txt)+""" and am.state = 'posted'
						and ap.code = '""" + line + anio  + """' and fc.rubro = '""" + elementos[0] +"""'
						group by fc.id, fc.codigo, fc.rubro, fc.grupo, fc.orden
						order by orden
						""")
				element = self.env.cr.fetchall()
				for gg_ele in element:
					total_line = gg_ele[0] if gg_ele[0] else 0

				all_sum += total_line

				worksheet.write(x,y, total_line ,numberdos)
				x = x +1
			
			worksheet.write(x,y, all_sum ,numberdosbold)

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
		
		f = open( direccion + 'tempo_account_move_lineflujocaja.xlsx', 'rb')
		
		vals = {
			'output_name': 'FlujoCaja.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		sfs_id = self.env['export.file.save'].create(vals)

		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    "views": [[False, "form"]],
		    "res_id": sfs_id.id,
		    "target": "new",
		}
