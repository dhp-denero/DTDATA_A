# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime


class PlanillaDetalleLineaNomina(models.Model):
    _name = 'planilla.detalle.linea.nomina'
    _auto = False

    fecha_ini = fields.Date()
    fecha_fin = fields.Date()
    name = fields.Char()
    dni = fields.Char()
    nombres = fields.Char()
    sequence = fields.Char()
    concepto = fields.Char()
    cuenta_debe = fields.Char()
    cuenta_haber = fields.Char()
    monto = fields.Float('Monto', digits=(12, 2))
    slip_id = fields.Integer()
    salary_rule_id = fields.Integer()
    employee_id = fields.Integer()
    contract_id = fields.Integer()


class PlanillaDetalleLineaNominaWizard(models.TransientModel):

    _name = "planilla.detalle.linea.nomina.wizard"

    hr_payslip_run_id = fields.Many2one(
        'hr.payslip.run',
        string=u'Periodo de nomina', required=True,
        ondelete='cascade'
    )

    date_start_rel = fields.Date("Fecha inicio",related='hr_payslip_run_id.date_start', readonly="1")
    date_end_rel =  fields.Date("Fecha Fin",related='hr_payslip_run_id.date_end', readonly="1")




    @api.multi
    def do_rebuild(self):

        query_vista = """  
                DROP VIEW IF EXISTS planilla_detalle_linea_nomina;
                create or replace view planilla_detalle_linea_nomina as (
                select row_number() OVER () AS id,* from
                (
                    select 
                    a6.date_start as fecha_ini,
                    a6.date_end as fecha_fin,
                    a6.name,
                    a4.identification_id as dni,
                    a4.name_related as nombres,
                    a5.sequence,
                    a5.name as concepto,
                    a7.code as cuenta_debe,
                    a8.code as cuenta_haber,
                    a1.amount as monto,
                    a1.slip_id,a1.salary_rule_id,a1.employee_id,a1.contract_id from hr_payslip_line a1
                    left join hr_payslip a2 on a2.id=a1.slip_id
                    left join hr_contract a3 on a3.id=a1.contract_id
                    left join hr_employee a4 on a4.id=a1.employee_id
                    left join hr_salary_rule a5 on a5.id=a1.salary_rule_id
                    left join hr_payslip_run a6 on a6.id=a2.payslip_run_id
                    left join account_account a7 on a7.id=a5.account_debit
                    left join account_account a8 on a8.id=a5.account_credit
                    where char_length(trim(concat(a7.code,a8.code)))> 0 and  a6.date_start='%s' and a6.date_end='%s'
                    order by a5.sequence
                        ) T
                )""" % (self.date_start_rel,self.date_end_rel)

        self.env.cr.execute(query_vista)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'planilla.detalle.linea.nomina',
            'view_type': 'form',
            'view_mode': 'tree',
            'target': 'current'
        }
