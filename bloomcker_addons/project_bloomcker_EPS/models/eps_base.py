# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class EpsBase(models.Model):

    _name = 'eps.base'

    name = fields.Char('Identificador')
    period = fields.Date('Fecha Desde')
    nomina = fields.Many2one('hr.payslip.run', required=True)
    line_ids = fields.One2many('eps.base.line', 'eps_base_id', string='Lineas de EPS', ondelete='cascade')
    porcentaje_aporte = fields.Float("Aporte ESSALUD (%)", default=9)
    porcentaje_credito = fields.Float("Crédito ESSALUD (%)", default=25)
    porcentaje_descuento = fields.Float("Descuento ESSALUD (%)", default=18)

    def get_lines(self):

        if self.line_ids:
			self.line_ids.unlink()

        base = 0
        for i in self.nomina.slip_ids:
            if i.employee_id.eps_check:
                for j in i.line_ids:
                    if j.code == "AESSALUD":
                        base = j.total
                        break

                vals = {
                    'eps_base_id':self.id,
                    'dni':i.employee_id.identification_id,
                    'employee_id':i.employee_id.id,
                    'period':i.date_from,
                    'base_afecta':base,
                    'payslip_id':i.id,
                }
                line = self.env['eps.base.line'].create(vals)

    def mod_lines(self):
        compose_form = self.env.ref('project_bloomcker_EPS.eps_line_tree', raise_if_not_found=False)
        domain = [('eps_base_id', '=', self.id)]
        return {
                    'name': 'Lineas de EPS',
                    'domain': domain,
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'eps.base.line',
                    'views': [(compose_form.id, 'tree')],
                    'view_id': compose_form.id,
                }

class EpsLine(models.Model):

    _name = 'eps.base.line'

    name = fields.Char('Identificador')
    period = fields.Date('Periodo')
    eps_base_id = fields.Many2one('eps.base', readonly=True)
    payslip_id = fields.Many2one('hr.payslip', readonly=True)
    dni = fields.Char(string='DNI', readonly=True, related="employee_id.identification_id")
    employee_id = fields.Many2one('hr.employee','Apellidos y Nombres', required=True)
    plan = fields.Char('Plan', compute="_get_plan")
    base_afecta = fields.Float("Base Afecta ESSALUD")
    aporte_essalud = fields.Float("Aporte ESSALUD", compute="_get_amounts")
    credito_eps = fields.Float("Crédito EPS", compute="_get_amounts")
    costo = fields.Float("Costo", default=0)
    descuento = fields.Float("Descuento", compute="_get_amounts")

    def _get_plan(self):
        for i in self:
            i.plan = i.employee_id.plan_eps

    def _get_amounts(self):
        for i in self:
            i.aporte_essalud = i.base_afecta*i.eps_base_id.porcentaje_aporte/100
            i.credito_eps = i.base_afecta*i.eps_base_id.porcentaje_credito*i.eps_base_id.porcentaje_aporte/10000
            i.descuento = (i.costo - i.credito_eps)*(1 + i.eps_base_id.porcentaje_descuento/100)
            i.payslip_id.write({"descuento_eps": i.descuento})

    @api.onchange('descuento')
    def _onchange_descuento(self):
        self.payslip_id.write({"descuento_eps": self.descuento})

    @api.model
    def create(self, vals):
        result = super(EpsLine,self).create(vals)
        if result:
            try:
                employee = self.env['hr.employee'].search([('id', '=', vals['employee_id'])], limit=1)
                base = self.env['eps.base'].search([('id', '=', vals['eps_base_id'])], limit=1)
                slip = self.env['hr.payslip'].search([('payslip_run_id', '=', base.nomina.id), ('employee_id', '=', employee.id)], limit=1)
            except:
                return result
            if slip and employee:
                base_afecta = 0
                if employee.eps_check:
                    for record in slip.line_ids:
                        if record.code == "AESSALUD":
                            base_afecta = record.total
                            break
                result.base_afecta = base_afecta
                result.period = slip.date_from

            return result
