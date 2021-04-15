# -*- encoding: utf-8 -*-
import base64
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime
from odoo.exceptions import UserError
from openerp.osv import osv


class planilla_5ta_uit(models.Model):
    _name = 'planilla.5ta.uit'

    planilla_id = fields.Many2one('planilla.quinta.categoria', 'Padre')
    anio = fields.Many2one('account.fiscalyear', u'Anio')
    valor = fields.Float('Valor')

    _order = 'anio'


class planilla_5ta_limites(models.Model):
    _name = 'planilla.5ta.limites'

    planilla_id = fields.Many2one('planilla.quinta.categoria', 'Padre')
    limite = fields.Integer(u'Limite')
    monto = fields.Float('Monto')

    _order = 'limite'


class planilla_5ta_tasas(models.Model):
    _name = 'planilla.5ta.tasas'

    planilla_id = fields.Many2one('planilla.quinta.categoria', 'Padre')
    limite = fields.Integer(u'Limite')
    tasa = fields.Float('Tasa')

    _order = 'limite'


class planilla_quinta_categoria(models.Model):
    _name = "planilla.quinta.categoria"

    uits = fields.One2many('planilla.5ta.uit', 'planilla_id', 'Uit')
    limites = fields.One2many('planilla.5ta.limites', 'planilla_id', 'Limites')
    tasas = fields.One2many('planilla.5ta.tasas', 'planilla_id', 'Tasas')

    remuneracion_ordinaria_afecta = fields.Many2one(
        'hr.salary.rule', u'Remuneracion Ordinaria Afecta')
    remuneracion_basica_quinta = fields.Many2one(
        'hr.salary.rule',u'Remuneracion Basica Quinta')
    remuneracion_extraordinaria_afecta = fields.Many2one(
        'hr.salary.rule', u'Remuneracion Extraordinaria Afecta')
    gratificacion_fiesta_navidad = fields.Many2one(
        'hr.salary.rule', u'Gratificacion Fiestas Patrias y Navidad')

    ingreso_predeterminado = fields.Many2one(
        'planilla.inputs.nomina', u'Input para Retencion de Quinta Categoria')

    @api.model
    def create(self, vals):
        if len(self.env['planilla.quinta.categoria'].search([])) >= 1:
            raise ValidationError(
                "Solo puede haber un registro de configuracion de Quinta Categoria!")
        else:
            return super(planilla_quinta_categoria, self).create(vals)


class quinta_categoria_detalle(models.Model):
    _name = 'quinta.categoria.detalle'

    periodo = fields.Many2one('account.period', 'Periodo')
    dni = fields.Char('DNI')
    empleado = fields.Many2one('hr.employee', 'Empleado')
    ingresos_ord_afe = fields.Float(u'Ingresos Ordinario Afectos')
    ingresos_extra_afe = fields.Float(u'Ingresos Extraordinario Afectos')
    retencion = fields.Float(u'Retencion')

    padre = fields.Many2one('quinta.categoria', 'Padre')

    renum_comp = fields.Float(u'Remuneracion Computable')
    res_mes = fields.Float(u'X Resto de Meses')
    proyec_anual = fields.Float(u'Total Proyectado Anual')
    grat_julio = fields.Float(u'Gratificacion de Julio')
    grat_diciem = fields.Float(u'Gratificacion de Diciembre')
    renum_ant = fields.Float(u'Remuneraciones Regulares de Meses Anteriores')
    renum_ant_irre = fields.Float(
        u'Remuneraciones Irregulares de Meses Anteriores')
    renum_anual_proy = fields.Float(u'Remuneracion Anual Proyectada')
    _7uits = fields.Float(u'Deduccion 7 UITS')
    renta_neta_proy = fields.Float(u'Renta Neta Anual Proyectada')
    tramo1 = fields.Float(u'Tramo 1')
    tramo2 = fields.Float(u'Tramo 2')
    tramo3 = fields.Float(u'Tramo 3')
    tramo4 = fields.Float(u'Tramo 4')
    tramo5 = fields.Float(u'Tramo 5')
    impuesto1 = fields.Float(u'Impuesto Tramo 1')
    impuesto2 = fields.Float(u'Impuesto Tramo 2')
    impuesto3 = fields.Float(u'Impuesto Tramo 3')
    impuesto4 = fields.Float(u'Impuesto Tramo 4')
    impuesto5 = fields.Float(u'Impuesto Tramo 5')
    retenciones_ant = fields.Float(u'(-) Retenciones Meses Anteriores')
    renta_anual_proy = fields.Float(u'Renta Anual Proyectada')
    factor = fields.Float(u'Factor')
    renta_mensual = fields.Float(u'Renta Mensual')
    remun_extra_periodo = fields.Float(
        u'Remuneraciones Extraordinarias del Periodo')
    total_renta_neta_extra = fields.Float(
        u'Total Renta Neta Incluidas las Remuneraciones Extraordinarias')
    etramo1 = fields.Float(u'Tramo 1')
    etramo2 = fields.Float(u'Tramo 2')
    etramo3 = fields.Float(u'Tramo 3')
    etramo4 = fields.Float(u'Tramo 4')
    etramo5 = fields.Float(u'Tramo 5')
    eimpuesto1 = fields.Float(u'Impuesto Tramo 1')
    eimpuesto2 = fields.Float(u'Impuesto Tramo 2')
    eimpuesto3 = fields.Float(u'Impuesto Tramo 3')
    eimpuesto4 = fields.Float(u'Impuesto Tramo 4')
    eimpuesto5 = fields.Float(u'Impuesto Tramo 5')
    renta_extraor = fields.Float(u'Retencion de Conceptos Extraordinarios')
    renta_total = fields.Float(u'Retencion Mensual Total')

    remuneracion_m_anterior = fields.Float("Remuneracion meses anteriores")
    retencion_m_anterior = fields.Float("Retencion meses anteriores")

    rem_ord_otra_empresa = fields.Float("Remuneracion ordinaria otra empresa")
    rem_ext_otra_empresa = fields.Float(
        "Remuneracion extraordinaria otra empresa")
    slip_id = fields.Many2one(
        string=u'slip_id',
        comodel_name='hr.payslip',
        ondelete='set null',
    )
    flag = fields.Boolean(default=False)


