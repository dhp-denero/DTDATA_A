# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime


class PlanillaAsientoDistribuido(models.Model):
    _name = 'planilla.asiento.distribuido'
    _auto = False

    fecha_fin = fields.Date()
    concepto = fields.Char()
    cuenta_debe = fields.Char("Cuenta")
    cuenta_analitica_id = fields.Char()
    debe = fields.Float('Debe', digits=(12, 2))
    haber = fields.Float('Haber', digits=(12, 2))


class PlanillaAsientoDistribuidoWizard(models.TransientModel):

    _name = "planilla.asiento.distribuido.wizard"

    hr_payslip_run_id = fields.Many2one(
        'hr.payslip.run',
        string=u'Periodo de Procesamiento de nomina', required=True,
        ondelete='cascade'
    )

    date_start_rel = fields.Date("Fecha inicio",related='hr_payslip_run_id.date_start', readonly="1")
    date_end_rel =  fields.Date("Fecha Fin",related='hr_payslip_run_id.date_end', readonly="1")




    @api.multi
    def do_rebuild(self):
        query_vista = """  
                DROP VIEW IF EXISTS planilla_asiento_distribuido;
                create or replace view planilla_asiento_distribuido as (
                select row_number() OVER () AS id,* from
                (
                    select * from (
                    select 
                    a6.date_end as fecha_fin,
                    'ASIENTO DISTRIBUIDO DE LA PLANILLA DEL MES':: TEXT as concepto,
                    a7.code::TEXT as cuenta_debe,
                    a10.code as cuenta_analitica_id,
                    sum(a1.amount*(a9.porcentaje/100)) as debe,
                    0 as haber
                    from hr_payslip_line a1
                    left join hr_payslip a2 on a2.id=a1.slip_id
                    left join hr_contract a3 on a3.id=a1.contract_id
                    left join hr_employee a4 on a4.id=a1.employee_id
                    left join hr_salary_rule a5 on a5.id=a1.salary_rule_id
                    left join hr_payslip_run a6 on a6.id=a2.payslip_run_id
                    left join account_account a7 on a7.id=a5.account_debit
                    left join planilla_distribucion_analitica a8 on a8.id=a3.distribucion_analitica_id
                    left join planilla_distribucion_analitica_lines a9 on a9.distribucion_analitica_id=a8.id
					left join account_analytic_account a10 on a10.id=a9.cuenta_analitica_id
                    where a7.code is not null and a1.amount<>0 and a6.date_start='""" +self.date_start_rel+"""' and a6.date_end='"""+self.date_end_rel+ """'
                    group by a6.date_end,a7.code,a10.code
                    order by a7.code)tt
                    union all 
                    select * from (
                    select 
                    a6.date_end as fecha_fin,
                    a5.name as concepto,
                    a7.code:: TEXT as cuenta,
                    null:: TEXT as cuenta_analitica_id,
                    0 as debe,
                    sum(a1.amount) as haber
                    from hr_payslip_line a1
                    left join hr_payslip a2 on a2.id=a1.slip_id
                    left join hr_contract a3 on a3.id=a1.contract_id
                    left join hr_employee a4 on a4.id=a1.employee_id
                    left join hr_salary_rule a5 on a5.id=a1.salary_rule_id
                    left join hr_payslip_run a6 on a6.id=a2.payslip_run_id
                    left join account_account a7 on a7.id=a5.account_credit
                    where a7.code is not null and a6.date_start='%s' and a6.date_end='%s'
                    group by a6.date_end,a6.name,a5.name,a7.id,a7.code
                    having sum(a1.amount)<>0
                    order by a7.code)tt
                        ) T
                )""" % (self.date_start_rel,self.date_end_rel)

        self.env.cr.execute(query_vista)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'planilla.asiento.distribuido',
            'view_type': 'form',
            'view_mode': 'tree',
            'target': 'current'
        }
