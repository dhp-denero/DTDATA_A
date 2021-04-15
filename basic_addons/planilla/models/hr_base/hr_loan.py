from odoo import api, fields, models, tools, _
import calendar
from datetime import *
from decimal import *
from dateutil.relativedelta import relativedelta
import base64
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT

class HrLoan(models.Model):
	_name = 'hr.loan'

	employee_id = fields.Many2one('hr.employee','Empleado')
	date = fields.Date('Fecha de Prestamo')
	amount = fields.Float('Monto de Prestamo')
	loan_type_id = fields.Many2one('hr.loan.type','Tipo de Prestamo')
	fees_number = fields.Integer('Numero de Cuotas')
	line_ids = fields.One2many('hr.loan.line','loan_id')
	observations = fields.Text('Observaciones')

	@api.multi
	def get_fees(self):
		self.line_ids.unlink()
		date = datetime.strptime(self.date,'%Y-%m-%d')
		debt = self.amount
		for c,fee in enumerate(range(self.fees_number),1):
			first_day,last_day = calendar.monthrange(date.year,date.month)
			if c == 1 and date.day == last_day:
				date = date + relativedelta(months=1)
			if c != 1:
				date = date + relativedelta(months=1)
			first_day,last_day = calendar.monthrange(date.year,date.month)
			date = date.replace(day=last_day)
			fee_amount = float(Decimal(str(self.amount/self.fees_number)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
			debt -= fee_amount
			self.env['hr.loan.line'].create({
					'loan_id':self.id,
					'employee_id':self.employee_id.id,
					'input_id':self.loan_type_id.input_id.id,
					'fee':c,
					'amount':fee_amount,
					'date':date,
					'debt':debt
				})
		return {}

	@api.multi
	def refresh_fees(self):
		total = self.amount
		for line in self.line_ids.sorted(lambda l:l.fee):
			total -= line.amount
			line.debt = total
		self.fees_number = len(self.line_ids)

	@api.multi
	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook

		try:
			direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except: 
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		workbook = Workbook(direccion +'prestamos.xlsx')

		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		boldbord.set_text_wrap()
		boldbord.set_font_size(10)
		boldbord.set_bg_color('#DCE6F1')
		boldbord.set_font_name('Times New Roman')

		especial1 = workbook.add_format()
		especial1.set_align('center')
		especial1.set_align('vcenter')
		especial1.set_border(style=1)
		especial1.set_text_wrap()
		especial1.set_font_size(10)
		especial1.set_font_name('Times New Roman')

		especial3 = workbook.add_format({'bold': True})
		especial3.set_align('center')
		especial3.set_align('vcenter')
		especial3.set_border(style=1)
		especial3.set_text_wrap()
		especial3.set_bg_color('#DCE6F1')
		especial3.set_font_size(15)
		especial3.set_font_name('Times New Roman')

		numberdos = workbook.add_format({'num_format':'0'})
		numberdos.set_border(style=1)
		numberdos.set_font_size(10)
		numberdos.set_font_name('Times New Roman')

		dateformat = workbook.add_format({'num_format':'d-m-yyyy'})
		dateformat.set_border(style=1)
		dateformat.set_font_size(10)
		dateformat.set_font_name('Times New Roman')

		hourformat = workbook.add_format({'num_format':'hh:mm'})
		hourformat.set_align('center')
		hourformat.set_align('vcenter')
		hourformat.set_border(style=1)
		hourformat.set_font_size(10)
		hourformat.set_font_name('Times New Roman')

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		##########ASISTENCIAS############
		worksheet = workbook.add_worksheet("PRESTAMOS")
		worksheet.set_tab_color('blue')

		worksheet.merge_range(1,0,1,4,"PRESTAMO %s %s"%(self.employee_id.name_related,self.date), especial3)
		worksheet.write(3,0,"Empleado",boldbord)
		worksheet.merge_range(3,1,3,2,self.employee_id.name_related,especial1)
		worksheet.write(3,3,"Fecha de Prestamo",boldbord)
		worksheet.write(3,4,self.date,especial1)
		worksheet.write(5,0,"Tipo de Prestamo",boldbord)
		worksheet.merge_range(5,1,5,2,self.loan_type_id.name,especial1)
		worksheet.write(5,3,"Numero de Cuotas",boldbord)
		worksheet.write(5,4,self.fees_number,especial1)

		x = 7
		worksheet.write(x,0,"CUOTA",boldbord)
		worksheet.write(x,1,"MONTO",boldbord)
		worksheet.write(x,2,"FECHA DE PAGO",boldbord)
		worksheet.write(x,3,"DEUDA POR PAGAR",boldbord)
		worksheet.write(x,4,"VALIDACION",boldbord)
		x=8

		for line in self.line_ids:
			worksheet.write(x,0,line.fee if line.fee else 0,numberdos)
			worksheet.write(x,1,line.amount if line.amount else 0,numberdos)
			worksheet.write(x,2,line.date if line.date else '',especial1)
			worksheet.write(x,3,line.debt if line.debt else 0,numberdos)
			worksheet.write(x,4,dict(line._fields['validation'].selection).get(line.validation) if line.validation else '',especial1)
			x += 1

		tam_col = [12,12,12,12,12,12]

		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])

		workbook.close()

		f = open(direccion + 'prestamos.xlsx', 'rb')
		
		vals = {
			'output_name': 'Prestamo - %s.xlsx'%(self.date),
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

	@api.multi
	def get_pdf(self):
		try:
			direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except: 
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		doc = SimpleDocTemplate(direccion + 'prestamos.pdf',pagesize=letter)
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=14, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		
		try:
			logo = open(direccion+"logo.jpg","rb")
			c = Image(logo,2*inch,0.5*inch)
		except Exception as e:
			c = ''
			print("No se encontro el logo en la ruta "+ str(direccion) +" Inserte una imagen del logo en la ruta especificada con el nombre 'logo.jpg'")
		finally:
			data = [[c,'','','','','','','']]

			t = Table(data, style=[
				('ALIGN', (0, 0), (-1, -1), 'CENTER')
			],hAlign='LEFT')
			t._argW[0] = 1.5*inch
			elements.append(t)

		elements.append(Paragraph("PRESTAMO %s - %s"%(self.employee_id.name_related,self.date),style_title))
		elements.append(Spacer(10, 20))

		data = [[Paragraph('EMPLEADO',style_cell),Paragraph(self.employee_id.name_related,style_cell),'',''],
				[Paragraph('FECHA PRESTAMO',style_cell),Paragraph(self.date,style_cell),
				Paragraph('NUMERO CUOTAS',style_cell),Paragraph(str(self.fees_number),style_cell),
				]]
		t = Table(data,4*[1.4*inch],2*[0.4*inch])
		t.setStyle(TableStyle([
						('SPAN',(1,0),(3,0)),
						('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
			]))
		elements.append(t)

		elements.append(Spacer(10, 20))

		data = [[Paragraph('CUOTA',style_cell),
				Paragraph('MONTO',style_cell),
				Paragraph('FECHA DE PAGO',style_cell),
				Paragraph('DEUDA POR PAGAR',style_cell),
				Paragraph('VALIDACION',style_cell)],
				]
		y = 1
		for line in self.line_ids:
			data.append([Paragraph(str(line.fee) if line.fee else '',style_cell),
						Paragraph(str(line.amount) if line.amount else '0',style_cell),
						Paragraph(line.date if line.date else '',style_cell),
						Paragraph(str(line.debt) if line.debt else '0',style_cell),
						Paragraph(dict(line._fields['validation'].selection).get(line.validation) if line.validation else '',style_cell),])
			y += 1
		t = Table(data,[0.8*inch,1.0*inch,1.4*inch,1.4*inch,1.4*inch],y*[0.3*inch])
		t.setStyle(TableStyle([
							('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4C5CF9")),
							('ALIGN', (0, 0), (-1, -1), 'CENTER'),
							('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
							('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
							('BOX', (0, 0), (-1, -1), 0.25, colors.black),
							]))
		elements.append(t)

		try:
			firma_digital = open(direccion+"firma.jpg","rb")
			c = Image(firma_digital,2*inch,1*inch)
		except Exception as e:
			c = ''
			print("No se encontro la firma en la ruta "+ direccion +" Inserte una imagen de la firma en la ruta especificada con el nombre 'firma.jpg'")
		finally:
			data = [
				[' ', ' ',  ' ', ' ', ' ', ' ', ' ', ' ', ' '],
				[' ', ' ',  ' ', ' ', ' ', ' ', ' ', ' ', ' '],
				[' ', ' ',  ' ', ' ', ' ', ' ', ' ', c , ' '],
				['  ', 'FIRMA TRABAJADOR', ' ', '  ', ' ',
				 ' ', '  ', 'FIRMA EMPLEADOR', '  ']
			]

			t = Table(data, style=[
				('ALIGN', (0, 0), (-1, -1), 'CENTER'),
				('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),

				('LINEABOVE', (0, -1), (2, -1), 1, colors.black),
				('LINEABOVE', (6, -1), (8, -1), 1, colors.black),
			])
			t._argW[3] = 1.5*inch
			elements.append(t)

		doc.build(elements)

		vals = {
			'output_name': "Prestamo %s - %s.pdf"%(self.employee_id.name_related,self.date),
			'output_file': open(direccion + "prestamos.pdf", "rb").read().encode("base64"),
		}
		sfs_id = self.env['planilla.export.file'].create(vals)
		return {
			"type": "ir.actions.act_window",
			"res_model": "planilla.export.file",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

class HrLoanType(models.Model):
	_name = 'hr.loan.type'

	name = fields.Char('Nombre')
	input_id = fields.Many2one('planilla.inputs.nomina','Input')

class HrLoanLine(models.Model):
	_name = 'hr.loan.line'

	loan_id = fields.Many2one('hr.loan', ondelete='cascade')
	employee_id = fields.Many2one('hr.employee')
	input_id = fields.Many2one('planilla.inputs.nomina')
	fee = fields.Integer('Cuota')
	amount = fields.Float('Monto')
	date = fields.Date('Fecha de Pago')
	debt = fields.Float('Deuda por Pagar')
	validation = fields.Selection([('not payed','NO PAGADO'),('paid out','PAGADO')],'Validacion',default='not payed')