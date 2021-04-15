from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from decimal import *
from datetime import *
import base64

class HrProvisiones(models.Model):
	_name = 'hr.provisiones'

	periodo_id = fields.Many2one('account.period','Periodo')
	gratificacion_id = fields.Many2one('planilla.gratificacion','Gratificacion')
	asiento_contable = fields.Many2one('account.move','Asiento Contable')
	cts_debe = fields.Many2one('account.account')
	cts_haber = fields.Many2one('account.account')
	grati_debe = fields.Many2one('account.account')
	grati_haber = fields.Many2one('account.account')
	boni_debe = fields.Many2one('account.account')
	boni_haber = fields.Many2one('account.account')
	vaca_debe = fields.Many2one('account.account')
	vaca_haber = fields.Many2one('account.account')
	cts_lines = fields.One2many('hr.provisiones.cts.line','provision_id')
	grati_lines = fields.One2many('hr.provisiones.grati.line','provision_id')
	vaca_lines = fields.One2many('hr.provisiones.vaca.line','provision_id')

	@api.multi
	def actualizar(self):
		if self.cts_lines:
			self.env['hr.provisiones.cts.line'].search([('provision_id','=',self.id)]).unlink()
		if self.grati_lines:
			self.env['hr.provisiones.grati.line'].search([('provision_id','=',self.id)]).unlink()
		if self.vaca_lines:
			self.env['hr.provisiones.vaca.line'].search([('provision_id','=',self.id)]).unlink()

		employees = self.env['hr.employee'].search([])
		grati = self.env['planilla.gratificacion'].browse(self.gratificacion_id.id)
		for employee in employees:
			sql = """
				select 
				max(hc.id) as contract_id,
				max(hc.date_start) as date_start,
				sum(hpl.total) as total,
				max(pss.porcentaje) as porcentaje
				from hr_payslip hp
				inner join hr_payslip_line hpl on hpl.slip_id = hp.id
				inner join hr_contract hc on hc.id = hp.contract_id
				left join planilla_seguro_salud pss on pss.id = hc.seguro_salud_id
				where hp.employee_id = %d
				and hp.date_from = '%s'
				and hp.date_to = '%s'
				and hc.regimen_laboral_empresa not in ('practicante','microempresa')
				and hpl.code = 'BAS'
				group by hp.employee_id
			"""%(employee.id,self.periodo_id.date_start,self.periodo_id.date_stop)
			self.env.cr.execute(sql)
			data = self.env.cr.dictfetchall()
			payslips = self.env['hr.payslip'].search([('employee_id','=',employee.id),('date_from','=',self.periodo_id.date_start),('date_to','=',self.periodo_id.date_stop)])
			if payslips:
				for payslip in data:
					line = filter(lambda line: line.employee_id.id == employee.id ,grati.planilla_gratificacion_lines)
					self.env['hr.provisiones.cts.line'].create({
							'provision_id':self.id,
							'nro_doc':employee.identification_id,
							'employee_id':employee.id,
							'contract_id':payslip['contract_id'],
							'fecha_ingreso':payslip['date_start'],
							'basico': self.env['hr.contract'].browse(payslip['contract_id']).wage,
							'asignacion':93.00 if employee.children > 0 else 0,
							'un_sexto_grati': float(Decimal(str(line[0].total_gratificacion/6)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)) if len(line)>0 else 0
						})
					self.env['hr.provisiones.grati.line'].create({
							'provision_id':self.id,
							'nro_doc':employee.identification_id,
							'employee_id':employee.id,
							'contract_id':payslip['contract_id'],
							'fecha_ingreso':payslip['date_start'],
							'basico': self.env['hr.contract'].browse(payslip['contract_id']).wage,
							'asignacion':93.00 if employee.children > 0 else 0,
							'tasa':payslip['porcentaje']
						})
					self.env['hr.provisiones.vaca.line'].create({
							'provision_id':self.id,
							'nro_doc':employee.identification_id,
							'employee_id':employee.id,
							'contract_id':payslip['contract_id'],
							'fecha_ingreso':payslip['date_start'],
							'basico': self.env['hr.contract'].browse(payslip['contract_id']).wage,
							'asignacion':93.00 if employee.children > 0 else 0
						})
		return self.env['planilla.warning'].info(title='Resultado', message="Se actualizo de manera correcta")
	
	@api.multi
	def generar_asiento(self):
		if self.asiento_contable:
			self.asiento_contable.button_cancel()
			self.asiento_contable.unlink()

		ajustes = self.env['planilla.ajustes'].search([],limit=1)
		if not ajustes.diario_provisiones:
			raise UserError('No se ha configurado diario para Provisiones en el Menu Parametros Boleta de Pago')
		else:
			diario = ajustes.diario_provisiones
		t = self.env['account.move'].create({
				'journal_id':diario.id,
				'date':datetime.now(),
				'ref':'Provision - '+self.periodo_id.name
			})
		montos = []
		for line in self.cts_lines:
			for cal in line.contract_id.distribucion_analitica_id.cuenta_analitica_lines:
				if not any(i.get('cuenta',None) == cal.cuenta_analitica_id.id for i in montos):
					montos.append({'cuenta':cal.cuenta_analitica_id.id,'monto':float(Decimal(str((line.provisiones_cts * cal.porcentaje)/100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))})
				else:
					for i in montos: 
						if i['cuenta'] == cal.cuenta_analitica_id.id:
							i['monto'] = float(Decimal(str(i['monto'] + ((line.provisiones_cts * cal.porcentaje)/100))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
		
		montos_grati = []
		for line in self.grati_lines:
			for cal in line.contract_id.distribucion_analitica_id.cuenta_analitica_lines:
				if not any(i.get('cuenta',None) == cal.cuenta_analitica_id.id for i in montos_grati):
					montos_grati.append({'cuenta':cal.cuenta_analitica_id.id,'monto':float(Decimal(str((line.provisiones_grati * cal.porcentaje)/100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))})
				else:
					for i in montos_grati:
						if i['cuenta'] == cal.cuenta_analitica_id.id:
							i['monto'] = float(Decimal(str(i['monto'] + ((line.provisiones_grati * cal.porcentaje)/100))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

		montos_boni = []
		for line in self.grati_lines:
			for cal in line.contract_id.distribucion_analitica_id.cuenta_analitica_lines:
				if not any(i.get('cuenta',None) == cal.cuenta_analitica_id.id for i in montos_boni):
					montos_boni.append({'cuenta':cal.cuenta_analitica_id.id,'monto':float(Decimal(str((line.boni_grati * cal.porcentaje)/100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))})
				else:
					for i in montos_boni:
						if i['cuenta'] == cal.cuenta_analitica_id.id:
							i['monto'] = float(Decimal(str(i['monto'] + ((line.boni_grati * cal.porcentaje)/100))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

		montos_vaca = []
		for line in self.vaca_lines:
			for cal in line.contract_id.distribucion_analitica_id.cuenta_analitica_lines:
				if not any(i.get('cuenta',None) == cal.cuenta_analitica_id.id for i in montos_vaca):
					montos_vaca.append({'cuenta':cal.cuenta_analitica_id.id,'monto':float(Decimal(str((line.provisiones_vaca * cal.porcentaje)/100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))})
				else:
					for i in montos_vaca:
						if i['cuenta'] == cal.cuenta_analitica_id.id:
							i['monto'] = float(Decimal(str(i['monto'] + ((line.provisiones_vaca * cal.porcentaje)/100))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

		credit = 0
		for monto in montos:
			self.env['account.move.line'].create({
					'account_id':self.cts_debe.id,
					'analytic_account_id':monto['cuenta'],
					'debit':monto['monto'],
					'credit':0,
					'name':'Provision - '+self.periodo_id.name,
					'move_id':t.id
				})
			credit += monto['monto']

		credit_grati = 0
		for monto_grati in montos_grati:
			self.env['account.move.line'].create({
					'account_id':self.grati_debe.id,
					'analytic_account_id':monto_grati['cuenta'],
					'debit':monto_grati['monto'],
					'credit':0,
					'name':'Provision - '+self.periodo_id.name,
					'move_id':t.id
				})
			credit_grati += monto_grati['monto']

		credit_boni = 0
		for monto_boni in montos_boni:
			self.env['account.move.line'].create({
					'account_id':self.boni_debe.id,
					'analytic_account_id':monto_boni['cuenta'],
					'debit':monto_boni['monto'],
					'credit':0,
					'name':'Provision - '+self.periodo_id.name,
					'move_id':t.id
				})
			credit_boni += monto_boni['monto']

		credit_vaca = 0
		for monto_vaca in montos_vaca:
			self.env['account.move.line'].create({
					'account_id':self.vaca_debe.id,
					'analytic_account_id':monto_vaca['cuenta'],
					'debit':monto_vaca['monto'],
					'credit':0,
					'name':'Provision - '+self.periodo_id.name,
					'move_id':t.id
				})
			credit_vaca += monto_vaca['monto']
		c = 0
		for line in self.cts_lines:
			c += line.provisiones_cts
			self.env['account.move.line'].create({
					'account_id':self.cts_haber.id,
					'debit':0,
					'credit':line.provisiones_cts,
					'name':'Provision - '+self.periodo_id.name,
					'move_id':t.id,
					'partner_id':line.employee_id.address_home_id.id if line.employee_id.address_home_id else 0,
					'nro_comprobante':line.employee_id.address_home_id.nro_documento if line.employee_id.address_home_id else ''
				})
		print('c',c)
		for line in self.grati_lines:
			c += line.provisiones_grati
			self.env['account.move.line'].create({
					'account_id':self.grati_haber.id,
					'debit':0,
					'credit':line.provisiones_grati,
					'name':'Provision - '+self.periodo_id.name,
					'move_id':t.id,
					'partner_id':line.employee_id.address_home_id.id if line.employee_id.address_home_id else 0,
					'nro_comprobante':line.employee_id.address_home_id.nro_documento if line.employee_id.address_home_id else ''
				})
		print('g',c)
		for line in self.grati_lines:
			c += line.boni_grati
			self.env['account.move.line'].create({
					'account_id':self.boni_haber.id,
					'debit':0,
					'credit':line.boni_grati,
					'name':'Provision - '+self.periodo_id.name,
					'move_id':t.id,
					'partner_id':line.employee_id.address_home_id.id if line.employee_id.address_home_id else 0,
					'nro_comprobante':line.employee_id.address_home_id.nro_documento if line.employee_id.address_home_id else ''
				})
		print('b',c)
		for line in self.vaca_lines:
			c += line.provisiones_vaca 
			self.env['account.move.line'].create({
					'account_id':self.vaca_haber.id,
					'debit':0,
					'credit':line.provisiones_vaca,
					'name':'Provision - '+self.periodo_id.name,
					'move_id':t.id,
					'partner_id':line.employee_id.address_home_id.id if line.employee_id.address_home_id else 0,
					'nro_comprobante':line.employee_id.address_home_id.nro_documento if line.employee_id.address_home_id else ''
				})
		print('v',c)
		
		self.asiento_contable = t.id
		return {}

	@api.multi
	def get_provisiones_excel(self):
		import io
		from xlsxwriter.workbook import Workbook

		try:
			direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except: 
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		workbook = Workbook(direccion +'provisiones.xlsx')

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

		numberdos = workbook.add_format({'num_format':'0.00'})
		numberdos.set_border(style=1)
		numberdos.set_font_size(10)
		numberdos.set_font_name('Times New Roman')

		dateformat = workbook.add_format({'num_format':'d-m-yyyy'})
		dateformat.set_border(style=1)
		dateformat.set_font_size(10)
		dateformat.set_font_name('Times New Roman')

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		##########CTS############
		worksheet = workbook.add_worksheet("CTS")
		worksheet.set_tab_color('blue')

		worksheet.merge_range(1,0,1,7, "PROVISIONES-CTS", especial3)
		worksheet.write(3,0,"Periodo",boldbord)
		worksheet.write(3,1,self.periodo_id.name,especial1)

		x = 5
		worksheet.write(x,0,"NUMERO DE DOCUMENTO",boldbord)
		worksheet.write(x,1,"EMPLEADO",boldbord)
		worksheet.write(x,2,"FECHA INGRESO",boldbord)
		worksheet.write(x,3,"REMUNERACION BASICA",boldbord)
		worksheet.write(x,4,"ASIGNACION FAMILIAR",boldbord)
		worksheet.write(x,5,"1/6 GRATIFICACION",boldbord)
		worksheet.write(x,6,"PROVISIONES CTS",boldbord)
		worksheet.write(x,7,"TOTAL CTS ADIC.",boldbord)
		x=6

		for line in self.cts_lines:
			worksheet.write(x,0,line.nro_doc if line.nro_doc else '',especial1)
			worksheet.write(x,1,line.employee_id.name_related if line.employee_id else '',especial1)
			worksheet.write(x,2,line.fecha_ingreso if line.fecha_ingreso else '',dateformat)
			worksheet.write(x,3,line.basico if line.basico else 0,numberdos)
			worksheet.write(x,4,line.asignacion if line.asignacion else 0,numberdos)
			worksheet.write(x,5,line.un_sexto_grati if line.un_sexto_grati else 0,numberdos)
			worksheet.write(x,6,line.provisiones_cts if line.provisiones_cts else 0,numberdos)
			worksheet.write(x,7,line.total_cts if line.total_cts else 0,numberdos)
			x += 1

		tam_col = [12,38,13,16,13,15,13,11]

		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])
		worksheet.set_column('G:G', tam_col[6])
		worksheet.set_column('H:H', tam_col[7])

		##########GRATIFICACION############
		worksheet = workbook.add_worksheet("GRATIFICACION")
		worksheet.set_tab_color('green')

		worksheet.merge_range(1,0,1,8, "PROVISIONES-GRATIFICACION", especial3)
		worksheet.write(3,0,"Periodo",boldbord)
		worksheet.write(3,1,self.periodo_id.name,especial1)

		x = 5
		worksheet.write(x,0,"NUMERO DE DOCUMENTO",boldbord)
		worksheet.write(x,1,"EMPLEADO",boldbord)
		worksheet.write(x,2,"FECHA INGRESO",boldbord)
		worksheet.write(x,3,"REMUNERACION BASICA",boldbord)
		worksheet.write(x,4,"ASIGNACION FAMILIAR",boldbord)
		worksheet.write(x,5,"PROVISIONES GRATIFICACION",boldbord)
		worksheet.write(x,6,"BONIFICACION DE GRATIFICACION",boldbord)
		worksheet.write(x,7,"TOTAL",boldbord)
		worksheet.write(x,8,"TOTAL GRATIFICACION ADIC.",boldbord)
		x=6

		for line in self.grati_lines:
			worksheet.write(x,0,line.nro_doc if line.nro_doc else '',especial1)
			worksheet.write(x,1,line.employee_id.name_related if line.employee_id else '',especial1)
			worksheet.write(x,2,line.fecha_ingreso if line.fecha_ingreso else '',dateformat)
			worksheet.write(x,3,line.basico if line.basico else 0,numberdos)
			worksheet.write(x,4,line.asignacion if line.asignacion else 0,numberdos)
			worksheet.write(x,5,line.provisiones_grati if line.provisiones_grati else 0,numberdos)
			worksheet.write(x,6,line.boni_grati if line.boni_grati else 0,numberdos)
			worksheet.write(x,7,line.total if line.total else 0,numberdos)
			worksheet.write(x,8,line.total_grati if line.total_grati else 0,numberdos)
			x += 1

		tam_col = [12,38,13,15,13,15,16,11,15]

		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])
		worksheet.set_column('G:G', tam_col[6])
		worksheet.set_column('H:H', tam_col[7])
		worksheet.set_column('I:I', tam_col[8])

		##########VACACIONES############
		worksheet = workbook.add_worksheet("VACACIONES")
		worksheet.set_tab_color('orange')

		worksheet.merge_range(1,0,1,6, "PROVISIONES-VACACIONES", especial3)
		worksheet.write(3,0,"Periodo",boldbord)
		worksheet.write(3,1,self.periodo_id.name,especial1)

		x = 5
		worksheet.write(x,0,"NUMERO DE DOCUMENTO",boldbord)
		worksheet.write(x,1,"EMPLEADO",boldbord)
		worksheet.write(x,2,"FECHA INGRESO",boldbord)
		worksheet.write(x,3,"REMUNERACION BASICA",boldbord)
		worksheet.write(x,4,"ASIGNACION FAMILIAR",boldbord)
		worksheet.write(x,5,"PROVISIONES VACACIONES",boldbord)
		worksheet.write(x,6,"TOTAL VACACIONES ADIC.",boldbord)
		x=6

		for line in self.vaca_lines:
			worksheet.write(x,0,line.nro_doc if line.nro_doc else '',especial1)
			worksheet.write(x,1,line.employee_id.name_related if line.employee_id else '',especial1)
			worksheet.write(x,2,line.fecha_ingreso if line.fecha_ingreso else '',dateformat)
			worksheet.write(x,3,line.basico if line.basico else 0,numberdos)
			worksheet.write(x,4,line.asignacion if line.asignacion else 0,numberdos)
			worksheet.write(x,5,line.provisiones_vaca if line.provisiones_vaca else 0,numberdos)
			worksheet.write(x,6,line.total_vaca if line.total_vaca else 0,numberdos)
			x += 1

		tam_col = [12,38,13,15,13,13,12]

		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])
		worksheet.set_column('G:G', tam_col[6])

		workbook.close()

		f = open(direccion + 'provisiones.xlsx', 'rb')
		
		vals = {
			'output_name': 'Provisiones - %s.xlsx'%(self.periodo_id.name),
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
	def unlink(self):
		for i in self.ids:
			self.env['hr.provisiones.cts.line'].search([('provision_id','=',i)]).unlink()
			self.env['hr.provisiones.grati.line'].search([('provision_id','=',i)]).unlink()
			self.env['hr.provisiones.vaca.line'].search([('provision_id','=',i)]).unlink()
		return super(HrProvisiones,self).unlink()

class HrProvisionesCtsLine(models.Model):
	_name = 'hr.provisiones.cts.line'

	provision_id = fields.Many2one('hr.provisiones')
	nro_doc = fields.Char('Numero de Documento')
	employee_id = fields.Many2one('hr.employee','Empleado')
	contract_id = fields.Many2one('hr.contract','Contrato')
	fecha_ingreso = fields.Date('Fecha Ingreso')
	basico = fields.Float('Remuneracion Basica')
	asignacion = fields.Float('Asignacion Familiar')
	un_sexto_grati = fields.Float('1/6 Gratificacion')

	@api.one
	@api.depends('basico','asignacion','un_sexto_grati','total_cts')
	def _get_prov_cts(self):
		#total = (self.basico + self.asignacion + self.un_sexto_grati + self.total_cts)/12
		self.provisiones_cts = float(Decimal(str((self.basico + self.asignacion + self.un_sexto_grati + self.total_cts)/12)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

	provisiones_cts = fields.Float('Provisiones CTS',compute="_get_prov_cts")
	total_cts = fields.Float('Total CTS Adic.')

	@api.multi
	def get_wizard(self):
		return self.env['cts.line.wizard'].get_wizard(self.employee_id.id,self.provision_id.id,self.id)

	@api.multi
	def unlink(self):
		for i in self.ids:
			self.env['cts.line.wizard'].search([('line_id','=',i)]).unlink()
		return super(HrProvisionesCtsLine,self).unlink()

class CtsLineWizard(models.Model):
	_name = 'cts.line.wizard'

	conceptos_lines = fields.One2many('cts.conceptos','cts_line_id')
	employee_id = fields.Many2one('hr.employee')
	provision_id = fields.Many2one('hr.provisiones')
	line_id = fields.Many2one('hr.provisiones.cts.line')

	@api.multi
	def get_wizard(self,employee_id,provision_id,line_id):
		res_id = self.env['cts.line.wizard'].search([('line_id','=',line_id)],limit=1)
		res_id = res_id.id if res_id else self.id
		return {
			'name':_('Conceptos Adicionales'),
			'type':'ir.actions.act_window',
			'res_id':res_id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'cts.line.wizard',
			'views':[[self.env.ref('planilla.cts_line_wizard').id,'form']],
			'target':'new',
			'context':{
				'default_employee_id':employee_id,
				'default_provision_id':provision_id,
				'default_line_id':line_id
			}
		}

	@api.multi
	def add_concept(self):
		total = 0
		if self.conceptos_lines:
			for line in self.conceptos_lines:
				total += line.monto
			self.env['hr.provisiones.cts.line'].browse(self.line_id.id).write({'total_cts':total})
		else:
			self.env['hr.provisiones.cts.line'].browse(self.line_id.id).write({'total_cts':0}) 
		return self.env['hr.provisiones'].browse(self.provision_id.id).cts_lines.refresh()

	@api.multi
	def unlink(self):
		for i in self.ids:
			self.env['cts.conceptos'].search([('cts_line_id','=',i)]).unlink()
		return super(CtsLineWizard,self).unlink()

class CtsConceptos(models.Model):
	_name = 'cts.conceptos'
	
	cts_line_id = fields.Many2one('cts.line.wizard')
	concepto = fields.Many2one('hr.salary.rule','Concepto')
	monto = fields.Float('Monto')

class HrProvisionesGratiLine(models.Model):
	_name = 'hr.provisiones.grati.line'

	provision_id = fields.Many2one('hr.provisiones')
	nro_doc = fields.Char('Numero de Documento')
	employee_id = fields.Many2one('hr.employee','Empleado')
	contract_id = fields.Many2one('hr.contract','Contrato')
	fecha_ingreso = fields.Date('Fecha Ingreso')
	basico = fields.Float('Remuneracion Basica')
	asignacion = fields.Float('Asignacion Familiar')

	@api.one
	@api.depends('basico','asignacion','total_grati')
	def _get_prov_grati(self):
		total = (self.basico + self.asignacion + self.total_grati)/6
		self.provisiones_grati = float(Decimal(str(total)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

	provisiones_grati = fields.Float('Provisiones Gratificacion',compute="_get_prov_grati")
	tasa = fields.Float('Tasa')

	@api.one
	@api.depends('provisiones_grati','tasa')
	def _get_boni(self):
		self.boni_grati = float(Decimal(str((self.provisiones_grati*self.tasa)/100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

	boni_grati = fields.Float('Bonificacion de Gratificacion',compute="_get_boni")

	@api.one
	@api.depends('provisiones_grati','boni_grati')
	def _get_total(self):
		self.total = self.provisiones_grati + self.boni_grati

	total = fields.Float('Total',compute="_get_total")
	total_grati = fields.Float('Total Grat. Adic.')

	@api.multi
	def get_wizard(self):
		return self.env['grati.line.wizard'].get_wizard(self.employee_id.id,self.provision_id.id,self.id)

	@api.multi
	def unlink(self):
		for i in self.ids:
			self.env['grati.line.wizard'].search([('line_id','=',i)]).unlink()
		return super(HrProvisionesGratiLine,self).unlink()

class GratiLineWizard(models.Model):
	_name = 'grati.line.wizard'

	conceptos_lines = fields.One2many('grati.conceptos','grati_line_id')
	employee_id = fields.Many2one('hr.employee')
	provision_id = fields.Many2one('hr.provisiones')
	line_id = fields.Many2one('hr.provisiones.grati.line')

	@api.multi
	def get_wizard(self,employee_id,provision_id,line_id):
		res_id = self.env['grati.line.wizard'].search([('line_id','=',line_id)],limit=1)
		res_id = res_id.id if res_id else self.id
		return {
			'name':_('Conceptos Adicionales'),
			'type':'ir.actions.act_window',
			'res_id':res_id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'grati.line.wizard',
			'views':[[self.env.ref('planilla.grati_line_wizard').id,'form']],
			'target':'new',
			'context':{
				'default_employee_id':employee_id,
				'default_provision_id':provision_id,
				'default_line_id':line_id
			}
		}

	@api.multi
	def add_concept(self):
		total = 0
		if self.conceptos_lines:
			for line in self.conceptos_lines:
				total += line.monto
			self.env['hr.provisiones.grati.line'].browse(self.line_id.id).write({'total_grati':total})
		else:
			self.env['hr.provisiones.grati.line'].browse(self.line_id.id).write({'total_grati':0}) 
		return self.env['hr.provisiones'].browse(self.provision_id.id).grati_lines.refresh()

	@api.multi
	def unlink(self):
		for i in self.ids:
			self.env['grati.conceptos'].search([('grati_line_id','=',i)]).unlink()
		return super(GratiLineWizard,self).unlink()

class GratiConceptos(models.Model):
	_name = 'grati.conceptos'
	
	grati_line_id = fields.Many2one('grati.line.wizard')
	concepto = fields.Many2one('hr.salary.rule','Concepto')
	monto = fields.Float('Monto')

class HrProvisionesVacaLine(models.Model):
	_name = 'hr.provisiones.vaca.line'

	provision_id = fields.Many2one('hr.provisiones')
	nro_doc = fields.Char('Numero de Documento')
	employee_id = fields.Many2one('hr.employee','Empleado')
	contract_id = fields.Many2one('hr.contract','Contrato')
	fecha_ingreso = fields.Date('Fecha Ingreso')
	basico = fields.Float('Remuneracion Basica')
	asignacion = fields.Float('Asignacion Familiar')

	@api.one
	@api.depends('basico','asignacion','total_vaca')
	def _get_prov_vaca(self):
		total = (self.basico + self.asignacion + self.total_vaca)/12
		self.provisiones_vaca = float(Decimal(str(total)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))	

	provisiones_vaca = fields.Float('Provisiones Vacacion',compute="_get_prov_vaca")
	total_vaca = fields.Float('Total Vac. Adic.')

	@api.multi
	def get_wizard(self):
		return self.env['vaca.line.wizard'].get_wizard(self.employee_id.id,self.provision_id.id,self.id)

	@api.multi
	def unlink(self):
		for i in self.ids:
			self.env['vaca.line.wizard'].search([('line_id','=',i)]).unlink()
		return super(HrProvisionesVacaLine,self).unlink()

class VacaLineWizard(models.Model):
	_name = 'vaca.line.wizard'

	conceptos_lines = fields.One2many('vaca.conceptos','vaca_line_id')
	employee_id = fields.Many2one('hr.employee')
	provision_id = fields.Many2one('hr.provisiones')
	line_id = fields.Many2one('hr.provisiones.vaca.line')

	@api.multi
	def get_wizard(self,employee_id,provision_id,line_id):
		res_id = self.env['vaca.line.wizard'].search([('line_id','=',line_id)],limit=1)
		res_id = res_id.id if res_id else self.id
		return {
			'name':_('Conceptos Adicionales'),
			'type':'ir.actions.act_window',
			'res_id':res_id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'vaca.line.wizard',
			'views':[[self.env.ref('planilla.vaca_line_wizard').id,'form']],
			'target':'new',
			'context':{
				'default_employee_id':employee_id,
				'default_provision_id':provision_id,
				'default_line_id':line_id
			}
		}

	@api.multi
	def add_concept(self):
		total = 0
		if self.conceptos_lines:
			for line in self.conceptos_lines:
				total += line.monto
			self.env['hr.provisiones.vaca.line'].browse(self.line_id.id).write({'total_vaca':total})
		else:
			self.env['hr.provisiones.vaca.line'].browse(self.line_id.id).write({'total_vaca':0}) 
		return self.env['hr.provisiones'].browse(self.provision_id.id).vaca_lines.refresh()

	@api.multi
	def unlink(self):
		for i in self.ids:
			self.env['vaca.conceptos'].search([('vaca_line_id','=',i)]).unlink()
		return super(VacaLineWizard,self).unlink()

class VacaConceptos(models.Model):
	_name = 'vaca.conceptos'
	
	vaca_line_id = fields.Many2one('vaca.line.wizard')
	concepto = fields.Many2one('hr.salary.rule','Concepto')
	monto = fields.Float('Monto')