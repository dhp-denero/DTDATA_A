# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import logging


class EmployeeExt(models.Model):
    _inherit = 'hr.payslip.run'

    def update_employees(self):
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
        for contract in self.env['hr.contract'].browse([row['id'] for row in employee_aux_ids]):
            if contract.employee_id.id in self.slip_ids:
                raise UserError('Hola '+str(contract.employee_id.name))
