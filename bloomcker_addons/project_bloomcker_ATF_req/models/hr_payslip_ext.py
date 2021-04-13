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