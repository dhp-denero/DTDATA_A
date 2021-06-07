# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging


class QuintaDetalExt(models.Model):
    _inherit = 'quinta.categoria.detalle'

    grat_compu = fields.Float(u'Proyección de Remuneración Computable', compute="_get_grat_compu")

    def _get_grat_compu(self):
        self.periodo
        elementos = self.env['hr.payslip.run'].search(
            [('date_start', '>=', self.periodo.date_start), ('date_end', '<=', self.periodo.date_stop)])
        if len(elementos) == 0:
            raise ValidationError(u'No existe Nomina para este periodo')

        nomina = elementos[0]
        proyec_remu = 0
        for i in nomina.slip_ids:
            if i.employee_id.id == self.empleado.id:
                proyec_remu = 0
                for j in i.line_ids:
                    if j.code == "PROYREM":
                        proyec_remu = j.total

        self.grat_compu = proyec_remu

class QuintaExt(models.Model):
    _inherit = 'quinta.categoria'

    @api.one
    def generar_data(self, elimina_detalle=True):
        if elimina_detalle:
            for i in self.detalle:
                i.unlink()
        self.ingresos_ord_afe = 0
        self.ingresos_extra_afe = 0
        self.retencion = 0
        elementos = self.env['hr.payslip.run'].search(
            [('date_start', '>=', self.periodo.date_start), ('date_end', '<=', self.periodo.date_stop)])
        if len(elementos) == 0:
            raise ValidationError(u'No existe Nomina para este periodo')
        config = self.env['planilla.quinta.categoria'].search([])
        if len(config) == 0:
            raise ValidationError(
                u'No esta configurado los parametros para Quinta Categoria')

        config = config[0]
        nomina = elementos[0]
        employees = []
        for i in nomina.slip_ids:
            if i.employee_id.id not in employees:
                if i.contract_id.regimen_laboral_empresa != 'practicante':
                    grati_julio = 0
                    grati_dicie = 0
                    proyec_remu = 0
                    for j in i.line_ids:
                        if j.code == "PROGRATI":
                            grati_julio = j.total
                        elif j.code == "GRATDIC":
                            grati_dicie = j.total
                        elif j.code == "PROYREM":
                            proyec_remu = j.total

                    sql = """
                        select distinct
                        min(hp.id) as slip_id,
                        coalesce(max(hc.gratificacion_fiesta_patria_proyectada),0) as gfp,
                        coalesce(max(hc.gratificacion_navidad_proyectada),0) as gnp,
                        min(hc.id) as contract_id,
                        min(he.id) as employee_id,
                        sum(case when hpl.code = '%s' then hpl.amount else 0 end) as roaq,
                        sum(case when hpl.code = '%s' then hpl.amount else 0 end) as rbq,
                        sum(case when hpl.code = '%s' then hpl.amount else 0 end) as reaq
                        from hr_payslip hp
                        inner join hr_contract hc on hc.id = hp.contract_id
                        inner join planilla_situacion ps on ps.id = hc.situacion_id
                        inner join hr_employee he on he.id = hp.employee_id
                        inner join hr_payslip_line hpl on hpl.slip_id = hp.id
                        where hp.payslip_run_id = %d
                        and hp.employee_id = %d
                        and ps.codigo = '1'
                        and hc.regimen_laboral_empresa not in ('practicante','microempresa')
                        group by hp.employee_id
                    """%(config.remuneracion_ordinaria_afecta.code,
                        config.remuneracion_basica_quinta.code,
                        config.remuneracion_extraordinaria_afecta.code,
                        i.payslip_run_id.id,
                        i.employee_id.id)
                    self.env.cr.execute(sql)
                    res = self.env.cr.dictfetchall()
                    if len(res) == 0:
                        continue
                    fecha_ini = fields.Date.from_string(self.periodo.date_start)

                    remuneracion_ordinaria_afecta = res[0]['roaq']
                    # remuneracion_basica_quinta = res[0]['rbq']
                    remuneracion_basica_quinta = proyec_remu
                    remuneracion_extraordinaria_afecta = res[0]['reaq']
                    if fecha_ini.month >= 7 and fecha_ini.month < 12:
                        gratificacion = self.env['planilla.gratificacion'].search([('year','=',self.periodo.fiscalyear_id.name),('tipo','=','07')])
                        if gratificacion:
                            line = next(iter(filter(lambda l:l.employee_id.id == i.employee_id.id,gratificacion.planilla_gratificacion_lines)),None)
                            gratificacion_julio = grati_julio
                        else:
                            gratificacion_julio = 0
                        gratificacion_diciembre = grati_dicie
                    elif fecha_ini.month == 12:
                        gratificacion = self.env['planilla.gratificacion'].search([('year','=',self.periodo.fiscalyear_id.name),('tipo','=','07')])
                        if gratificacion:
                            line = next(iter(filter(lambda l:l.employee_id.id == i.employee_id.id,gratificacion.planilla_gratificacion_lines)),None)
                            gratificacion_julio = grati_julio
                        else:
                            gratificacion_julio = 0
                        gratificacion = self.env['planilla.gratificacion'].search([('year','=',self.periodo.fiscalyear_id.name),('tipo','=','12')])
                        if gratificacion:
                            line = next(iter(filter(lambda l:l.employee_id.id == i.employee_id.id,gratificacion.planilla_gratificacion_lines)),None)
                            gratificacion_diciembre = grati_dicie
                        else:
                            gratificacion_diciembre = 0
                    else:
                        gratificacion_julio = grati_julio
                        gratificacion_diciembre = grati_dicie

                    # Culpa de Cleyner 07/06/2021
                    gratificacion_julio = grati_julio
                    gratificacion_diciembre = grati_dicie

                    respuesta = self.datos_quinta(config, i.employee_id,remuneracion_ordinaria_afecta, remuneracion_extraordinaria_afecta,
                                                gratificacion_julio, gratificacion_diciembre, 0, 0, 0, 0,remuneracion_basica_quinta)
                    if respuesta[0]:
                        respuesta = respuesta[0]
                        respuesta['slip_id'] = i.id
                        self.env['quinta.categoria.detalle'].create(respuesta)
                        self.ingresos_ord_afe += respuesta['ingresos_ord_afe']
                        self.ingresos_extra_afe += respuesta['ingresos_extra_afe']
                        self.retencion += respuesta['renta_total']
                        employees.append(i.employee_id.id)
        nomina.write({'flag':True})
        t = self.env['planilla.warning'].info(title='Resultado de importacion', message="SE CALCULO QUINTA DE MANERA EXITOSA!")
        return t

    @api.one
    def datos_quinta(self, config, employee_id, remuneracion_ordinaria_afecta, remuneracion_extraordinaria_afecta, gratificacion_julio, gratificacion_diciembre, remuneracion_m_anterior, retencion_m_anterior, rem_ord_otra_empresa, rem_ext_otra_empresa,remuneracion_basica_quinta,flag=False):

        equivalente = {
            '01': 12,
            '02': 11,
            '03': 10,
            '04': 9,
            '05': 8,
            '06': 7,
            '07': 6,
            '08': 5,
            '09': 4,
            '10': 3,
            '11': 2,
            '12': 1,
        }

        anterior = {
            '12': '11',
            '11': '10',
            '10': '09',
            '09': '08',
            '08': '07',
            '07': '06',
            '06': '05',
            '05': '04',
            '04': '03',
            '03': '02',
            '02': '01',
        }

        periodo_num = {
            0: '01/',
            1: '02/',
            2: '03/',
            3: '04/',
            4: '05/',
            5: '06/',
            6: '07/',
            7: '08/',
            8: '09/',
            9: '10/',
            10: '11/',
            11: '12/',
        }

        ant = 0.0
        ant_irre = 0
        rma,rtma = 0,0

        for ccc in range(int(self.periodo.code.split('/')[0])-1):
            anterior_grat = self.env['quinta.categoria.detalle'].search(
                [('periodo.code', '=', periodo_num[ccc] + self.periodo.code.split('/')[1]), ('empleado', '=', employee_id.id), ('padre', '!=', False)])
            print anterior_grat
            if len(anterior_grat) > 0:
                ant += anterior_grat[0].renum_comp
                ant_irre += anterior_grat[0].remun_extra_periodo
                if anterior_grat[0].remuneracion_m_anterior > 0:
                    rma = anterior_grat[0].remuneracion_m_anterior
                if anterior_grat[0].retencion_m_anterior > 0:
                    rtma = anterior_grat[0].retencion_m_anterior
        if remuneracion_m_anterior > 0.0:
            ant += remuneracion_m_anterior
        uits = self.env['planilla.5ta.uit'].search(
            [('planilla_id', '=', config.id), ('anio', '=', self.periodo.fiscalyear_id.id)])
        if len(uits) == 0:
            raise ValidationError(
                u'No esta configurado el valor UIT para el anio fiscal')

        val_uits = uits[0].valor

        respuesta = {}
        respuesta['remuneracion_m_anterior'] = rma
        respuesta['retencion_m_anterior'] = rtma
        respuesta['renum_comp'] = remuneracion_ordinaria_afecta
        respuesta['res_mes'] = equivalente[self.periodo.code.split('/')[0]]
        respuesta['proyec_anual'] = remuneracion_basica_quinta * (respuesta['res_mes'] - 1) + respuesta['renum_comp']
        respuesta['grat_julio'] = gratificacion_julio
        respuesta['grat_diciem'] = gratificacion_diciembre
        respuesta['renum_ant'] = ant
        respuesta['renum_ant_irre'] = ant_irre
        respuesta['renum_anual_proy'] = respuesta['proyec_anual'] + respuesta['grat_julio'] + respuesta['grat_diciem'] + respuesta['renum_ant'] + respuesta['renum_ant_irre']
        respuesta['_7uits'] = - (val_uits*7)
        respuesta['renta_neta_proy'] = respuesta['renum_anual_proy'] + respuesta['_7uits']
        if not flag:
            if respuesta['renta_neta_proy'] <= 0:
                return False

        acumulador = respuesta['renta_neta_proy']

        limite1 = self.env['planilla.5ta.limites'].search(
            [('planilla_id', '=', config.id), ('limite', '=', 1)])
        if len(limite1) == 0:
            raise ValidationError(
                u'No esta configurado el limite para la trama 1')
        limite1 = limite1[0].monto

        limite2 = self.env['planilla.5ta.limites'].search(
            [('planilla_id', '=', config.id), ('limite', '=', 2)])
        if len(limite2) == 0:
            raise ValidationError(
                u'No esta configurado el limite para la trama 2')
        limite2 = limite2[0].monto

        limite3 = self.env['planilla.5ta.limites'].search(
            [('planilla_id', '=', config.id), ('limite', '=', 3)])
        if len(limite3) == 0:
            raise ValidationError(
                u'No esta configurado el limite para la trama 3')
        limite3 = limite3[0].monto

        limite4 = self.env['planilla.5ta.limites'].search(
            [('planilla_id', '=', config.id), ('limite', '=', 4)])
        if len(limite4) == 0:
            raise ValidationError(
                u'No esta configurado el limite para la trama 4')
        limite4 = limite4[0].monto

        respuesta['tramo1'] = min(acumulador, limite1)
        acumulador -= respuesta['tramo1']

        respuesta['tramo2'] = min(acumulador, limite2 - limite1)
        acumulador -= respuesta['tramo2']

        respuesta['tramo3'] = min(acumulador, limite3 -limite2)
        acumulador -= respuesta['tramo3']

        respuesta['tramo4'] = min(acumulador, limite4 - limite3)
        acumulador -= respuesta['tramo4']

        respuesta['tramo5'] = acumulador

        tasa1 = self.env['planilla.5ta.tasas'].search(
            [('planilla_id', '=', config.id), ('limite', '=', 1)])
        if len(tasa1) == 0:
            raise ValidationError(
                u'No esta configurado la tasa para la trama 1')
        tasa1 = tasa1[0].tasa

        tasa2 = self.env['planilla.5ta.tasas'].search(
            [('planilla_id', '=', config.id), ('limite', '=', 2)])
        if len(tasa2) == 0:
            raise ValidationError(
                u'No esta configurado la tasa para la trama 2')
        tasa2 = tasa2[0].tasa

        tasa3 = self.env['planilla.5ta.tasas'].search(
            [('planilla_id', '=', config.id), ('limite', '=', 3)])
        if len(tasa3) == 0:
            raise ValidationError(
                u'No esta configurado la tasa para la trama 3')
        tasa3 = tasa3[0].tasa

        tasa4 = self.env['planilla.5ta.tasas'].search(
            [('planilla_id', '=', config.id), ('limite', '=', 4)])
        if len(tasa4) == 0:
            raise ValidationError(
                u'No esta configurado la tasa para la trama 4')
        tasa4 = tasa4[0].tasa

        tasa5 = self.env['planilla.5ta.tasas'].search(
            [('planilla_id', '=', config.id), ('limite', '=', 5)])
        if len(tasa5) == 0:
            raise ValidationError(
                u'No esta configurado la tasa para la trama 5')
        tasa5 = tasa5[0].tasa

        respuesta['impuesto1'] = respuesta['tramo1'] * tasa1 / 100
        respuesta['impuesto2'] = respuesta['tramo2'] * tasa2 / 100
        respuesta['impuesto3'] = respuesta['tramo3'] * tasa3 / 100
        respuesta['impuesto4'] = respuesta['tramo4'] * tasa4 / 100
        respuesta['impuesto5'] = respuesta['tramo5'] * tasa5 / 100

        factor = {
            '01': 12,
            '02': 11,
            '03': 10,
            '04': 9,
            '05': 8,
            '06': 7,
            '07': 6,
            '08': 5,
            '09': 4,
            '10': 3,
            '11': 2,
            '12': 1,
        }
        respuesta['retenciones_ant'] = 0
        if self.periodo.code.split('/')[0] in ('01'):
            pass
        elif self.periodo.code.split('/')[0] != '01':
            for i_e in range(int(self.periodo.code.split('/')[0])-1):
                tmp = self.env['quinta.categoria.detalle'].search(
                    [('periodo.code', '=', periodo_num[i_e] + self.periodo.fiscalyear_id.name), ('empleado', '=', employee_id.id), ('padre', '!=', False)])
                if len(tmp) > 0:
                    respuesta['retenciones_ant'] -= tmp[0].retencion
            respuesta['retenciones_ant'] -= retencion_m_anterior

        # if self.periodo.code.split('/')[0] in ('01', '02', '03'):
        #     respuesta['retenciones_ant'] = -retencion_m_anterior
        #     pass
        # elif self.periodo.code.split('/')[0] == '04':
        #     for i_e in range(3):
        #         tmp = self.env['quinta.categoria.detalle'].search(
        #             [('periodo.code', '=', periodo_num[i_e] + self.periodo.fiscalyear_id.name), ('empleado', '=', employee_id.id), ('padre', '!=', False)])
        #         if len(tmp) > 0:
        #             respuesta['retenciones_ant'] -= tmp[0].retencion
        #     respuesta['retenciones_ant'] -= retencion_m_anterior
        #
        # elif self.periodo.code.split('/')[0] in ('05', '06', '07'):
        #     for i_e in range(4):
        #         tmp = self.env['quinta.categoria.detalle'].search(
        #             [('periodo.code', '=', periodo_num[i_e] + self.periodo.fiscalyear_id.name), ('empleado', '=', employee_id.id), ('padre', '!=', False)])
        #         if len(tmp) > 0:
        #             respuesta['retenciones_ant'] -= tmp[0].retencion
        #     respuesta['retenciones_ant'] -= retencion_m_anterior
        #
        # elif self.periodo.code.split('/')[0] in ('08'):
        #     for i_e in range(7):
        #         tmp = self.env['quinta.categoria.detalle'].search(
        #             [('periodo.code', '=', periodo_num[i_e] + self.periodo.fiscalyear_id.name), ('empleado', '=', employee_id.id), ('padre', '!=', False)])
        #         if len(tmp) > 0:
        #             respuesta['retenciones_ant'] -= tmp[0].retencion
        #     respuesta['retenciones_ant'] -= retencion_m_anterior
        #
        # elif self.periodo.code.split('/')[0] in ('09', '10', '11'):
        #     for i_e in range(8):
        #         tmp = self.env['quinta.categoria.detalle'].search(
        #             [('periodo.code', '=', periodo_num[i_e] + self.periodo.fiscalyear_id.name), ('empleado', '=', employee_id.id), ('padre', '!=', False)])
        #         if len(tmp) > 0:
        #             respuesta['retenciones_ant'] -= tmp[0].retencion
        #     respuesta['retenciones_ant'] -= retencion_m_anterior
        #
        # elif self.periodo.code.split('/')[0] in ('12'):
        #     for i_e in range(11):
        #         tmp = self.env['quinta.categoria.detalle'].search(
        #             [('periodo.code', '=', periodo_num[i_e] + self.periodo.fiscalyear_id.name), ('empleado', '=', employee_id.id), ('padre', '!=', False)])
        #         if len(tmp) > 0:
        #             respuesta['retenciones_ant'] -= tmp[0].retencion
        #     respuesta['retenciones_ant'] -= retencion_m_anterior

        respuesta['renta_anual_proy'] = respuesta['impuesto1'] + respuesta['impuesto2'] + \
            respuesta['impuesto3'] + respuesta['impuesto4'] + \
            respuesta['impuesto5'] + respuesta['retenciones_ant']
        respuesta['factor'] = factor[self.periodo.code.split('/')[0]]
        respuesta['renta_mensual'] = respuesta['renta_anual_proy'] / \
            respuesta['factor']
        respuesta['remun_extra_periodo'] = remuneracion_extraordinaria_afecta
        respuesta['total_renta_neta_extra'] = respuesta['renta_neta_proy'] + \
            respuesta['remun_extra_periodo']

        acumulador = respuesta['total_renta_neta_extra']

        respuesta['etramo1'] = min(acumulador, limite1)
        acumulador -= respuesta['etramo1']

        respuesta['etramo2'] = min(acumulador, limite2 - limite1)
        acumulador -= respuesta['etramo2']

        respuesta['etramo3'] = min(acumulador, limite3 - limite2)
        acumulador -= respuesta['etramo3']

        respuesta['etramo4'] = min(acumulador, limite4 - limite3)
        acumulador -= respuesta['etramo4']

        respuesta['etramo5'] = acumulador

        respuesta['eimpuesto1'] = respuesta['etramo1'] * tasa1 / 100
        respuesta['eimpuesto2'] = respuesta['etramo2'] * tasa2 / 100
        respuesta['eimpuesto3'] = respuesta['etramo3'] * tasa3 / 100
        respuesta['eimpuesto4'] = respuesta['etramo4'] * tasa4 / 100
        respuesta['eimpuesto5'] = respuesta['etramo5'] * tasa5 / 100

        respuesta['renta_extraor'] = (respuesta['eimpuesto1'] + respuesta['eimpuesto2'] + respuesta['eimpuesto3'] + respuesta['eimpuesto4'] + respuesta['eimpuesto5'] - (
            respuesta['impuesto1'] + respuesta['impuesto2'] + respuesta['impuesto3'] + respuesta['impuesto4'] + respuesta['impuesto5']))  # / respuesta['factor']
        respuesta['renta_total'] = respuesta['renta_extraor'] + \
            respuesta['renta_mensual']

        # respuesta['retenciones_ant'] -= -respuesta['renta_extraor'] # Cleyner me obligo a quitar esta linea, Luis Millan 07/06/2021

        respuesta['padre'] = self.id
        respuesta['retencion'] = respuesta['renta_total']

        respuesta['periodo'] = self.periodo.id
        respuesta['dni'] = employee_id.identification_id
        respuesta['empleado'] = employee_id.id
        respuesta['ingresos_ord_afe'] = remuneracion_ordinaria_afecta
        respuesta['ingresos_extra_afe'] = remuneracion_extraordinaria_afecta

        return respuesta

    @api.one
    def add_employee(self, elimina_detalle=True):
        elementos = self.env['hr.payslip.run'].search(
            [('date_start', '=', self.periodo.date_start), ('date_end', '=', self.periodo.date_stop)])
        if len(elementos) == 0:
            raise ValidationError(u'No existe Nomina para este periodo')
        config = self.env['planilla.quinta.categoria'].search([])
        if len(config) == 0:
            raise ValidationError(
                u'No esta configurado los parametros para Quinta Categoria')

        config = config[0]
        nomina = elementos[0]
        employees = []
        for i in nomina.slip_ids:
            if i.employee_id not in employees:
                if i.employee_id.id == self.new_employee_id.id:
                    proyec_remu = 0
                    for j in i.line_ids:
                        if j.code == "PROYREM":
                            proyec_remu = j.total

                    sql = """
                        select distinct
                        min(hp.id) as slip_id,
                        coalesce(max(hc.gratificacion_fiesta_patria_proyectada),0) as gfp,
                        coalesce(max(hc.gratificacion_navidad_proyectada),0) as gnp,
                        min(hc.id) as contract_id,
                        min(he.id) as employee_id,
                        sum(case when hpl.code = '%s' then hpl.amount else 0 end) as roaq,
                        sum(case when hpl.code = '%s' then hpl.amount else 0 end) as rbq,
                        sum(case when hpl.code = '%s' then hpl.amount else 0 end) as reaq
                        from hr_payslip hp
                        inner join hr_contract hc on hc.id = hp.contract_id
                        inner join planilla_situacion ps on ps.id = hc.situacion_id
                        inner join hr_employee he on he.id = hp.employee_id
                        inner join hr_payslip_line hpl on hpl.slip_id = hp.id
                        where hp.payslip_run_id = %d
                        and hp.employee_id = %d
                        and ps.codigo = '1'
                        and hc.regimen_laboral_empresa not in ('practicante','microempresa')
                        group by hp.employee_id
                    """%(config.remuneracion_ordinaria_afecta.code,
                        config.remuneracion_basica_quinta.code,
                        config.remuneracion_extraordinaria_afecta.code,
                        i.payslip_run_id.id,
                        i.employee_id.id)
                    self.env.cr.execute(sql)
                    res = self.env.cr.dictfetchall()
                    if len(res) == 0:
                        raise ValidationError(u'El trabajador no tiene un contrato vigente: ' + i.employee_id.name_related)
                    fecha_ini = fields.Date.from_string(self.periodo.date_start)
                    remuneracion_ordinaria_afecta = res[0]['roaq']
                    # remuneracion_basica_quinta = res[0]['rbq']
                    remuneracion_basica_quinta = proyec_remu
                    remuneracion_extraordinaria_afecta = res[0]['reaq']
                    if fecha_ini.month >= 7 and fecha_ini.month < 12:
                        gratificacion = self.env['planilla.gratificacion'].search([('year','=',self.periodo.fiscalyear_id.name),('tipo','=','07')])
                        if gratificacion:
                            line = next(iter(filter(lambda l:l.employee_id.id == i.employee_id.id,gratificacion.planilla_gratificacion_lines)),None)
                            gratificacion_julio = line.total if line else 0
                        else:
                            gratificacion_julio = 0
                        gratificacion_diciembre = res[0]['gnp']
                    elif fecha_ini.month == 12:
                        gratificacion = self.env['planilla.gratificacion'].search([('year','=',self.periodo.fiscalyear_id.name),('tipo','=','07')])
                        if gratificacion:
                            line = next(iter(filter(lambda l:l.employee_id.id == i.employee_id.id,gratificacion.planilla_gratificacion_lines)),None)
                            gratificacion_julio = line.total if line else 0
                        else:
                            gratificacion_julio = 0
                        gratificacion = self.env['planilla.gratificacion'].search([('year','=',self.periodo.fiscalyear_id.name),('tipo','=','12')])
                        if gratificacion:
                            line = next(iter(filter(lambda l:l.employee_id.id == i.employee_id.id,gratificacion.planilla_gratificacion_lines)),None)
                            gratificacion_diciembre = line.total if line else 0
                        else:
                            gratificacion_diciembre = 0
                    else:
                        gratificacion_julio = res[0]['gfp']
                        gratificacion_diciembre = res[0]['gnp']
                    respuesta = self.datos_quinta(config, i.employee_id,remuneracion_ordinaria_afecta, remuneracion_extraordinaria_afecta,
                                                gratificacion_julio, gratificacion_diciembre, 0, 0, 0, 0,remuneracion_basica_quinta,True)
                    if respuesta[0]:
                        respuesta = respuesta[0]
                        respuesta['slip_id'] = i.id
                        respuesta['flag'] = True
                        self.env['quinta.categoria.detalle'].create(respuesta)
                        self.ingresos_ord_afe = self.ingresos_ord_afe + respuesta['ingresos_ord_afe']
                        self.ingresos_extra_afe = self.ingresos_extra_afe + respuesta['ingresos_extra_afe']
                        self.retencion = self.retencion + respuesta['renta_total']
                    employees.append(i.employee_id)
        t = self.env['planilla.warning'].info(title='Resultado de importacion', message="SE CALCULO QUINTA DE MANERA EXITOSA!")
        return t

    @api.one
    def actualizar_data(self):
        self.ingresos_ord_afe = 0
        self.ingresos_extra_afe = 0
        self.retencion = 0
        config = self.env['planilla.quinta.categoria'].search([])
        if len(config) == 0:
            raise ValidationError(
                u'No esta configurado los parametros para Quinta Categoria')
        else:
            if not config.remuneracion_basica_quinta or not config.remuneracion_extraordinaria_afecta or not config.remuneracion_ordinaria_afecta:
                raise UserError('Faltan Configuracion de Reglas Asociadas para Quinta Categoria')

        config = config[0]
        for row in self.detalle:
            remuneracion_ordinaria_afecta = self.env['hr.payslip.line'].search(
                [('slip_id', '=', row.slip_id.id), ('code', '=', config.remuneracion_ordinaria_afecta.code)]).amount
            # remuneracion_basica_quinta = self.env['hr.payslip.line'].search(
            #     [('slip_id', '=', row.slip_id.id), ('code', '=', config.remuneracion_basica_quinta.code)]).amount
            remuneracion_basica_quinta = self.env['hr.payslip.line'].search(
                [('slip_id', '=', row.slip_id.id), ('code', '=', 'PROYREM')]).amount
            remuneracion_extraordinaria_afecta = self.env['hr.payslip.line'].search(
                [('slip_id', '=', row.slip_id.id), ('code', '=', config.remuneracion_extraordinaria_afecta.code)]).amount
            respuesta = self.datos_quinta(config, row.empleado, remuneracion_ordinaria_afecta+row.rem_ord_otra_empresa, remuneracion_extraordinaria_afecta+row.rem_ext_otra_empresa,
                                          row.grat_julio, row.grat_diciem, row.remuneracion_m_anterior, row.retencion_m_anterior, row.rem_ord_otra_empresa, row.rem_ext_otra_empresa,remuneracion_basica_quinta+row.rem_ord_otra_empresa,row.flag)
            respuesta = respuesta[0]
            row.ingresos_ord_afe = respuesta['ingresos_ord_afe']
            row.ingresos_extra_afe = respuesta['ingresos_extra_afe']
            row.retencion = respuesta['retencion']
            row.renum_comp = respuesta['renum_comp']
            row.res_mes = respuesta['res_mes']
            row.proyec_anual = respuesta['proyec_anual']
            row.grat_julio = respuesta['grat_julio']
            row.grat_diciem = respuesta['grat_diciem']
            row.renum_ant = respuesta['renum_ant']
            row.renum_ant_irre = respuesta['renum_ant_irre']
            row.renum_anual_proy = respuesta['renum_anual_proy']
            row._7uits = respuesta['_7uits']
            row.renta_neta_proy = respuesta['renta_neta_proy']
            row.tramo1 = respuesta['tramo1']
            row.tramo2 = respuesta['tramo2']
            row.tramo3 = respuesta['tramo3']
            row.tramo4 = respuesta['tramo4']
            row.tramo5 = respuesta['tramo5']
            row.impuesto1 = respuesta['impuesto1']
            row.impuesto2 = respuesta['impuesto2']
            row.impuesto3 = respuesta['impuesto3']
            row.impuesto4 = respuesta['impuesto4']
            row.impuesto5 = respuesta['impuesto5']
            row.retenciones_ant = respuesta['retenciones_ant']
            row.renta_anual_proy = respuesta['renta_anual_proy']
            row.factor = respuesta['factor']
            row.renta_mensual = respuesta['renta_mensual']
            row.remun_extra_periodo = respuesta['remun_extra_periodo']
            row.total_renta_neta_extra = respuesta['total_renta_neta_extra']
            row.etramo1 = respuesta['etramo1']
            row.etramo2 = respuesta['etramo2']
            row.etramo3 = respuesta['etramo3']
            row.etramo4 = respuesta['etramo4']
            row.etramo5 = respuesta['etramo5']
            row.eimpuesto1 = respuesta['eimpuesto1']
            row.eimpuesto2 = respuesta['eimpuesto2']
            row.eimpuesto3 = respuesta['eimpuesto3']
            row.eimpuesto4 = respuesta['eimpuesto4']
            row.eimpuesto5 = respuesta['eimpuesto5']
            row.renta_extraor = respuesta['renta_extraor']
            row.renta_total = respuesta['renta_total']
            self.ingresos_ord_afe += respuesta['ingresos_ord_afe']
            self.ingresos_extra_afe += respuesta['ingresos_extra_afe']
            self.retencion += respuesta['renta_total']
