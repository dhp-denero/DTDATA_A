# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import sys
import io
from xlsxwriter.workbook import Workbook
import base64
import calendar
from decimal import *

class PlanillaCts(models.Model):
    _name = "planilla.cts"
    _rec_name = 'year'

    year = fields.Selection([
        ('2017', '2017'),
        ('2018', '2018'),
        ('2019', '2019'),
        ('2020', '2020'),
        ('2021', '2021'),
        ('2022', '2022'),
        ('2023', '2023'),
        ('2024', '2024'),
        ('2025', '2025'),
        ('2026', '2026'),
        ('2027', '2027'),
        ('2028', '2028'),
        ('2029', '2029'),
        ('2030', '2030'),
    ], string=u"Año")

    tipo = fields.Selection([('07', "CTS Mayo - Octubre"),
                             ('12', "CTS Noviembre - Abril")], "Mes", required=1)

    date_start = fields.Date()
    date_end = fields.Date()

    tipo_cambio = fields.Float("Tipo de Cambio", required=True,default=1)
    planilla_cts_lines = fields.One2many(
        'planilla.cts.line', 'planilla_cts_id', "Lineas")

    deposit_date = fields.Date(u'Fecha depósito')

    @api.multi
    @api.depends('tipo', 'year')
    @api.onchange('tipo', 'year')
    def change_dates(self):
        self.ensure_one()
        if self.year:
            if self.tipo == '07':
                self.date_start = date(int(self.year), 11, 1)
                self.date_end = date(int(self.year), 11, 30)
            else:
                self.date_start = date(int(self.year), 5, 1)
                self.date_end = date(int(self.year), 5, 31)

    @api.model
    def create(self, vals):
        if len(self.search([('year', '=', vals['year']), ('tipo', '=', vals['tipo'])])) >= 1:
            raise UserError(
                "Ya existe un registros %s %s" % (vals['year'], vals['tipo']))
        else:
            if vals['tipo'] == '07':
                vals['date_start'] = date(int(vals['year']), 11, 1)
                vals['date_end'] = date(int(vals['year']), 11, 30)
            else:
                vals['date_start'] = date(int(vals['year']), 5, 1)
                vals['date_end'] = date(int(vals['year']), 5, 31)
            return super(PlanillaCts, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals and "tipo"in vals:
            if vals['tipo'] == '07':
                vals['date_start'] = date(int(self.year), 11, 1)
                vals['date_end'] = date(int(self.year), 11, 30)
            else:
                vals['date_start'] = date(int(self.year), 5, 1)
                vals['date_end'] = date(int(self.year), 5, 31)
        return super(PlanillaCts, self).write(vals)

    @api.multi
    def unlink(self):
        nomina = self.env['hr.payslip.run'].search([('date_start', '=', self.date_start), 
                                                    ('date_end', '=', self.date_end)])
        nomina.write({'cts_flag':False})
        super(PlanillaCts,self).unlink()

    @api.model
    def get_parametros_cts(self):
        # self.ensure_one()
        parametros_cts = self.env['planilla.parametros.cts'].search([
        ], limit=1)

        if not parametros_cts.cod_cts.codigo \
                or not parametros_cts.cod_basico.code \
                or not parametros_cts.cod_asignacion_familiar.code \
                or not parametros_cts.cod_bonificaciones \
                or not parametros_cts.cod_comisiones \
                or not parametros_cts.cod_sobretiempos.code:

            raise UserError(
                'Debe crear un registro de ajustes en: Nomina->configuracion->parametros cts')

        # if not parametros_cts.cod_cts.codigo:
        #     raise UserError(
        #         'Debe configurar parametros de cts cod_cts Nomina->configuracion->parametros cts')
        # elif not parametros_cts.cod_basico.code:
        #     raise UserError(
        #         'Debe configurar parametros de cts cod_basico Nomina->configuracion->parametros cts')
        # elif not parametros_cts.cod_asignacion_familiar.code:
        #     raise UserError(
        #         'Debe configurar parametros de cts cod_asignacion_familiar Nomina->configuracion->parametros cts')
        # elif not parametros_cts.cod_bonificaciones.code:
        #     raise UserError(
        #         'Debe configurar parametros de cts cod_bonificaciones Nomina->configuracion->parametros cts')
        # elif not parametros_cts.cod_comisiones.code:
        #     raise UserError(
        #         'Debe configurar parametros de cts cod_comisiones Nomina->configuracion->parametros cts')
        # elif not parametros_cts.cod_dias_faltas.codigo:
        #     raise UserError(
        #         'Debe configurar parametros de cts cod_dias_faltas Nomina->configuracion->parametros cts')
        # elif not parametros_cts.cod_sobretiempos.code:
        #     raise UserError(
        #         'Debe configurar parametros de cts cod_sobretiempos Nomina->configuracion->parametros cts')
        else:
            return parametros_cts

    @api.multi
    def ver_wizard_cts_liquidacion_semestral(self):

        return {
            'name': 'Ver liquidacion semestral pdf',
            "type": "ir.actions.act_window",
            "res_model": "planilla.cts.liquidacion.semestral.wizard",
            'view_type': 'form',
            'view_mode': 'form',
            "views": [[False, "form"]],
            "target": "new"
            }
        
    @api.multi
    def calcular_cts(self):
        self.ensure_one()
        helper_liquidacion = self.env['planilla.helpers']
        parametros_gratificacion = self.env['planilla.gratificacion'].get_parametros_gratificacion(
        )
        self.planilla_cts_lines.unlink()

        parametros_cts = self.get_parametros_cts()

        # print parametros_cts.cod_he100.codigo
        if self.tipo == '07':  # mayo a octubre
            # el rango fin deberia ser 31 del mes 10
            # pero para asegurarme que al menos haya
            # un mes para que se le pague la cts
            # le aumentare la fecha final(para control resumen_periodo) que sea mayor a 31 del mes 10
            # ya que si es menor a esa fecha o bien seso y bien sesara el mes 7
            # por lo que le corresponderia no cts sino liquidacion
            #
            # para el rango de inicio para asegurarme de que tenga al menos un mes
            # el rango de inicio de resumen_periodo deberia ser como minimo menor o igual a el 1 del mes 10
            rango_inicio_contrato = date(int(self.year), 10, 1)
            rango_inicio_contrato_fin_mes = date(int(self.year), 10, calendar.monthrange(
                int(self.year), 10)[1])
            rango_fin_contrato = date(int(self.year), 10, 31)
            rango_inicio_planilla = date(int(self.year), 5, 1)
            rango_fin_planilla = date(int(self.year), 10, 31)
            # se usa para sacar los dia del periodo anterior
            anho_periodo_anterior = int(self.year)
            anho_gratificacion = int(self.year)
            tipo_periodo_anterior = '07'

        else:
            rango_inicio_contrato = date(int(self.year), 4, 1)

            rango_inicio_contrato_fin_mes = date(int(self.year), 4, calendar.monthrange(
                int(self.year), 4)[1])
            # rango_fin_contrato tiene que ser mayor sino, es liquidacion
            rango_fin_contrato = date(int(self.year), 4, 30)
            rango_inicio_planilla = date(int(self.year)-1, 11, 1)
            rango_fin_planilla = date(int(self.year), 4, 30)
            # se usa para sacar los dia del periodo anterior
            anho_periodo_anterior = int(self.year)-1
            anho_gratificacion = int(self.year)-1
            tipo_periodo_anterior = '12'

        query_gratificacion = """
        select 
        T.regimen_laboral_empresa,
        T.id,
        T.employee_id,
        T.identification_id, 
        T.a_paterno,
        T.a_materno,
        T.nombres,
        T.date_start,
        T.date_end,
        sum(faltas) as faltas,
        max(T.basico) as basico,
        max(T.afam) as afam,
        coalesce((select sum(total_gratificacion/6.0) 
                from planilla_gratificacion pg 
                inner join planilla_gratificacion_line pgl on pgl.planilla_gratificacion_id = pg.id 
                where employee_id = T.employee_id and year = '%s' and tipo = '%s'
                group by employee_id),0.0) as gratificacion,
        coalesce((select dias_proxima_fecha 
                from planilla_cts pc
                inner join planilla_cts_line pcl on pc.id= pcl.planilla_cts_id
                where employee_id = T.employee_id and year='%s' and tipo='%s'),0) as  dias
        from (
            select hc.id,hc.employee_id, hc.date_start,hc.date_end,
            he.identification_id,
            hc.regimen_laboral_empresa,
            he.a_paterno,
            he.a_materno,   
            he.nombres,
            (case when  hp.date_from>='%s' and hp.date_to<='%s'   then hp.basico else 0 end) as basico ,
            (case when ( date_from>='%s' and date_to<='%s'  ) then hp.asignacion_familiar else 0 end) as afam,
            hp.dias_faltas  as faltas
            from hr_payslip hp
            inner join hr_contract hc
            on hc.id = hp.contract_id
            inner join hr_employee he
            on he.id = hp.employee_id
            where ( date_start <= '%s' ) and (date_end is null or date_end>'%s')
            and( date_from>='%s' and date_to<='%s'  )
            ) as T
        group by T.id,T.employee_id,T.identification_id, T.a_paterno,T.a_materno,T.nombres,T.date_start,T.date_end,T.regimen_laboral_empresa
        order by T.id
        """ % (anho_gratificacion, tipo_periodo_anterior,  # self.tipo,
               anho_periodo_anterior, tipo_periodo_anterior,
               rango_inicio_contrato, rango_fin_planilla,
               rango_inicio_contrato, rango_fin_planilla,
               rango_inicio_contrato_fin_mes, rango_fin_contrato,
               rango_inicio_planilla, rango_fin_planilla)
        print("sql",query_gratificacion)
        self.env.cr.execute(query_gratificacion)

        contratos = self.env.cr.dictfetchall()

        # itero los rangos de fechas de cada resumen_periodo
        # el objetivo es encontrar el maximo rango de
        # fechas continuas
        fechas = list()
        for e,i in enumerate(range(len(contratos)),1):
            resumen_periodo = contratos[i]
            contratos_empleado = self.env['hr.contract'].search(
                [('employee_id', '=',  resumen_periodo['employee_id']),'|', ('date_end', '<=', resumen_periodo['date_end']),('date_end', '=', False )], order='date_end desc')
            fecha_ini = fields.Date.from_string(contratos_empleado[0].date_start)
            fecha_fin_contrato = fields.Date.from_string(contratos_empleado[0].date_end)
            # 2 busco los contratos anteriores que esten continuos(no mas de un dia de diferencia entre contratos)
            for i in range(1, len(contratos_empleado)):
                c_empleado = contratos_empleado[i]
                fecha_fin = fields.Date.from_string(c_empleado.date_end)
                if abs(((fecha_fin)-(fecha_ini)).days) == 1:
                    fecha_ini = fields.Date.from_string(c_empleado.date_start)
            fecha_fin = fecha_fin_contrato



            
            tmp_dias = 0
            dias_proxima_fecha = 0

            if fecha_ini < rango_inicio_planilla:
                fecha_computable = rango_inicio_planilla
            else:
                fecha_computable = fecha_ini
            print(resumen_periodo['employee_id'],fecha_computable,rango_fin_planilla)
            meses, tmp_dias = helper_liquidacion.diferencia_meses_dias(
                fecha_computable, rango_fin_planilla)
            print('diferencia',meses,tmp_dias)
            # los que esten en el mes de abril y octubre
            # los dias se que ddan en la cts actual
            # se van al siguiente semestre
            # el resto se queda
            if fecha_ini.month == 4 or fecha_ini.month == 10:
                dias_proxima_fecha = tmp_dias  # 30-fecha_ini.day+1
                tmp_dias = 0
            else:
                dias_proxima_fecha = 0

            fecha_inicio_nominas = date(
                fecha_computable.year, fecha_computable.month, 1)

            sql = """
                select min(hp.id),min(hp.name) as name
                from hr_payslip hp
                inner join hr_contract hc on hc.id = hp.contract_id
                where hp.date_from >= '%s'
                and hp.date_to <= '%s'
                and hp.employee_id = %d
                and hc.regimen_laboral_empresa not in ('practicante','microempresa')
                group by hp.employee_id, hp.payslip_run_id
            """%(fecha_inicio_nominas,rango_fin_planilla,resumen_periodo['employee_id'])
            self.env.cr.execute(sql)
            conceptos = self.env.cr.dictfetchall()
            #conceptos = conceptos.filtered(lambda x: x.contract_id.regimen_laboral_empresa != 'practicante')

            verificar_meses, _dias_tmp = helper_liquidacion.diferencia_meses_dias(
                fecha_inicio_nominas, rango_fin_planilla)
            if len(conceptos) < 1:
                continue
            if len(conceptos) != verificar_meses:
                fecha_encontradas = ' '.join(
                    ['\t-'+x['name']+'\n' for x in conceptos])
                if not fecha_encontradas:
                    fecha_encontradas = '"No tiene nominas"'
                raise UserError(
                    'Error en CTS: El empleado %s debe tener nominas desde:\n %s hasta %s pero solo tiene nominas en las siguientes fechas:\n %s \nfaltan %d nominas, subsanelas por favor ' % (
                        contratos_empleado[0].employee_id.name_related, fecha_inicio_nominas, rango_fin_planilla, fecha_encontradas, abs(len(
                            conceptos) - (verificar_meses))
                    ))


            lines = []
            contract_obj = self.env['hr.contract'].browse(resumen_periodo['id'])
            if contract_obj.hourly_worker:
                payslips = self.env['hr.payslip'].search([('employee_id','=',contract_obj.employee_id.id),
                                                            ('date_from','>=',rango_inicio_planilla),
                                                            ('date_to','<=',rango_fin_planilla)])
                for payslip in payslips:
                    lines.append(next(iter(filter(lambda l:l.code == 'BAS',payslip.line_ids)),None))
                basico = sum([line.amount for line in lines])/6.0
            else:
                basico = helper_liquidacion.getBasicoByDate(rango_inicio_planilla, rango_fin_planilla,
                                                        resumen_periodo['employee_id'], parametros_gratificacion.cod_basico.code)  # conceptos[0].basico if conceptos else 0.0
            if parametros_gratificacion.cod_dias_faltas:
                faltas = helper_liquidacion.getSumFaltas(fecha_inicio_nominas, rango_fin_planilla,
                                                    resumen_periodo['employee_id'], parametros_gratificacion.cod_dias_faltas.codigo)  # sum([x.dias_faltas for x in conceptos])
            else:
                faltas = 0
            afam = helper_liquidacion.getAsignacionFamiliarByDate(
                date(rango_fin_planilla.year, rango_fin_planilla.month, 1), rango_fin_planilla, resumen_periodo['employee_id'], parametros_gratificacion.cod_asignacion_familiar.code)

            comisiones_periodo, promedio_bonificaciones, promedio_horas_trabajo_extra = helper_liquidacion.calcula_comision_gratificacion_hrs_extras(
                contratos_empleado[0], fecha_computable, rango_fin_planilla, meses, rango_fin_planilla)

            bonificacion = promedio_bonificaciones
            comision = comisiones_periodo


            rem_computable = basico + afam + resumen_periodo['gratificacion'] + bonificacion + comision + promedio_horas_trabajo_extra
            if contract_obj.regimen_laboral_empresa == 'pequenhaempresa':
                rem_computable = rem_computable/2.0
            dias = int(resumen_periodo['dias'])
            dias = dias + tmp_dias

            monto_x_mes = float(Decimal(str(rem_computable/12.0)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            monto_x_dia = float(Decimal(str(monto_x_mes/30.0)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            monto_x_meses = float(Decimal(str(monto_x_mes*meses)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            monto_x_dias = float(Decimal(str(monto_x_dia*dias)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            total_faltas = float(Decimal(str(monto_x_dia*faltas)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

            cts_soles = monto_x_dias+monto_x_meses-total_faltas
            cts_interes = 0.0
            otros_dtos = 0.0
            cts_a_pagar = (cts_soles+cts_interes)-otros_dtos              

            tipo_cambio_venta = self.tipo_cambio
            cts_dolares = float(Decimal(str(cts_a_pagar/tipo_cambio_venta)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            cuenta_cts = contratos_empleado[0].employee_id.bacts_acc_number_rel
            banco = contratos_empleado[0].employee_id.bacts_bank_id_rel.id

            vals = {
                'planilla_cts_id': self.id,
                'orden': e,
                'employee_id': resumen_periodo['employee_id'],
                'identification_number': resumen_periodo['identification_id'],
                'last_name_father': resumen_periodo['a_paterno'],
                'last_name_mother': resumen_periodo['a_materno'],
                'names': resumen_periodo['nombres'],
                'fecha_ingreso': fecha_ini,
                'basico': basico,
                'a_familiar': afam,
                'gratificacion': resumen_periodo['gratificacion'],
                'horas_extras_mean': promedio_horas_trabajo_extra,
                'bonificacion': bonificacion,
                'comision': comisiones_periodo,
                'base': rem_computable,
                'monto_x_mes': monto_x_mes,
                'monto_x_dia': monto_x_dia,
                'faltas': faltas,
                'meses': meses,
                # este valor sera de utilidad para el calculo del siguiente periodo de cts
                'dias': dias,
                'monto_x_meses': monto_x_meses,
                'monto_x_dias':  monto_x_dias,
                'total_faltas':  total_faltas,
                'cts_soles': cts_soles,
                'intereses_cts': cts_interes,
                'otros_dtos': otros_dtos,
                'cts_a_pagar': cts_a_pagar,
                'tipo_cambio_venta': tipo_cambio_venta,
                'cts_dolares': cts_dolares,
                'cta_cts': cuenta_cts,
                'banco': banco,
                'dias_proxima_fecha': dias_proxima_fecha
            }
            self.planilla_cts_lines.create(vals)
        nomina = self.env['hr.payslip.run'].search([('date_start', '=', self.date_start),
                                                    ('date_end', '=', self.date_end)])
        nomina.write({'cts_flag':True})

        return self.env['planilla.warning'].info(title='Resultado de importacion', message="SE CALCULO CTS DE MANERA EXITOSA!")

    @api.multi
    def get_excel(self):
        # -------------------------------------------Datos---------------------------------------------------
        reload(sys)
        sys.setdefaultencoding('iso-8859-1')
        output = io.BytesIO()
        try:
            direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
        except: 
            raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
        
        workbook = Workbook(direccion+'CTS%s-%s.xlsx' % (self.year, self.tipo))
        worksheet = workbook.add_worksheet(
            'CTS%s-%s.xlsx' % (self.year, self.tipo))
        lines = self.env['planilla.cts.line'].search(
            [('planilla_cts_id', "=", self.id)])
        self.getCTSSheet(workbook, worksheet, lines,False)
        workbook.close()

        f = open(direccion+'CTS%s-%s.xlsx' % (self.year, self.tipo), 'rb')

        vals = {
            'output_name': 'CTS%s-%s.xlsx' % (self.year, dict(self._fields['tipo'].selection).get(self.tipo)),
            'output_file': base64.encodestring(''.join(f.readlines())),
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
    def resumen_pago(self):
        planilla_ajustes = self.env['planilla.ajustes'].search([], limit=1)
        reload(sys)
        sys.setdefaultencoding('iso-8859-1')
        output = io.BytesIO()

        try:
            direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
        except: 
            raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
        
        workbook=Workbook(direccion+'Resumen_pago_%s-%s.xlsx' % (self.year, self.tipo))
        worksheet = workbook.add_worksheet("Resumen")

        basic = {
            'align'		: 'left',
            'valign'	: 'vcenter',
            'text_wrap'	: 1,
            'font_size'	: 9,
            'font_name'	: 'Calibri'
        }

        percentage = basic.copy()
        percentage['align'] = 'right'
        percentage['num_format'] = '0.00%'

        percentage_y = percentage.copy()
        percentage_y['bg_color'] = '#F2E400'

        numeric = basic.copy()
        numeric['align'] = 'right'
        numeric['num_format'] = '#,##0.00'

        numeric_y = numeric.copy()
        numeric_y['bg_color'] = '#F2E400'

        numeric_gr = numeric.copy()
        numeric_gr['bg_color'] = '#CECECE'

        numeric_int = basic.copy()
        numeric_int['align'] = 'right'

        numeric_int_bold_format = numeric.copy()
        numeric_int_bold_format['bold'] = 1

        numeric_bold_format = numeric.copy()
        numeric_bold_format['bold'] = 1
        numeric_bold_format['num_format'] = '#,##0.00'

        bold = basic.copy()
        bold['bold'] = 1

        header = bold.copy()
        header['bg_color'] = '#CECECE'
        header['border'] = 1
        header['align'] = 'center'

        header_w = bold.copy()
        header_w['bg_color'] = '#FFFFFF'
        header_w['border'] = 1
        header_w['align'] = 'center'

        header_g = bold.copy()
        header_g['bg_color'] = '#4FA147'
        header_g['border'] = 1
        header_g['align'] = 'center'

        header_y = bold.copy()
        header_y['bg_color'] = '#F2E400'
        header_y['border'] = 1
        header_y['align'] = 'center'

        title = bold.copy()
        title['font_size'] = 15

        basic_format			= workbook.add_format(basic)
        bold_format			 = workbook.add_format(bold)
        percentage_format		= workbook.add_format(percentage)
        percentage_y_format		= workbook.add_format(percentage_y)
        numeric_int_format	  = workbook.add_format(numeric_int)
        numeric_y_format	  = workbook.add_format(numeric_y)
        numeric_gr_format	  = workbook.add_format(numeric_gr)
        numeric_int_bold_format = workbook.add_format(numeric_int_bold_format)
        numeric_format		  = workbook.add_format(numeric)
        numeric_bold_format	 = workbook.add_format(numeric_bold_format)
        title_format			= workbook.add_format(title)
        header_format		   = workbook.add_format(header)
        header_g_format		 = workbook.add_format(header_g)
        header_y_format		 = workbook.add_format(header_y)
        header_w_format		 = workbook.add_format(header_w)

        dts = {0:"lunes", 1:"martes", 2:u"miércoles", 3:"jueves", 4:"viernes", 5:u"sábado", 6:"domingo"}
        mts = {1:"enero", 2:"febrero", 3:"marzo", 4:"abril", 5:"mayo", 6:"junio", 7:"julio", 8:"agosto", 9:"septiembre", 10:"octubre", 11:"noviembre", 12:"diciembre"}

        rc = self.env['res.company'].search([])[0]
        worksheet.merge_range('A1:D1', rc.name.strip() if rc.name else '', title_format)
        worksheet.merge_range('A2:D2', ("RUC: "+planilla_ajustes.ruc) if planilla_ajustes else 'RUC: ', title_format)

        row = 5
        worksheet.merge_range(row,0,row,6, 'Pago CTS '+mts[fields.Date.from_string(self.date_start).month]+' '+self.year, header_format)

        row += 1
        col = 0
        pago_headers = [u'', u'Fecha depósito', u'Trabajador', u'DNI', u'BCO', u'Cuenta', u'Total a depositar']
        for ph in pago_headers:
            worksheet.write(row, col, ph, header_w_format)
            col += 1

        row += 1
        item = 1
        for i in self.planilla_cts_lines:
            col = 0
            worksheet.write(row, col, item, numeric_int_format)
            col += 1
            worksheet.write(row, col, self.deposit_date if self.deposit_date else '', basic_format)
            col += 1
            worksheet.write(row, col, i.employee_id.name_related if i.employee_id.name_related else '', basic_format)
            col += 1
            worksheet.write(row, col, i.employee_id.identification_id if i.employee_id.identification_id else '', basic_format)
            col += 1
            worksheet.write(row, col, i.employee_id.bacts_bank_id_rel.name if i.employee_id.bacts_bank_id_rel else '', basic_format)
            col += 1
            worksheet.write(row, col, i.employee_id.bacts_acc_number_rel if i.employee_id.bacts_acc_number_rel else '', basic_format)
            col += 1
            worksheet.write(row, col, i.cts_a_pagar if i.cts_a_pagar else 0, numeric_format)
            col += 1
            item += 1
            row += 1

        col_sizes = [13.57, 27.86]
        worksheet.set_column('A:B', col_sizes[0])
        worksheet.set_column('C:C', col_sizes[1])
        worksheet.set_column('D:G', col_sizes[0])

        workbook.close()

        f = open(direccion+'Resumen_pago_%s-%s.xlsx' % (self.year, self.tipo), 'rb')

        vals = {
            'output_name': 'Resumen_pago_%s-%s.xlsx' % (self.year, dict(self._fields['tipo'].selection).get(self.tipo)),
            'output_file': base64.encodestring(''.join(f.readlines())),
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
    def getCTSSheet(self, workbook, worksheet, lines,year):
                # ----------------Formatos------------------
        basic = {
            'align'		: 'left',
            'valign'	: 'vcenter',
            'text_wrap'	: 1,
            'font_size'	: 9,
            'font_name'	: 'Calibri'
        }

        basic_center = basic.copy()
        basic_center['align'] = 'center'

        numeric = basic.copy()
        numeric['align'] = 'right'
        numeric['num_format'] = '0.00'

        numeric_bold_format = numeric.copy()
        numeric_bold_format['bold'] = 1

        bold = basic.copy()
        bold['bold'] = 1

        header = bold.copy()
        header['bg_color'] = '#A9D0F5'
        header['border'] = 1
        header['align'] = 'center'

        title = bold.copy()
        title['font_size'] = 15

        basic_format = workbook.add_format(basic)
        basic_center_format = workbook.add_format(basic_center)
        numeric_format = workbook.add_format(numeric)
        bold_format = workbook.add_format(bold)
        numeric_bold_format = workbook.add_format(numeric_bold_format)
        header_format = workbook.add_format(header)
        title_format = workbook.add_format(title)

        nro_columnas = 17

        tam_col = [0]*nro_columnas

        # ----------------------------------------------Título--------------------------------------------------
        rc = self.env['res.company'].search([])[0]
        cabecera = rc.name
        worksheet.merge_range('A1:B1', cabecera, title_format)
        # ---------------------------------------------Cabecera------------------------------------------------
        worksheet.merge_range('A2:D2', "CTS", bold_format)
        worksheet.write('A3', u"Año :", bold_format)

        worksheet.write('B3', self.year if self.year != False else year, bold_format)

        columnas = ["Orden",
                    "Nro Documento",
                    "Apellido\nPaterno",
                    "Apellido\nMaterno",
                    "Nombres",
                    "Fecha\nIngreso",
                    u"Sueldo",
                    "A.\nFamiliar",
                    '1/6 Gratificacion',
                    "PROM. HRS\n EXTRAS",
                    u"Prom Bonificación",
                    u"Prom Comision",
                    'Base',
                    "Monto Mes",
                    u"M. por\nDía",
                    "Total\nFaltas",
                    'Meses',
                    'Dias',
                    'Monto\npor mes',
                    'Monto\npor dia',
                    'Monto\nfaltas',
                    "CTS soles",
                    "Intereses CTS",
                    "Otros dtos",
                    "CTS a Pagar",
                    u"Tipo de\ncambio de\nventa",
                    "CTS dolares",
                    "Cuenta CTS",
                    u"Banco"]
        fil = 4

        for col in range(len(columnas)):
            worksheet.write(fil, col, columnas[col], header_format)
        worksheet.set_row(fil, 30)

        # ------------------------------------------Insertando Data----------------------------------------------
        fil = 5
        # lines = self.env['planilla.cts.line'].search(
        #     [('planilla_cts_id', "=", self.id)])
        totals = [0]*29

        for line in lines:
            col = 0
            worksheet.write(fil, col, line.orden, basic_format)
            col += 1
            worksheet.write(fil, col, line.identification_number, basic_format)
            col += 1
            worksheet.write(fil, col, line.last_name_father, basic_format)
            col += 1
            worksheet.write(fil, col, line.last_name_mother, basic_format)
            col += 1
            worksheet.write(fil, col, line.names, basic_format)
            col += 1
            worksheet.write(fil, col, line.fecha_ingreso, basic_center_format)
            col += 1
            worksheet.write(fil, col, line.basico, numeric_format)
            totals[col] += line.basico
            col += 1
            worksheet.write(fil, col, line.a_familiar, numeric_format)
            totals[col] += line.a_familiar
            col += 1
            worksheet.write(fil, col, line.gratificacion, numeric_format)
            totals[col] += line.gratificacion
            col += 1
            worksheet.write(fil, col, line.horas_extras_mean, numeric_format)
            totals[col] += line.horas_extras_mean
            col += 1
            worksheet.write(
                fil, col, line.bonificacion, numeric_format)
            totals[col] += line.bonificacion
            col += 1
            worksheet.write(fil, col, line.comision, numeric_format)
            totals[col] += line.comision
            col += 1
            worksheet.write(fil, col, line.base, numeric_format)
            totals[col] += line.base
            col += 1
            worksheet.write(fil, col, line.monto_x_mes, numeric_format)
            totals[col] += line.monto_x_mes
            col += 1
            worksheet.write(fil, col, line.monto_x_dia, numeric_format)
            totals[col] += line.monto_x_dia
            col += 1
            worksheet.write(fil, col, line.faltas, numeric_format)
            totals[col] += line.faltas
            col += 1
            worksheet.write(fil, col, line.meses, numeric_format)
            totals[col] += line.meses
            col += 1
            worksheet.write(fil, col, line.dias, numeric_format)
            totals[col] += line.dias
            col += 1
            worksheet.write(fil, col, line.monto_x_meses, numeric_format)
            totals[col] += line.monto_x_meses
            col += 1
            worksheet.write(fil, col, line.monto_x_dias, numeric_format)
            totals[col] += line.monto_x_dias
            col += 1
            worksheet.write(fil, col, line.total_faltas, numeric_format)
            totals[col] += line.total_faltas
            col += 1
            worksheet.write(fil, col, line.cts_soles, numeric_format)
            totals[col] += line.cts_soles
            col += 1
            worksheet.write(fil, col, line.intereses_cts, numeric_format)
            totals[col] += line.intereses_cts
            col += 1
            worksheet.write(fil, col, line.otros_dtos, numeric_format)
            totals[col] += line.otros_dtos
            col += 1
            worksheet.write(fil, col, line.cts_a_pagar, numeric_format)
            totals[col] += line.cts_a_pagar
            col += 1
            worksheet.write(fil, col, line.tipo_cambio_venta, numeric_format)
            totals[col] += line.tipo_cambio_venta
            col += 1
            worksheet.write(fil, col, line.cts_dolares, numeric_format)
            totals[col] += line.cts_dolares
            col += 1
            worksheet.write(fil, col, line.cta_cts, basic_format)
            totals[col] += 0
            col += 1
            worksheet.write(fil, col, line.banco.name, basic_format)
            totals[col] += 0
            fil += 1

        col = 6
        for i in range(6, len(totals)):
            worksheet.write(fil, col, totals[i], numeric_bold_format)
            col += 1
        col_size = [5, 12, 20]
        worksheet.set_column('A:A', col_size[0])
        worksheet.set_column('B:E', col_size[1])
        worksheet.set_column('E:E', col_size[2])
        worksheet.set_column('G:U', col_size[1])


class PlanillaCtsLine(models.Model):
    _name = 'planilla.cts.line'

    planilla_cts_id = fields.Many2one(
        'planilla.cts', "Planilla CTS")
    employee_id = fields.Many2one(
        'hr.employee', "Empleado")
    identification_number = fields.Char("Nro Documento", size=9)
    last_name_father = fields.Char("Apellido Paterno")
    last_name_mother = fields.Char("Apellido Materno")
    names = fields.Char("Nombres")
    fecha_ingreso = fields.Date("Fecha Ingreso")

    basico = fields.Float(u"Básico", digits=(10, 2))
    a_familiar = fields.Float("A. Familiar", digits=(10, 2))
    gratificacion = fields.Float(u"1/6 Gratificación", digits=(10, 2))
    horas_extras_mean = fields.Float("Prom. Hras extras", digits=(10, 2))
    bonificacion = fields.Float(u"Bonificación", digits=(10, 2))
    comision = fields.Float(u"Comision", digits=(10, 2))
    base = fields.Float(u"Base", digits=(10, 2))
    monto_x_mes = fields.Float("M. por Mes", digits=(10, 2))
    monto_x_dia = fields.Float(u"M. por Día", digits=(10, 2))
    faltas = fields.Integer("Faltas")
    meses = fields.Integer("Meses")
    # este valor sera de utilidad para el calculo del siguiente periodo de cts
    dias = fields.Integer(u"Días")
    dias_proxima_fecha = fields.Integer(u"Días proxima fecha")
    monto_x_meses = fields.Float("Monto. Por los\nMeses", digits=(10, 2))
    monto_x_dias = fields.Float(u"Monto. Por los\nDías", digits=(10, 2))
    total_faltas = fields.Float("Total Faltas", digits=(10, 2))
    cts_soles = fields.Float("CTS \n Soles", digits=(10, 2))
    intereses_cts = fields.Float("Intereses \n CTS", digits=(10, 2))
    otros_dtos = fields.Float("Otros \n Cdtos", digits=(10, 2))
    cts_a_pagar = fields.Float("CTS a\n Pagar", digits=(10, 2))
    tipo_cambio_venta = fields.Float("Tipo de\nCambio\nVenta", digits=(10, 2))
    cts_dolares = fields.Float("CTS \nDolares", digits=(10, 2))
    cta_cts = fields.Char("CTA \nCTS")
    banco = fields.Many2one(
        string=u'Banco',
        comodel_name='res.bank',
        ondelete='set null',
    )
    orden = fields.Integer("Orden")

    @api.onchange('cts_soles', 'otros_dtos', 'intereses_cts')
    def _recalcula_cts(self):
        self.cts_a_pagar = self.cts_soles+self.intereses_cts-self. otros_dtos