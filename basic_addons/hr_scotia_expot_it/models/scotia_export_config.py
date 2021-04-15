# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api, exceptions, _
from odoo.exceptions import UserError

class hr_sbank_export_config(models.Model):
	_name = 'hr.sbank.export.config'

	name=fields.Char('Nombre de Banco',default='ScotiaBank')
	bank_id = fields.Many2one('res.bank','Banco asociado')
	text_concep = fields.Char('Texto para la referencia/concepto',default='Pago de sueldos')
	cod_ofi_pos = fields.Char(u'Posición del código de oficna en el número de cta',help=u'Indique la posición del codigo de oficina ej. si la cuenta es 0597432970 colocar: 1,3 que sería el 059',default='1,3')
	cod_cta_pos = fields.Char(u'Posición del Inicial del código de cuenta en el número de cta',help=u'Indique la posición del número de cuenta ej. si la cuenta es 0597432970 colocar: 5',default='5')
	# paymethod_ids = fields.One2many('hr.bank.export.paymethod','main_id',u'Métodos de pago')
	salary_rule_id = fields.Many2one('hr.salary.rule','Regla Salarial para el sueldo')

class hr_sbank_export_paymethod(models.Model):
	_name = 'hr.sbank.export.paymethod'	

	name=fields.Char('Método de pago')
	value_export=fields.Char('Valor equivalente')
	main_id = fields.Many2one('scotia.export.config','')

