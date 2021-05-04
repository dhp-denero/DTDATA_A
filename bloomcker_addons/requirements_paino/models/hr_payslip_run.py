# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import logging


class EmployeeExt(models.Model):
    _inherit = 'hr.payslip.run'

    def update_employees(self):
        payslips = self.env['hr.payslip']
        from_date = self.date_start
        to_date = self.date_end
        query = """
		select hc.id
		from hr_contract hc
		inner join hr_employee he on hc.employee_id = he.id
		where
		(date_end >= '%s' and date_end <= '%s') or
		(date_start <= '%s' and date_start >='%s'   ) or
		(
			date_start <='%s' and (date_end is null or date_end >= '%s' )
		)
		""" % (from_date, to_date,
			   to_date, from_date,
			   from_date, to_date
			   )
        self.env.cr.execute(query)
        employee_aux_ids = self.env.cr.dictfetchall()
        employees = []

        for slip in self.slip_ids:
            employees.append(slip.employee_id.id)

        for contract in self.env['hr.contract'].browse([row['id'] for row in employee_aux_ids]):
            if contract.employee_id.id not in employees:
                slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, contract.employee_id.id, contract.id)
                res = {
    				'employee_id': contract.employee_id.id,
    				'name': slip_data['value'].get('name'),
    				'struct_id': slip_data['value'].get('struct_id'),
    				'contract_id': contract.id,
    				'payslip_run_id': self.id,
    				'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
    				'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
    				'date_from': from_date,
    				'date_to': to_date,
    				'credit_note': self.credit_note,
    				'company_id': contract.employee_id.company_id.id,
    			}
                payslip = self.env['hr.payslip'].create(res)
                payslip.load_entradas_tareos()
                payslips += payslip
