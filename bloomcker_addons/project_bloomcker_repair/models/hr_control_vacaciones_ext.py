# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import logging

class ControlExt(models.Model):
    _inherit = 'hr.control.vacaciones'

    @api.multi
    def calcular_vacaciones(self):

        if self.vacaciones_line:

            employee_aux = False
            sald_aux = 0

            for i in self.vacaciones_line.sorted(key=lambda r: r.employee_id):
                if employee_aux == False or employee_aux == i.employee_id:
                    employee_aux = i.employee_id
                    if i.saldo_vacaciones > sald_aux:
                        i.employee_id.sald_vacaciones = i.saldo_vacaciones
                        sald_aux = i.saldo_vacaciones
                    else:
                        i.employee_id.sald_vacaciones = sald_aux
                else:
                    i.employee_id.sald_vacaciones = i.saldo_vacaciones
                    sald_aux = i.saldo_vacaciones
                    employee_aux = i.employee_id


            self.vacaciones_line.unlink()

        employees = self.env['hr.employee'].search([('id','!=','1')])

        for employee in employees:

            saldo = employee.sald_vacaciones
            # saldo, aux_year = 30, 0
            aux_year = 0
            devengues = self.env['hr.devengue'].search([('employee_id','=',employee.id)])
            devengues = devengues.sorted(key=lambda devengue:devengue.periodo_devengue.date_start)

            if len(devengues) == 0:
                self.env['hr.control.vacaciones.line'].create({
                    'fiscalyear_id':0,
                    'dni':employee.identification_id,
                    'employee_id':employee.id,
                    'periodo_planilla':0,
                    'periodo_devengue':0,
                    'saldo_vacaciones':saldo,
                    'dias_gozados':0,
                    # 'total':saldo,
                    'control_vacaciones_id':self.id
                })
            else:
                for devengue in devengues:
                    try:
                        year = self.env['account.fiscalyear'].search([('name','=',str(datetime.strptime(devengue.periodo_devengue.date_start,'%Y-%m-%d').year))],limit=1)
                    except:
                        year = self.env['account.fiscalyear'].search([],limit=1)

                    if year != aux_year:
                        saldo = employee.sald_vacaciones
                        # saldo = 30

                    aux_year = year
                    if devengue.dias > 0:
                        self.env['hr.control.vacaciones.line'].create({
                            'fiscalyear_id':year.id,
                            'dni':employee.identification_id,
                            'employee_id':employee.id,
                            'employee_id':employee.id,
                            'periodo_planilla':devengue.slip_id.payslip_run_id.id,
                            'periodo_devengue':devengue.periodo_devengue.id,
                            'saldo_vacaciones':saldo,
                            'dias_gozados': devengue.dias,
                            'control_vacaciones_id':self.id
                        })

                        saldo = saldo - devengue.dias
        return self.env['planilla.warning'].info(title='Resultado', message="Se actualizo correctamente")

class CotrolLineExt(models.Model):
    _inherit = 'hr.control.vacaciones.line'

    total = fields.Integer('Total', compute="_get_total_days", readonly=True)
    sald_sugerido = fields.Integer('Saldo Sugerido', compute="_get_sal_sugerido", readonly=True)
    fecha_inicio = fields.Char('Fecha de Inicio', compute="_get_fecha_inicio", readonly=True)
    devengue_total = fields.Integer('Total Dias Gozados', compute="_get_devengue_total", readonly=True)

    def _get_devengue_total(self):
        for i in self:
            devengues = i.env['hr.devengue'].search([('employee_id','=',i.employee_id.id)])
            i.devengue_total = sum(devengues.mapped('dias'))

    def _get_fecha_inicio(self):
        for i in self:
            i.fecha_inicio = str(i.employee_id.contract_id.date_start)

    def _get_sal_sugerido(self):
        for i in self:
            calculo = fields.Datetime.from_string(str(i.employee_id.contract_id.date_start)) - datetime.now()
            i.sald_sugerido = int(calculo.days * -2.5 / 30)

    @api.model
    def _get_total_days(self):
        for i in self:
            try:
                i.total = i.saldo_vacaciones - i.dias_gozados
            except:
                i.total = 0

    @api.onchange('saldo_vacaciones', 'dias_gozados')
    def _onchange_total(self):
        try:
            self.total = self.saldo_vacaciones - self.dias_gozados
        except:
            self.total = 0
