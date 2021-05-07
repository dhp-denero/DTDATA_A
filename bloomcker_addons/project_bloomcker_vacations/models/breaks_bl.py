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
    date_pre = fields.Date("Fecha de Pre")
    date_pos = fields.Date("Fecha de Pos")
    days_total = fields.Integer('Días', compute="_get_days_total")
    reason = fields.Text('Motivo')
    period = fields.Many2one('hr.payslip.run', string="Periodo")
    breaks_base_id = fields.Many2one('breaks.bl')
    employee_id = fields.Many2one('hr.employee','Apellidos y Nombres', related='breaks_base_id.employee_id', readonly=True)
    amount = fields.Float('Monto', compute='_get_amount')
    days_period = fields.Integer('Días por Periodo', compute="_get_days_period")
    alert = fields.Char('Alerta', compute="_get_alert")
    type = fields.Selection([
        ('break', 'Descanso Medico'),
        ('subsidy', 'Subsidio'),
        ('break_mother', 'Subsidio por Maternidad')], string='Tipo de Descanso')

    @api.model
    def create(self, vals):
        result = super(breaksLines,self).create(vals)
        if result:
            try:
                start = datetime.strptime(vals['date_start'], "%Y-%m-%d")
                end = datetime.strptime(vals['date_end'], "%Y-%m-%d")
                period = self.env['hr.payslip.run'].search([('id', '=', vals['period'])])
            except:
                raise UserError("Datos Suministrados Invalidos")

            if str(start)[0:7] != str(end)[0:7] or start > end:
                raise UserError("Fechas de Inicio o Fin Invalidas")

            if period.date_start[0:7] != str(start)[0:7]:
                raise UserError("Fechas de Inicio o Fin no Coinciden con periodo")

            if vals['type'] == 'break':
                lines = self.env['breaks.line.bl'].search([('breaks_base_id', '=', vals['breaks_base_id']), ('type', '=', 'break')])
                if not period:
                    raise UserError("Periodo Invalido")
                days_total = 0
                for i in lines:
                    if i.period.date_start[0:4] == period.date_start[0:4]:
                        days_total += i.days_total

                date_i = datetime.strptime(vals['date_start'], "%Y-%m-%d")
                date_o = datetime.strptime(vals['date_end'], "%Y-%m-%d")
                days_record = abs(start - end).days + 1
                if days_total <= 20:
                    return result
                else:
                    mensaje = "Un Trabajador no puede sumar más de 20 días de descanso por año, favor elegir otro tipo"
                    raise UserError(mensaje)
            else:
                return result


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
        for record in self:

            if record.type == "subsidy":
                nominas = record.env['hr.payslip'].search([('employee_id', '=', record.employee_id.id), ('state', '=', 'done'), ('date_from', '<=', record.date_start)], limit=12)
                basic_total = 0
                extras = 0
                for nomina in nominas:
                    basic_total += nomina.contract_id.wage
                    for linea in nomina.line_ids:
                        if linea.code == "COMI":
                            extras += linea.total
                        elif linea.code == "HE25":
                            extras += linea.total
                        elif linea.code == "HE35":
                            extras += linea.total
                        elif linea.code == "HE100":
                            extras += linea.total
                        elif linea.code == "LEY26504":
                            extras += linea.total
                        elif linea.code == "CONDTRA":
                            extras += linea.total
                        elif linea.code == "TRABCOMB":
                            extras += linea.total

                if basic_total:
                    prome_diario = (basic_total + extras)/(len(nominas)*30)
                    record.amount = record.days_total*prome_diario
                else:
                    record.amount = 0

            elif record.type == "break_mother":
                nominas = record.env['hr.payslip'].search([('employee_id', '=', record.employee_id.id), ('state', '=', 'done'), ('date_from', '<=', record.date_start)], limit=12)
                basic_total = 0
                extras = 0
                for nomina in nominas:
                    basic_total += nomina.contract_id.wage
                    for linea in nomina.line_ids:
                        if linea.code == "COMI":
                            extras += linea.total
                        elif linea.code == "HE25":
                            extras += linea.total
                        elif linea.code == "HE35":
                            extras += linea.total
                        elif linea.code == "HE100":
                            extras += linea.total
                        elif linea.code == "LEY26504":
                            extras += linea.total
                        elif linea.code == "CONDTRA":
                            extras += linea.total
                        elif linea.code == "TRABCOMB":
                            extras += linea.total

                if basic_total:
                    prome_diario = (basic_total + extras)/(len(nominas)*30)
                    record.amount = record.days_total*prome_diario
                else:
                    record.amount = 0

                record.amount = amount_total
            else:
                nominas = record.env['hr.payslip'].search([('employee_id', '=', record.employee_id.id), ('payslip_run_id', '=', record.period.id)], limit=1)
                basic_total = 0
                extras = 0
                for nomina in nominas:
                    basic_total += nomina.contract_id.wage
                    for linea in nomina.line_ids:
                        if linea.code == "LEY26504":
                            extras += linea.total
                            break

                if basic_total:
                    prome_diario = (basic_total + extras)/(len(nominas)*30)
                    record.amount = record.days_total*prome_diario
                else:
                    record.amount = 0

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
