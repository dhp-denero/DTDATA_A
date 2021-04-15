# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
import base64

class AddInput(models.TransientModel):
	_name = 'add.input'

	name = fields.Char('Nombre')
	code = fields.Char('Codigo')
	payslip_run_id = fields.Many2one('hr.payslip.run')

	@api.multi
	def get_wizard(self,payslip_run_id):
		return {
			'name':_('Generar Input'),
            'res_id':self.id,
            'view_type':'form',
            'view_mode':'form',
            'res_model':'add.input',
            'views':[[self.env.ref('planilla.add_input_view').id,'form']],
            'type':'ir.actions.act_window',
            'target':'new',
            'context':{
            	'default_payslip_run_id':payslip_run_id
            }
		}

	@api.multi
	def generar_input(self):
		for i in self.payslip_run_id.slip_ids:
			data = {'name': self.name,
					'payslip_id': i.id,
					'code': self.code,
					'amount': 0,
					'contract_id': i.contract_id.id}
			self.env['hr.payslip.input'].create(data)
		self.payslip_run_id.slip_ids.refresh()
		return {
            'res_id':self.payslip_run_id.id,
            'view_type':'form',
            'view_mode':'form',
            'res_model':'hr.payslip.run',
            'views':[[self.env.ref('planilla.hr_payslip_run_inherit_form').id,'form']],
            'type':'ir.actions.act_window',
        }