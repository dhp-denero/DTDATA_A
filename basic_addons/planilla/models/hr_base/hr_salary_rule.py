import time
from datetime import datetime, timedelta
from dateutil import relativedelta

import babel

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
from decimal import *

'''
result = contract.wage + payslip.planilla_afiliacion_line_id.search([['periodo_id.code','=',payslip.periodo_id.code],['planilla_afiliacion_id.entidad','=',contract.afiliacion_id.entidad]]).fondo
'''


class hr_salary_rule(models.Model):

    _inherit = 'hr.salary.rule'
    code = fields.Char(required=True,size=8)# reescribiendo el codigo de arriba
    cod_sunat = fields.Char("Codigo Sunat")
    category_id = fields.Many2one("hr.salary.rule.category",string="Category",required=False)
    is_subtotal = fields.Boolean("Es un Subtotal",required=True)


    @api.multi
    def write(self,vals):
        self.ensure_one()
        line=False
        if 'code' in vals:
            line = self.env['hr.salary.rule'].search(
                [('code', '=', vals['code'])])
        if line:
            raise ValidationError(
                "la regla salarial %s ya existe" % vals['code'])
        t = super(hr_salary_rule, self).write(vals)
        return t

    @api.multi
    def compute_rule(self,localdict):
        self.ensure_one()
        if self.amount_select == 'code':
            localdict['Decimal'] = Decimal
            localdict['ROUND_HALF_UP'] = ROUND_HALF_UP
            if self.code == 'AF':
                sql = """
                    select he.id
                    from hr_payslip hp
                    inner join hr_employee he on he.id = hp.employee_id
                    inner join hr_contract hc on hc.id = hp.contract_id
                    where hp.payslip_run_id = %d and
                    he.id = %d and
                    hc.regimen_laboral_empresa not in ('practicante','microempresa')
                """%(localdict['payslip'].payslip_run_id.id,localdict['employee'].id)
                self.env.cr.execute(sql)
                data = self.env.cr.dictfetchall()
                localdict['payslip_count'] = len(data)
            try:
                safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
                return float(localdict['result']), 'result_qty' in localdict and localdict['result_qty'] or 1.0, 'result_rate' in localdict and localdict['result_rate'] or 100.0
            except:
                raise UserError(_('Wrong python code defined for salary rule %s (%s).') % (self.name, self.code))
        amount,qty,rate = super(hr_salary_rule,self).compute_rule(localdict)
        return amount,qty,rate

class hr_salary_rule_line(models.Model):

    _inherit = 'hr.payslip.line'
    is_subtotal_ref = fields.Boolean(
        "Es un Subtotal", related="salary_rule_id.is_subtotal")
