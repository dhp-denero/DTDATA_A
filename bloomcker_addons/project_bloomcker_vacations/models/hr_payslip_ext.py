# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from dateutil import relativedelta
import babel
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
from reportlab.lib.pagesizes import landscape, letter, A2, A4
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from decimal import *
from math import modf


class HrPayslipExt(models.Model):
    _inherit = 'hr.payslip'

    monto_descanso = fields.Float("Monto por Descanso", compute="_get_descanso")
    monto_subsidio = fields.Float("Monto por Subsidio", compute="_get_descanso")
    comi_promedio = fields.Float("Promedio de Comisiones", compute="_get_comisiones")
    fault_ids = fields.One2many('faults.bl', 'slip_base_id', string='Lineas de Faltas', ondelete='cascade')
    comisiones_aux = fields.Float("campo aux para comisiones")

    def _get_comisiones(self):
        for j in self:
            comisiones_ids = j.env['hr.payslip.line'].search([('employee_id', '=', j.employee_id.id), ('code', '=', 'COMI')])
            monto = 0
            contador = 0
            for i in comisiones_ids:
                if j.date_from[0:4] == str(datetime.now().date())[0:4]:
                    if int(j.date_from[5:7]) in list(range(1,7)):
                        inicio = 1
                    else:
                        inicio = int(j.date_from[5:7]) - 5
                    lista = list(range(inicio, int(j.date_from[5:7]) + 1))
                    if int(i.slip_id.date_from[5:7]) in lista:
                        monto += i.total
                        contador += 1
            if contador and monto:
                j.comi_promedio = monto / contador
            else:
                j.comi_promedio = 0

    def _get_descanso(self):
        descansos_ids = self.env['breaks.line.bl'].search([('employee_id', '=', self.employee_id.id), ('period', '=', self.payslip_run_id.id)])
        amount = 0
        dias = 0
        subsidy = 0
        for descanso in descansos_ids:
            dias += descanso.days_total
            amount += descanso.amount
            if descanso.subsidy:
                subsidy += descanso.amount

        if dias > 20:
            self.monto_descanso = (amount/dias)*20 - subsidy
            self.monto_subsidio = (amount/dias)*(dias - 20) + subsidy
        else:
            self.monto_descanso = amount - subsidy
            self.monto_subsidio = 0 + subsidy



    @api.multi
    def compute_sheet(self):
        self.comisiones_aux = self.comi_promedio
        config = self.env['planilla.quinta.categoria'].search([])
        if len(config) == 0:
            raise ValidationError(
                u'No esta configurado los parametros para Quinta Categoria')
        config = config[0]

        breaks = self.env['breaks.line.bl'].search([('employee_id', '=', self.employee_id.id), ('period', '=', self.payslip_run_id.id)])
        mother_days = self.env['hr.payslip.worked_days'].search([('payslip_id', '=', self.id), ('code', '=', 'DSUBM')], limit=1)
        
        if mother_days:
            days_mother = mother_days.number_of_days
        else:
            days_mother = 0

        days_total = 0
        days_break = 0
        days_faults = 0

        for i in breaks:
            days_break += i.days_total

        for i in self.periodos_devengue:
            days_total += i.dias

        for i in self.fault_ids:
            days_faults += i.days



        for days_line in self.worked_days_line_ids:
            if days_line.code == "DVAC":
                days_line.number_of_days = days_total
            elif days_line.code == "DSUBE":
                days_line.number_of_days = days_break
            elif days_line.code == "FAL":
                days_line.number_of_days = days_faults
            elif days_line.code == "DLAB":
                days_line.number_of_days = 30 - days_total - days_break - days_faults - days_mother

        self.env.cr.execute("""delete from hr_payslip_line
                            where employee_id = """+str(self.employee_id.id)+""" and slip_id = """+str(self.id))
        super(HrPayslipExt, self).compute_sheet()

    @api.multi
    def imprimir_boleta(self):
        self.ensure_one()
        dias_no_laborados,dias_laborados,first,second,dias_faltas = 0,0,0,0,0
        payslips = self.env['hr.payslip'].search([('payslip_run_id','=',self.payslip_run_id.id),('employee_id','=',self.employee_id.id)])
        planilla_ajustes = self.env['planilla.ajustes'].search([], limit=1)
        try:
            ruta = self.env['main.parameter.hr'].search([])[0].dir_create_file
        except:
            raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')

        archivo_pdf = SimpleDocTemplate(
            ruta+"planilla_tmp.pdf", pagesize=A4, rightMargin=10, leftMargin=10, topMargin=10, bottomMargin=5)

        elements = []
        company = self.env['res.company'].search([], limit=1)
        categories = self.env['hr.salary.rule.category'].search(
            [('aparece_en_nomina', '=', True)], order="secuencia")

        for payslip in payslips:
            dias_no_laborados += int(payslip.worked_days_line_ids.search([('code', '=', planilla_ajustes.cod_dias_no_laborados.codigo if planilla_ajustes else ''),
                                                                        ('payslip_id', '=', payslip.id)], limit=1).number_of_days)
        for payslip in payslips:
            if not payslip.contract_id.hourly_worker:
                dias_laborados += int(payslip.worked_days_line_ids.search([('code', '=', planilla_ajustes.cod_dias_laborados.codigo if len(planilla_ajustes) > 0 else ''),
                                                                    ('payslip_id', '=', payslip.id)], limit=1).number_of_days)
        dias_laborados=dias_laborados-self.feriados if dias_laborados > 0 else 0
        if not planilla_ajustes.cod_dias_subsidiados:
            raise UserError('Falta configurar codigos de dias subsidiados en Parametros de Boleta.')
        wd_codes = planilla_ajustes.cod_dias_subsidiados.mapped('codigo')
        dias_subsidiados = 0
        for payslip in payslips:
            wds = filter(lambda l:l.code in wd_codes and l.payslip_id == payslip,payslip.worked_days_line_ids)
            dias_subsidiados += sum([int(i.number_of_days) for i in wds])

        query_horas_sobretiempo = '''
        select sum(number_of_days) as dias ,sum(number_of_hours) as horas ,sum(minutos) as minutos from hr_payslip_worked_days
        where (code = 'HE25' OR code = 'HE35' or code = 'HE100')
        and payslip_id in (%s)
        ''' % (','.join(str(i) for i in payslips.mapped('id')))

        self.env.cr.execute(query_horas_sobretiempo)
        total_sobretiempo = self.env.cr.dictfetchone()
        for payslip in payslips:
            dias_faltas += self.env['hr.payslip.worked_days'].search([('code', '=', planilla_ajustes.cod_dias_no_laborados.codigo if planilla_ajustes else ''),
                                                                    ('payslip_id', '=', payslip.id)], limit=1).number_of_days
        if self.employee_id.calendar_id:
            total = self.employee_id.calendar_id.average_hours if self.employee_id.calendar_id.average_hours > 0 else 8
        else:
            total = 8

        total_horas_jornada_ordinaria = 0
        for payslip in payslips:
            if payslip.contract_id.hourly_worker:
                total_horas_jornada_ordinaria += sum(payslip.worked_days_line_ids.filtered(lambda l:l.code == planilla_ajustes.cod_dias_laborados.codigo).mapped('number_of_hours'))

        if self.employee_id.calendar_id:
            total = self.employee_id.calendar_id.average_hours if self.employee_id.calendar_id.average_hours > 0 else 8
        else:
            total = 8

        total_horas_minutos = modf(int(dias_laborados-dias_faltas)*total) if total_horas_jornada_ordinaria == 0 else total_horas_jornada_ordinaria
        total_horas_jornada_ordinaria = total_horas_minutos[1]
        total_minutos_jornada_ordinaria = Decimal(str(total_horas_minutos[0] * 60)).quantize(Decimal('1.'), rounding=ROUND_HALF_UP)

        payslip_run = self.env['hr.payslip.run']

        payslip_run.genera_boleta_empleado(self.date_from, self.date_to, payslips, str(dias_no_laborados), str(int(dias_laborados - dias_faltas)), str(total_horas_jornada_ordinaria), str(total_minutos_jornada_ordinaria), (total_sobretiempo), str(dias_subsidiados), elements,
                                           company, categories, planilla_ajustes)

        elements = elements*2
        archivo_pdf.build(elements)

        import sys
        reload(sys)
        sys.setdefaultencoding('iso-8859-1')
        import os
        vals = {
            'output_name': 'Boleta-%s.pdf' % (payslip[0].employee_id.name+'-'+payslip[0].date_from+'-'+payslip[0].date_to),
            'output_file': open(ruta+"planilla_tmp.pdf", "rb").read().encode("base64"),
        }
        sfs_id = self.env['planilla.export.file'].create(vals)
        return {
            "type": "ir.actions.act_window",
            "res_model": "planilla.export.file",
            "views": [[False, "form"]],
            "res_id": sfs_id.id,
            "target": "new",
        }
