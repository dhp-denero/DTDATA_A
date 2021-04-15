# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime


class PlanillaAsientoResumen(models.Model):
    _name = 'planilla.asiento.resumen'
    _auto = False

    fecha_fin = fields.Date()
    name = fields.Char()
    concepto = fields.Char()
    cuenta_id = fields.Integer()
    cuenta = fields.Float('Cuenta', digits=(12, 2))
    debe = fields.Float('Debe', digits=(12, 2))
    haber = fields.Float('Haber', digits=(12, 2))



class PlanillaAsientoResumenWizard(models.TransientModel):

    _name = "planilla.asiento.resumen.wizard"

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
                DROP VIEW IF EXISTS planilla_asiento_resumen;
                create or replace view planilla_asiento_resumen as (
                select row_number() OVER () AS id,* from
                (
                    select * from (
                        select 
                        a6.date_end as fecha_fin,
                        a6.name,
                        a5.name as concepto,
                        a7.id as cuenta_id,
                        a7.code as cuenta,
                        sum(a1.amount) as debe,
                        0 as haber,
                        ''::text as nro_documento,
                        0 as partner_id
                        from hr_payslip_line a1
                        left join hr_payslip a2 on a2.id=a1.slip_id
                        left join hr_contract a3 on a3.id=a1.contract_id
                        left join hr_employee a4 on a4.id=a1.employee_id
                        left join hr_salary_rule a5 on a5.id=a1.salary_rule_id
                        left join hr_payslip_run a6 on a6.id=a2.payslip_run_id
                        left join account_account a7 on a7.id=a5.account_debit
                        where a7.code is not null and a6.date_start='%s' and a6.date_end='%s'
                        group by a6.date_end,a6.name,a5.name,a7.id,a7.code
                        having sum(a1.amount)<>0
                        order by a7.code)tt
                    union all
                    select * from (
                        select 
                        a6.date_end as fecha_fin,
                        a6.name,
                        a5.name as concepto,
                        a7.id as cuenta_id,
                        a7.code as cuenta,
                        0 as debe,
                        sum(a1.amount) as haber,
                        ''::text as nro_documento,
                        0 as partner_id
                        from hr_payslip_line a1
                        left join hr_payslip a2 on a2.id=a1.slip_id
                        left join hr_contract a3 on a3.id=a1.contract_id
                        left join hr_employee a4 on a4.id=a1.employee_id
                        left join hr_salary_rule a5 on a5.id=a1.salary_rule_id
                        left join hr_payslip_run a6 on a6.id=a2.payslip_run_id
                        left join account_account a7 on a7.id=a5.account_credit
                        where a7.code is not null and  a6.date_start='%s' and a6.date_end='%s'
                            and a1.code not in ('COMFI','COMMIX','SEGI','A_JUB')
                            and a7.code not like '%s'
                        group by a6.date_end,a6.name,a5.name,a7.id,a7.code 
                        having sum(a1.amount)<>0
                        order by a7.code)tt
                    union all 
                    select * from (
                        select 
                        hpr.date_end as fecha_fin,
                        hpr.name,
                        pa.entidad||' - '||hpl.code as concepto,
                        pa.account_id as cuenta_id,
                        ''::text as cuenta,
                        0 as debe,
                        round(sum((hpl.amount))::numeric,2) as haber,
                        ''::text as nro_documento,
                        0 as partner_id
                        from hr_payslip_line hpl
                        left join hr_payslip hp on hp.id = hpl.slip_id
                        left join hr_contract hc on hc.id = hp.contract_id
                        left join planilla_afiliacion pa on pa.id = hc.afiliacion_id
                        left join hr_payslip_run hpr on hpr.id = hp.payslip_run_id
                        left join hr_salary_rule hsr on hsr.id = hpl.salary_rule_id
                        where pa.account_id is not null and hpr.date_start='%s' and hpr.date_end='%s' 
                            and hpl.code in ('COMFI','COMMIX','SEGI','A_JUB')
                        group by hpr.date_end,hpr.name,pa.entidad,pa.account_id,hpl.code
                        having sum(hpl.amount)<>0
                    )ttt 
                    union all
                    select * from (
                        select 
                        min(a6.date_end) as fecha_fin,
                        min(a6.name),
                        min(a5.name) as concepto,
                        min(a7.id) as cuenta_id,
                        ''::text as cuenta,
                        0 as debe,
                        round(sum((a1.amount))::numeric,2) as haber,
                        rp.nro_documento as nro_documento,
                        coalesce(rp.id,0) as partner_id
                        from hr_payslip_line a1
                        left join hr_payslip a2 on a2.id=a1.slip_id
                        left join hr_contract a3 on a3.id=a1.contract_id
                        left join hr_employee a4 on a4.id=a1.employee_id
                        left join res_partner rp on rp.id = a4.address_home_id
                        left join hr_salary_rule a5 on a5.id=a1.salary_rule_id
                        left join hr_payslip_run a6 on a6.id=a2.payslip_run_id
                        left join account_account a7 on a7.id=a5.account_credit
                        where a7.code is not null and a6.date_start= '%s' and a6.date_end= '%s'
                            and a1.code not in ('COMFI','COMMIX','SEGI','A_JUB')
                            and a7.code like '%s'
                        group by rp.id,rp.nro_documento,a7.code
                        having sum(a1.amount)<>0
                        order by a7.code)tt
                    ) T
                )""" % (self.date_start_rel,self.date_end_rel,
                    self.date_start_rel,self.date_end_rel,'41%',
                    self.date_start_rel,self.date_end_rel,
                    self.date_start_rel,self.date_end_rel,'41%')

        self.env.cr.execute(query_vista)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'planilla.asiento.resumen',
            'view_type': 'form',
            'view_mode': 'tree',
            'target': 'current'
        }