class quinta_categoria(models.Model):
    _name = 'quinta.categoria'

    periodo = fields.Many2one('account.period', 'Periodo')
    ingresos_ord_afe = fields.Float(u'Ingresos Ordinario Afectos')
    ingresos_extra_afe = fields.Float(u'Ingresos Extraordinario Afectos')
    retencion = fields.Float(u'Retencion')
    new_employee_id = fields.Many2one('hr.employee','Nuevo Empleado')
    detalle = fields.One2many('quinta.categoria.detalle', 'padre', 'Detalle')

    @api.multi
    def unlink(self):
        nomina = self.env['hr.payslip.run'].search(
            [('date_start', '=', self.periodo.date_start), ('date_end', '=', self.periodo.date_stop)])
        nomina.write({'flag':False})
        super(quinta_categoria, self).unlink()

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
            remuneracion_basica_quinta = self.env['hr.payslip.line'].search(
                [('slip_id', '=', row.slip_id.id), ('code', '=', config.remuneracion_basica_quinta.code)]).amount
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
            '02': 12,
            '03': 12,
            '04': 9,
            '05': 8,
            '06': 8,
            '07': 8,
            '08': 5,
            '09': 4,
            '10': 4,
            '11': 4,
            '12': 1,
        }
        respuesta['retenciones_ant'] = 0
        if self.periodo.code.split('/')[0] in ('01', '02', '03'):
            respuesta['retenciones_ant'] = -retencion_m_anterior
            pass
        elif self.periodo.code.split('/')[0] == '04':
            for i_e in range(3):
                tmp = self.env['quinta.categoria.detalle'].search(
                    [('periodo.code', '=', periodo_num[i_e] + self.periodo.fiscalyear_id.name), ('empleado', '=', employee_id.id), ('padre', '!=', False)])
                if len(tmp) > 0:
                    respuesta['retenciones_ant'] -= tmp[0].retencion
            respuesta['retenciones_ant'] -= retencion_m_anterior

        elif self.periodo.code.split('/')[0] in ('05', '06', '07'):
            for i_e in range(4):
                tmp = self.env['quinta.categoria.detalle'].search(
                    [('periodo.code', '=', periodo_num[i_e] + self.periodo.fiscalyear_id.name), ('empleado', '=', employee_id.id), ('padre', '!=', False)])
                if len(tmp) > 0:
                    respuesta['retenciones_ant'] -= tmp[0].retencion
            respuesta['retenciones_ant'] -= retencion_m_anterior

        elif self.periodo.code.split('/')[0] in ('08'):
            for i_e in range(7):
                tmp = self.env['quinta.categoria.detalle'].search(
                    [('periodo.code', '=', periodo_num[i_e] + self.periodo.fiscalyear_id.name), ('empleado', '=', employee_id.id), ('padre', '!=', False)])
                if len(tmp) > 0:
                    respuesta['retenciones_ant'] -= tmp[0].retencion
            respuesta['retenciones_ant'] -= retencion_m_anterior

        elif self.periodo.code.split('/')[0] in ('09', '10', '11'):
            for i_e in range(8):
                tmp = self.env['quinta.categoria.detalle'].search(
                    [('periodo.code', '=', periodo_num[i_e] + self.periodo.fiscalyear_id.name), ('empleado', '=', employee_id.id), ('padre', '!=', False)])
                if len(tmp) > 0:
                    respuesta['retenciones_ant'] -= tmp[0].retencion
            respuesta['retenciones_ant'] -= retencion_m_anterior

        elif self.periodo.code.split('/')[0] in ('12'):
            for i_e in range(11):
                tmp = self.env['quinta.categoria.detalle'].search(
                    [('periodo.code', '=', periodo_num[i_e] + self.periodo.fiscalyear_id.name), ('empleado', '=', employee_id.id), ('padre', '!=', False)])
                if len(tmp) > 0:
                    respuesta['retenciones_ant'] -= tmp[0].retencion
            respuesta['retenciones_ant'] -= retencion_m_anterior

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

        respuesta['padre'] = self.id
        respuesta['retencion'] = respuesta['renta_total']

        respuesta['periodo'] = self.periodo.id
        respuesta['dni'] = employee_id.identification_id
        respuesta['empleado'] = employee_id.id
        respuesta['ingresos_ord_afe'] = remuneracion_ordinaria_afecta
        respuesta['ingresos_extra_afe'] = remuneracion_extraordinaria_afecta

        return respuesta

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
            grati_julio = 0
            grati_dicie = 0
            for j in i.line_ids:
                if j.code == "PROGRATI":
                    grati_julio = j.total
                elif j.code == "GRATDIC":
                    grati_dicie = j.total

            if i.employee_id.id not in employees:
                if i.contract_id.regimen_laboral_empresa != 'practicante':
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
                        #raise ValidationError(u'El trabajador no tiene un contrato vigente: ' + i.employee_id.name_related)
                    fecha_ini = fields.Date.from_string(self.periodo.date_start)
                    remuneracion_ordinaria_afecta = res[0]['roaq']
                    remuneracion_basica_quinta = res[0]['rbq']
                    remuneracion_extraordinaria_afecta = res[0]['reaq']
                    if fecha_ini.month >= 7 and fecha_ini.month < 12:
                        gratificacion = self.env['planilla.gratificacion'].search([('year','=',self.periodo.fiscalyear_id.name),('tipo','=','07')])
                        if gratificacion:
                            line = next(iter(filter(lambda l:l.employee_id.id == i.employee_id.id,gratificacion.planilla_gratificacion_lines)),None)
                            # gratificacion_julio = line.total if line else 0
                            gratificacion_julio = grati_julio
                        else:
                            gratificacion_julio = 0
                        # gratificacion_diciembre = res[0]['gnp']
                        gratificacion_diciembre = grati_dicie
                    elif fecha_ini.month == 12:
                        gratificacion = self.env['planilla.gratificacion'].search([('year','=',self.periodo.fiscalyear_id.name),('tipo','=','07')])
                        if gratificacion:
                            line = next(iter(filter(lambda l:l.employee_id.id == i.employee_id.id,gratificacion.planilla_gratificacion_lines)),None)
                            # gratificacion_julio = line.total if line else 0
                            gratificacion_julio = grati_julio
                        else:
                            gratificacion_julio = 0
                        gratificacion = self.env['planilla.gratificacion'].search([('year','=',self.periodo.fiscalyear_id.name),('tipo','=','12')])
                        if gratificacion:
                            line = next(iter(filter(lambda l:l.employee_id.id == i.employee_id.id,gratificacion.planilla_gratificacion_lines)),None)
                            # gratificacion_diciembre = line.total if line else 0
                            gratificacion_diciembre = grati_dicie
                        else:
                            gratificacion_diciembre = 0
                    else:
                        # gratificacion_julio = res[0]['gfp']
                        gratificacion_julio = grati_julio
                        # gratificacion_diciembre = res[0]['gnp']
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
                    remuneracion_basica_quinta = res[0]['rbq']
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

    @api.multi
    def excel_export(self):
        import io
        from xlsxwriter.workbook import Workbook
        output = io.BytesIO()

        if len(self.detalle) < 1:
            raise osv.except_osv('Alerta','Primero debe generar quinta.')

        ########### PRIMERA HOJA DE LA DATA EN TABLA
        #workbook = Workbook(output, {'in_memory': True})

        try:
            direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
        except:
            raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
        workbook = Workbook(direccion +'quinta_categoria.xlsx')
        worksheet = workbook.add_worksheet("Kardex")
        bold = workbook.add_format({'bold': True})
        bold.set_font_size(8)
        normal = workbook.add_format()
        boldbord = workbook.add_format({'bold': True})
        boldbord.set_border(style=2)
        boldbord.set_align('center')
        boldbord.set_align('vcenter')
        boldbord.set_text_wrap()
        boldbord.set_font_size(8)
        boldbord.set_bg_color('#DCE6F1')

        especial1 = workbook.add_format({'bold': True})
        especial1.set_align('center')
        especial1.set_align('vcenter')
        especial1.set_text_wrap()
        especial1.set_font_size(15)

        especial2 = workbook.add_format({'bold': True})
        especial2.set_align('center')
        especial2.set_align('vcenter')
        especial2.set_text_wrap()
        especial2.set_font_size(8)

        especial3 = workbook.add_format({'bold': True})
        especial3.set_align('left')
        especial3.set_align('vcenter')
        especial3.set_text_wrap()
        especial3.set_font_size(15)

        numbertres = workbook.add_format({'num_format':'0.000'})
        numberdos = workbook.add_format({'num_format':'0.00'})
        numberseis = workbook.add_format({'num_format':'0.00'})
        numberseis.set_font_size(8)
        numberocho = workbook.add_format({'num_format':'0.00'})
        numberocho.set_font_size(8)
        bord = workbook.add_format()
        bord.set_border(style=1)
        bord.set_font_size(8)
        numberdos.set_border(style=1)
        numberdos.set_font_size(8)
        numbertres.set_border(style=1)
        numberseis.set_border(style=1)
        numberocho.set_border(style=1)
        numberdosbold = workbook.add_format({'num_format':'0.00','bold':True})
        numberdosbold.set_font_size(8)
        x= 10
        tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        tam_letra = 1.2
        import sys
        reload(sys)
        sys.setdefaultencoding('iso-8859-1')

        worksheet.merge_range(1,0,1,4,"QUINTA CATEGORIA", especial3)

        import datetime

        worksheet.write(4,0,"Periodo: ",especial1)
        worksheet.write(4,1,self.periodo.name,especial1)
        worksheet.write(6,0,"Retencion: ",especial1)
        worksheet.write(6,1,round(self.retencion,2) if self.retencion else 0.00,especial1)
        worksheet.write(4,3,"Ing. Ord. Afec.",especial1)
        worksheet.write(4,4,round(self.ingresos_ord_afe,2) if self.ingresos_ord_afe else 0.00,especial1)
        worksheet.write(6,3,"Ing. Extr. Afec.",especial1)
        worksheet.write(6,4,round(self.ingresos_extra_afe,2) if self.ingresos_extra_afe else 0.00,especial1)

        worksheet.write(8,0,"Periodo",boldbord)
        worksheet.write(8,1,"DNI",boldbord)
        worksheet.write(8,2,"Empleado",boldbord)
        worksheet.write(8,3,"Ingresos Ordinario Afectos",boldbord)
        worksheet.write(8,4,"Ingresos Extraordinario Afectos",boldbord)
        worksheet.write(8,5,"Retencion",boldbord)

        x=9
        periodo = fields.Many2one('account.period', 'Periodo')
        dni = fields.Char('DNI')
        empleado = fields.Many2one('hr.employee', 'Empleado')
        ingresos_ord_afe = fields.Float(u'Ingresos Ordinario Afectos')
        ingresos_extra_afe = fields.Float(u'Ingresos Extraordinario Afectos')
        retencion = fields.Float(u'Retencion')
        for i in self.detalle:
            worksheet.write(x,0,i.periodo.name)
            worksheet.write(x,1,i.dni)
            worksheet.write(x,2,i.empleado.nombres+" "+i.empleado.a_paterno+" "+i.empleado.a_materno)
            worksheet.write(x,3,round(i.ingresos_ord_afe,2) if i.ingresos_ord_afe else 0.00)
            worksheet.write(x,4,round(i.ingresos_extra_afe,2) if i.ingresos_extra_afe else 0.00)
            worksheet.write(x,5,round(i.retencion,2) if i.retencion else 0.00)
            x += 1

        tam_col = [14,14,25,18,18,18]

        worksheet.set_column('A:A', tam_col[0])
        worksheet.set_column('B:B', tam_col[1])
        worksheet.set_column('C:C', tam_col[2])
        worksheet.set_column('D:D', tam_col[3])
        worksheet.set_column('E:E', tam_col[4])
        worksheet.set_column('F:F', tam_col[5])

        workbook.close()


        #sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
        vals = {
            'output_name': 'Quinta_Categoria.xlsx',
            'output_file': open(direccion+"quinta_categoria.xlsx", "rb").read().encode("base64"),
        }

        sfs_id = self.env['planilla.export.file'].create(vals)

        #import os
        #os.system('c:\\eSpeak2\\command_line\\espeak.exe -ves-f1 -s 170 -p 100 "Se Realizo La exportación exitosamente Y A EDWARD NO LE GUSTA XDXDXDXDDDDDDDDDDDD" ')

        return {
            "type": "ir.actions.act_window",
            "res_model": "planilla.export.file",
            "views": [[False, "form"]],
            "res_id": sfs_id.id,
            "target": "new",
        }
