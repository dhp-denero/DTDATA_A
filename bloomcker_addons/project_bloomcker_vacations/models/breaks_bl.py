# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class breaksBL(models.Model):

    _name = 'breaks.bl'

    employee_id = fields.Many2one('hr.employee','Apellidos y Nombres')
    state = fields.Selection([ ('active', 'Activo'), ('inactive', 'Inactivo')], string='Estado')
    line_ids = fields.One2many('breaks.line.bl', 'breaks_base_id', string='Lineas de Descansos', ondelete='cascade')
    date_init = fields.Date('Fecha de Ingreso', related="employee_id.contract_id.date_start")
    dni = fields.Char('DNI', related="employee_id.identification_id")

    def send_message(self):
        mensaje = "El Trabajador " + str(self.employee_id.name) + " tiene más de 20 días de descanso, Favor elaborar el Formulario 8001"
        raise UserError(mensaje)

    def open_lines(self):
        compose_form = self.env.ref('project_bloomcker_vacations.breaks_line_bl_tree', raise_if_not_found=False)
        domain = [('breaks_base_id', '=', self.id)]
        return {
                    'name': 'Lineas de Descanso',
                    'domain': domain,
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'breaks.line.bl',
                    'views': [(compose_form.id, 'tree')],
                    'view_id': compose_form.id,
                }


class breaksLines(models.Model):

    _name = 'breaks.line.bl'

    date_start = fields.Date("Fecha de Inicio")
    date_end = fields.Date("Fecha de Fin")
    days_total = fields.Integer('Días', compute="_get_days_total")
    reason = fields.Char('Motivo')
    period = fields.Many2one('hr.payslip.run', string="Periodo")
    breaks_base_id = fields.Many2one('breaks.bl')
    employee_id = fields.Many2one('hr.employee','Apellidos y Nombres', related='breaks_base_id.employee_id', readonly=True)
    amount = fields.Float('Monto', compute='_get_amount')
    subsidy = fields.Boolean(name="Subsidio", default=False)
    days_period = fields.Integer('Días por Periodo', compute="_get_days_period")
    alert = fields.Char('Alerta', compute="_get_alert")

    def _get_days_period(self):
        for record in self:
            record.alert_check = False
            suma = 0
            for line in record.breaks_base_id.line_ids:
                if line.period == record.period:
                    suma += line.days_total

            record.days_period = suma

    def _get_alert(self):
        for record in self:
            if record.days_period > 20:
                record.alert = "Excedencia"
            else:
                record.alert = ""

    def _get_amount(self):
        for j in self:
            contracts = j.env['hr.contract'].search([('employee_id', '=', j.employee_id.id)], limit=6)
            amount_total = 0
            for i in contracts:
                amount_total += i.wage

            if amount_total:
                amount_total = ((amount_total/len(contracts))/30)*j.days_total

            j.amount = amount_total

    def _get_days_total(self):
        for line in self:
            if line.date_end and line.date_start:
                date_i = datetime.strptime(line.date_start, "%Y-%m-%d")
                date_o = datetime.strptime(line.date_end, "%Y-%m-%d")
                line.days_total = abs(date_o - date_i).days + 1
            else:
                line.days_total = 0

    def send_message(self):
        mensaje = "El Trabajador " + str(self.employee_id.name) + " tiene más de 20 días de descanso, Favor elaborar el Formulario 8001"
        raise UserError(mensaje)
