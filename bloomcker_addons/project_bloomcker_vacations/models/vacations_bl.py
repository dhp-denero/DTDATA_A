# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class VacationsBL(models.Model):

    _name = 'vacations.bl'

    code = fields.Char('Codigo')
    dni = fields.Char('DNI', compute="_get_dni")
    employee_id = fields.Many2one('hr.employee','Apellidos y Nombres')
    state = fields.Selection([ ('active', 'Activo'), ('inactive', 'Inactivo')], string='Estado')
    line_ids = fields.One2many('vacations.line.bl', 'vacations_base_id', string='Lineas de Vacaciones', ondelete='cascade')
    days_devs = fields.Integer('Días Devengados', compute="_get_days")
    days_totals = fields.Integer('Días Totales', compute="_get_days")
    days = fields.Integer('Días por Devengar', compute="_get_days")
    date_init = fields.Date('Fecha de Ingreso', related="employee_id.contract_id.date_start")

    @api.model
    def create(self, vals):
        result = super(VacationsBL,self).create(vals)
        if result:
            result.get_lines()

        return result

    def _get_days(self):
        for i in self:
            for line in i.line_ids:
                i.days_devs += line.days_total

            calculo = fields.Datetime.from_string(str(i.employee_id.contract_id.date_start)) - datetime.now()
            i.days_totals = int(-calculo.days // 360)*30
            i.days = i.days_totals - i.days_devs


    def _get_dni(self):
        for i in self:
            i.dni = i.employee_id.identification_id

    def _get_employees(self):
        employees = self.env['hr.employee'].search([])
        for employee in employees:
            vals = {
                'code':'0',
                'employee_id':employee.id,
                'state':'inactive',
            }
            line = self.env['vacations.bl'].create(vals)


    def get_lines(self):

        if self.line_ids:
            self.line_ids.unlink()

        devengues = self.env['hr.devengue'].search([('employee_id', '=', self.employee_id.id)])
        for devengue in devengues:
            vals = {
                'period':devengue.periodo_devengue.id,
                'employee_id':devengue.employee_id.id,
                'days_total':devengue.dias,
                'date_start':devengue.date_start,
                'date_end':devengue.date_end,
                'vacations_base_id':self.id,
            }
            line = self.env['vacations.line.bl'].create(vals)

    def put_lines(self):
        devengues = self.env['hr.devengue'].search([('employee_id', '=', self.employee_id.id)])
        devengues.unlink()
        for devengue in self.line_ids:

            slip = self.env['hr.payslip'].search([('employee_id', '=', devengue.employee_id.id), ('payslip_run_id', '=', devengue.period.id)], limit=1)
            if not slip:
                pass
                # raise UserError(('Alguna de las lineas no es valida por no tener un nomina en el periodo indicado\n Debe Procesar Las Nominas.'))
            else:
                vals = {
                    'date_end':devengue.date_end,
                    'date_start':devengue.date_start,
                    'dias':devengue.days_total,
                    'employee_id':devengue.employee_id.id,
                    'periodo_devengue':devengue.period.id,
                    'slip_id':slip.id,
                }
                line = self.env['hr.devengue'].create(vals)

    def open_lines(self):
        compose_form = self.env.ref('project_bloomcker_vacations.vacations_line_bl_tree', raise_if_not_found=False)
        domain = [('vacations_base_id', '=', self.id)]
        return {
                    'name': 'Lineas de Vacaciones',
                    'domain': domain,
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'vacations.line.bl',
                    'views': [(compose_form.id, 'tree')],
                    'view_id': compose_form.id,
                }

class VacationsLine(models.Model):

    _name = 'vacations.line.bl'

    date_start = fields.Date("Fecha de Inicio")
    date_end = fields.Date("Fecha de Fin")
    days_total = fields.Integer('Días', compute="_get_days_total")
    period = fields.Many2one('hr.payslip.run', string="Periodo")
    vacations_base_id = fields.Many2one('vacations.bl')
    employee_id = fields.Many2one('hr.employee','Apellidos y Nombres', related='vacations_base_id.employee_id', readonly=True)

    def _get_days_total(self):
        for line in self:
            if line.date_end and line.date_start:
                date_i = datetime.strptime(line.date_start, "%Y-%m-%d")
                date_o = datetime.strptime(line.date_end, "%Y-%m-%d")
                line.days_total = abs(date_o - date_i).days
            else:
                line.days_total = 0
