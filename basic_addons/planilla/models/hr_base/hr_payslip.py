import time
from datetime import datetime, timedelta
from dateutil import relativedelta

import babel

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from decimal import *
from math import modf


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    _description = 'Pay Slip'

    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Batches', readonly=True,
                                     copy=False, states={
                                         'draft': [('readonly', False)]},
                                     ondelete='cascade'
                                     )

    line_ids = fields.One2many('hr.payslip.line', 'slip_id', string='Payslip Lines', readonly=True,
                               states={'draft': [('readonly', False)]}, domain=[('appears_on_payslip', '=', True)])

    feriados = fields.Integer("Feriados y Domingos")
    dias_calendarios = fields.Integer(
        'Dias Calendarios')

    # variables que se usaran en la nomina
    basico = fields.Float(string='Basico', digits=(12, 2))
    asignacion_familiar = fields.Float(
        string='Asignacion Familiar', digits=(12, 2))
    bonificacion_9 = fields.Float(string='Bonificacion 9%', digits=(12, 2))
    dias_faltas = fields.Float(string='Faltas', digits=(12, 2))
    comisiones = fields.Float(string='Comisiones', digits=(12, 2))
    bonificaciones = fields.Float(string='Bonificaciones', digits=(12, 2))
    sobretiempos = fields.Float(string='sobretiempos', digits=(12, 2))

    basico_cts = fields.Float(string='Basico CTS', digits=(12, 2))
    asignacion_familiar_cts = fields.Float(
        string='Asignacion Familiar CTS', digits=(12, 2))
    dias_faltas_cts = fields.Float(string='Faltas CTS', digits=(12, 2))
    sobretiempos_cts = fields.Float(string='sobretiempos CTS', digits=(12, 2))

    afiliacion_rel = fields.Char(
        'Afiliacion', related='contract_id.afiliacion_id.entidad')
    periodos_devengue = fields.One2many('hr.devengue','slip_id')
    essalud = fields.Float()

    @api.multi
    def action_payslip_cancel(self):
        self.line_ids.unlink()
        return super(HrPayslip, self).action_payslip_cancel()

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
            ruta+"planilla_tmp.pdf", pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20)

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
        # str(int(self.env.cr.dictfetchone()['horas']))
        total_sobretiempo = self.env.cr.dictfetchone()
        for payslip in payslips:
            dias_faltas += self.env['hr.payslip.worked_days'].search([('code', '=', planilla_ajustes.cod_dias_no_laborados.codigo if planilla_ajustes else ''), 
                                                                    ('payslip_id', '=', payslip.id)], limit=1).number_of_days
        if self.employee_id.calendar_id:
            total = self.employee_id.calendar_id.average_hours if self.employee_id.calendar_id.average_hours > 0 else 8
        else:
            total = 8
            #raise UserError(u'Este empleado no tiene un Horario establecido.')
        total_horas_jornada_ordinaria = 0
        for payslip in payslips:
            if payslip.contract_id.hourly_worker:
                total_horas_jornada_ordinaria += sum(payslip.worked_days_line_ids.filtered(lambda l:l.code == planilla_ajustes.cod_dias_laborados.codigo).mapped('number_of_hours'))

        if self.employee_id.calendar_id:
            total = self.employee_id.calendar_id.average_hours if self.employee_id.calendar_id.average_hours > 0 else 8
        else:
            total = 8
        # formula para los dias laborados segun sunat
        total_horas_minutos = modf(int(dias_laborados-dias_faltas)*total) if total_horas_jornada_ordinaria == 0 else total_horas_jornada_ordinaria
        total_horas_jornada_ordinaria = total_horas_minutos[1]
        total_minutos_jornada_ordinaria = Decimal(str(total_horas_minutos[0] * 60)).quantize(Decimal('1.'), rounding=ROUND_HALF_UP)
        # busco cualquier campo ya que lo unico que quiero es usar la funcionalidad de la generacion de la boleta
        payslip_run = self.env['hr.payslip.run']

        payslip_run.genera_boleta_empleado(self.date_from, self.date_to, payslips, str(dias_no_laborados), str(int(dias_laborados - dias_faltas)), str(total_horas_jornada_ordinaria), str(total_minutos_jornada_ordinaria), (total_sobretiempo), str(dias_subsidiados), elements,
                                           company, categories, planilla_ajustes)
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

    @api.multi
    def reabrir(self):
        self.state = 'draft'

    '''
    hr_payroll_account crea asientos contables
    estoy sobrescribiendo la funcion
    para que no escriba los asientos contables y vaya directo al padre
    y solo genere las hojas
    '''
    @api.multi
    def action_payslip_done(self):
        if self.line_ids:
            self.line_ids.unlink()
        self.compute_sheet()
        return self.write({'state': 'done'})

    @api.multi
    def compute_sheet(self):
        config = self.env['planilla.quinta.categoria'].search([])
        if len(config) == 0:
            raise ValidationError(
                u'No esta configurado los parametros para Quinta Categoria')
        config = config[0]
        self.env.cr.execute("""delete from hr_payslip_line 
                            where employee_id = """+str(self.employee_id.id)+""" and slip_id = """+str(self.id))
        super(HrPayslip, self).compute_sheet()

    @api.multi
    def load_entradas_tareos(self):

        self.worked_days_line_ids.unlink()
        self.input_line_ids.unlink()

        inputs = self.env['planilla.inputs.nomina'].search([])
        worked_days = self.env['planilla.worked.days'].search([])

        for worked_day in worked_days:
            data = {'name': worked_day.descripcion,
                    'payslip_id': self.id,
                    'code': worked_day.codigo,
                    'number_of_days': worked_day.dias,
                    'number_of_hours': worked_day.horas,
                    'minutos': worked_day.minutos,
                    'tasa': worked_day.tasa_monto,
                    'contract_id': self.contract_id.id,
                    }
            self.env['hr.payslip.worked_days'].create(data)

        for my_input in inputs:
            data = {'name': my_input.descripcion,
                    'payslip_id': self.id,
                    'code': my_input.codigo,
                    'amount': 0,
                    'contract_id': self.contract_id.id,
                    }
            self.env['hr.payslip.input'].create(data)

class HrDevengue(models.Model):
    _name = 'hr.devengue'

    slip_id = fields.Many2one('hr.payslip','Nomina')
    periodo_devengue = fields.Many2one('hr.payslip.run','Periodo Devengue')
    dias = fields.Integer('Dias de Vacaciones')
    employee_id = fields.Many2one('hr.employee','Empleado')

    @api.multi
    def create(self,vals):
        t = super(HrDevengue,self).create(vals)
        t.write({'employee_id':self.env['hr.payslip'].browse(t.slip_id.id).employee_id.id})
        return t