# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv
import base64

class account_rat(models.Model):
	_name='account.rat'
	
	tipo = fields.Char('Tipo')
	ratio = fields.Char('Ratio')
	formula = fields.Char('Formula', help="Caracteres permitidos: + - * / y parentesis")

	@api.multi
	def crear_wizard(self):
		return {
            'name': 'Generar Reporte Ratio Financiero',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'account.rat.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class account_rat_wizard(models.Model):
	_name = 'account.rat.wizard'

	fecha_inicio = fields.Date('Fecha Inicio')
	fecha_final = fields.Date('Fecha Final')

	@api.multi
	def do_rebuild(self):
		self.env.cr.execute("""

select a1.id,a1.code,a1.name,coalesce(sum(a3.debit-a3.credit),'0.00') from account_account_type_it a1
left join account_account a2 on a2.type_it=a1.id
left join 
(select mov1.account_id,mov1.debit,mov1.credit from account_move_line mov1
 left join account_move mov2 on mov2.id=mov1.move_id
where mov2.fecha_contable  BETWEEN  '"""+str(self.fecha_inicio)+"""' AND '"""+str(self.fecha_final)+"""'  and (state='posted')) a3 on a3.account_id=a2.id 
group by a1.id,a1.code,a1.name
order by a1.id 
			""")

		element = self.env.cr.fetchall()
		todos = {}
		reglas = []
		for i in element:
			todos[i[1]] = i[3]
			reglas.append(i[1])


		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})
		direccion = self.env['main.parameter'].search([])[0].dir_create_file

		workbook = Workbook( direccion + 'tempo_account_move_line.xlsx')
		worksheet = workbook.add_worksheet("Ratios Financieros")
		bold = workbook.add_format({'bold': True})
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
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

		worksheet.write(0,0, "Razon Social:", bold)

		worksheet.write(0,1, self.env['res.company'].search([])[0].partner_id.name , normal)

		worksheet.write(1,0, "RUC:", bold)

		worksheet.write(1,1, self.env['res.company'].search([])[0].partner_id.nro_documento , normal)
	
	
		worksheet.write(2,0, "Fecha Inicial:",bold)
		
		worksheet.write(2,1, self.fecha_inicio, normal)
		

		worksheet.write(3,0, "Fecha Final:", bold)
		
		worksheet.write(3,1, self.fecha_final, normal)
		




		worksheet.write(5,1, "Tipo",boldbord)
		worksheet.write(5,2, "Ratio",boldbord)
		worksheet.write(5,3, "Formula",boldbord)
		worksheet.write(5,4, "Valor",boldbord)

		for line in self.env['account.rat'].search([]):
			worksheet.write(x,1,line.tipo if line.tipo  else '',bord )
			worksheet.write(x,2,line.ratio if line.ratio  else '',bord)
			worksheet.write(x,3,line.formula if line.formula  else '',bord)
			txt_for = line.formula
			for palabra in reglas:
				txt_for = txt_for.replace(palabra,str(todos[palabra]))

			worksheet.write(x,4, eval(txt_for) ,numberdos)

			x = x +1

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
		
		f = open( direccion + 'tempo_account_move_line.xlsx', 'rb')
		
		vals = {
			'output_name': 'AsientoContable.xlsx',
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
