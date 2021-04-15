# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime, date
from calendar import monthrange
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

class HelperLiquidacion(models.Model):
    _name = "planilla.helpers"

    def date_to_month(self,m):
        meses = {
            1:	"Enero",
            2:	"Febrero",
            3:	"Marzo",
            4: "Abril",
            5: "Mayo",
            6: "Junio",
            7: "Julio",
            8: "Agosto",
            9: "Setiembre",
            10: "Octubre",
            11: "Noviembre",
            12: "Diciembre",
        }
        return meses[m]

    def get_col_widths(self, datos):
        # First we find the maximum length of the index column
        datos = zip(*datos)  # transponiendo filas por columnas
        column_len = []
        for i in range(len(datos)):
            max_col = 0
            for j in range(len(datos[i])):
                if len(str(datos[i][j]).strip()) > max_col:
                    max_col = len(str(datos[i][j]).strip())

            column_len.append(max_col+5)
        return column_len




    @api.model
    def getAsignacionFamiliarByDate(self, fecha_ini, fecha_fin, employee_id, code):
        query = """
        select sum(hpl.total) as total
        from hr_payslip hp
        inner join hr_payslip_line hpl on hpl.slip_id = hp.id
        inner join hr_contract hc on hc.id = hp.contract_id 
        where hp.date_from >= '%s' and hp.date_to<= '%s' and hp.employee_id =%d
        and code ='%s' and hc.regimen_laboral_empresa not in ('practicante','microempresa')
        group by hp.employee_id
        """ % (fecha_ini, fecha_fin, employee_id, code)

        self.env.cr.execute(query)
        res = self.env.cr.dictfetchone()
        return res['total'] if res else 0.0

    @api.model
    def getBasicoByDate(self, fecha_ini, fecha_fin, employee_id, code,liquidacion=False):
        contracts = self.env['hr.employee'].browse(employee_id).contract_ids
        filtered_contracts = filter(lambda c:c.regimen_laboral_empresa not in ('practicante','microempresa')  
            and datetime.strptime(c.date_start,'%Y-%m-%d').date() <= fecha_fin
            and c.situacion_id.codigo == '1' if not liquidacion else True,contracts)
        last_contract = max(filtered_contracts,key=lambda c:c['date_start']) if filtered_contracts else False
        return last_contract.wage if last_contract else 0.0

    @api.model
    def getSumFaltas(self, fecha_ini, fecha_fin, employee_id, code):

        # query = """
        # select sum(total) as total from hr_payslip hp
        # inner join hr_payslip_line hpl
        # on hpl.slip_id = hp.id
        # where hp.date_from >= '%s' and hp.date_to<= '%s' and hp.employee_id =%d
        # and code ='%s'
        # group by hp.employee_id
        # """ % (fecha_ini, fecha_fin, employee_id, code)
        query = """
        select sum(number_of_days) as total 
        from hr_payslip hp
        inner join hr_contract hc on hc.id = hp.contract_id
        inner join hr_payslip_worked_days hpwd on hpwd.payslip_id = hp.id
        where hp.date_from >= '%s' and hp.date_to<= '%s' and hp.employee_id =%d
        and hpwd.code ='%s' and hc.regimen_laboral_empresa not in ('practicante','microempresa')
        group by hp.employee_id
        """ % (fecha_ini, fecha_fin, employee_id, code)

        self.env.cr.execute(query)
        res = self.env.cr.dictfetchone()
        return res['total'] if res is not None else 0.0

    @api.model
    def queryBeneficiosSociales(self, fecha_ini, fecha_fin, employee_id, code):
        # query = """
        # select sum(total) as total,count(total) as count from hr_payslip hp
        # inner join hr_payslip_line hpl
        # on hpl.slip_id = hp.id
        # where hp.date_from >= '%s' and hp.date_to<= '%s' and hp.employee_id =%d
        # and code ='%s'
        # group by hp.employee_id
        # """ % (fecha_ini, fecha_fin, employee_id, code)
        query = """
        select sum(coalesce(amount,0)) as total,count(amount) as count 
        from hr_payslip hp
        inner join hr_contract hc on hc.id = hp.contract_id
        inner join hr_payslip_input hpi on hpi.payslip_id = hp.id
        where hp.date_from >= '%s' and hp.date_to<= '%s' and hp.employee_id =%d and amount>0.0
        and code in (%s) and hc.regimen_laboral_empresa not in ('practicante','microempresa')
        """ % (fecha_ini, fecha_fin, employee_id,
               ','.join("'"+i+"'" for i in code.mapped('code')))

        self.env.cr.execute(query)
        res = self.env.cr.dictfetchone()
        return res['total'] if  res is not None  else 0.0,res['count'] if  res is not None  else 0.0
    @api.model
    def queryHorasExtras(self, fecha_ini, fecha_fin, employee_id, code):
        query = """
        select sum(hpl.total) as total,count(hpl.total) as count 
        from hr_payslip hp
        inner join hr_contract hc on hc.id = hp.contract_id
        inner join hr_payslip_line hpl on hpl.slip_id = hp.id
        where hp.date_from >= '%s' and hp.date_to<= '%s' and hp.employee_id =%d and hpl.total>0.0
        and code ='%s' and hc.regimen_laboral_empresa not in ('practicante','microempresa')
        group by hp.employee_id
        """ % (fecha_ini, fecha_fin, employee_id, code)

        self.env.cr.execute(query)
        res = self.env.cr.dictfetchone()
        return res['total'] if  res is not None  else 0.0,res['count'] if  res is not None  else 0.0

    @api.model
    def calcula_comision_gratificacion_hrs_extras(self, contrato, fecha_computable, fecha_fin_nominas, meses, fecha_cese):
        parametros_gratificacion = self.env['planilla.gratificacion'].get_parametros_gratificacion()    
        fecha_inicio_nominas = date(
            fecha_computable.year, fecha_computable.month, 1)

        sum_comisiones,count_comisiones = self.queryBeneficiosSociales(fecha_inicio_nominas,fecha_fin_nominas,contrato.employee_id,parametros_gratificacion.cod_comisiones)

        # si tiene mas de 3 comisiones recibidas en el rango entonces tiene grati de comision
        if count_comisiones >= 3:
            if meses == 6:
                comisiones_periodo = round(sum_comisiones/6.0, 2)
            else:
                payslips = self.env['hr.payslip'].search([ ('employee_id','=',contrato.employee_id.id),
                                                ('date_to','>=',fecha_computable),
                                                ('date_to','<=',fecha_fin_nominas)])
                comisiones_periodo = round(sum_comisiones/float(len(payslips)), 2) if payslips else 0
            #    dias = abs(fecha_computable - fecha_cese)
            #    dias = dias.days+1
            #    comisiones_periodo = round(sum_comisiones/dias, 2)*30
        else:
            comisiones_periodo = 0

        sum_bonificaciones,count_bonificaciones = self.queryBeneficiosSociales(fecha_inicio_nominas,fecha_fin_nominas,contrato.employee_id,parametros_gratificacion.cod_bonificaciones)

        # si tiene mas de 3 bonificaciones recibidas en el rango entonces tiene grati de comision
        if count_bonificaciones >= 3:
            if meses == 6:
                promedio_bonificaciones = round(sum_bonificaciones/6.0, 2)
            else:
                payslips = self.env['hr.payslip'].search([ ('employee_id','=',contrato.employee_id.id),
                                                ('date_to','>=',fecha_computable),
                                                ('date_to','<=',fecha_fin_nominas)])
                promedio_bonificaciones = round(sum_bonificaciones/float(len(payslips)), 2) if payslips else 0
            #    # dias = abs(fecha_fin_nominas.day-fecha_computable.day) + 1
            #    dias = abs(fecha_computable - fecha_cese)
            #    dias = dias.days+1
            #    promedio_bonificaciones = round(
            #        sum_bonificaciones/dias, 2)*30
        else:
            promedio_bonificaciones = 0.0

        sum_sobretiempos,count_sobretiempos = self.queryHorasExtras(fecha_inicio_nominas,fecha_fin_nominas,contrato.employee_id,parametros_gratificacion.cod_sobretiempos.code)


        # si tiene mas de 3 pagos de sobretiempo recibidas en el rango entonces tiene grati de comision
        if count_sobretiempos >= 3:
            if meses == 6:
                promedio_horas_trabajo_extra = round(sum_sobretiempos/6.0, 2)
            else:
                payslips = self.env['hr.payslip'].search([ ('employee_id','=',contrato.employee_id.id),
                                                ('date_to','>=',fecha_computable),
                                                ('date_to','<=',fecha_fin_nominas)])
                promedio_horas_trabajo_extra = round(sum_sobretiempos/float(len(payslips)), 2) if payslips else 0
            #    dias = abs(fecha_computable - fecha_cese)
            #    dias = dias.days+1
            #    promedio_horas_trabajo_extra = round(
            #        sum_sobretiempos/dias, 2)*30
        else:
            promedio_horas_trabajo_extra = 0.0
        return comisiones_periodo, promedio_bonificaciones, promedio_horas_trabajo_extra

    def _diferencia_meses(self, d1, d2):
        if d1 > d2:
            raise UserError("Fecha %s no puede se rmayor a %s" % (d1, d2))
        res = relativedelta(d1, d2)
        return abs(res.months), abs(res.days)

    def diferencia_meses_gratificacion(self, d1, d2):
        meses, dias = self._diferencia_meses(d1, d2)
        if meses == 0 and dias == 0:
            return meses

        if d1.day > 1:
            meses -= 1
        if meses == 0 and dias == 0:
            return meses

        dias_mes_cese = monthrange(d2.year, d2.month)[1]

        if d2.day == dias_mes_cese:
            meses += 1
        else:
            meses -= 1
        return meses

    def diferencia_meses_dias(self, d1, d2):
        res = self.days360(d1, d2)
        dias_mes_cese = monthrange(d2.year, d2.month)[1]
        meses = int(res/30)
        dias = res-(meses*30)
        if dias_mes_cese == 30:
            dias += 1
        if dias == 30:
            meses += 1
            dias = 0

        return meses, dias

    def days360(self, start_date, end_date, method_eu=False):
        start_day = start_date.day
        start_month = start_date.month
        start_year = start_date.year
        end_day = end_date.day
        end_month = end_date.month
        end_year = end_date.year

        if (
            start_day == 31 or
            (
                method_eu is False and
                start_month == 2 and (
                    start_day == 29 or (
                        start_day == 28 and
                        calendar.isleap(start_year) is False
                    )
                )
            )
        ):
            start_day = 30

        if end_day == 31:
            if method_eu is False and start_day != 30:
                end_day = 1

                if end_month == 12:
                    end_year += 1
                    end_month = 1
                else:
                    end_month += 1
            else:
                end_day = 30
        return (
            end_day + (end_month * 30) + (end_year * 360) -
            start_day - (start_month * 30) - (start_year * 360)
        )

    def number_to_letter(self,number):
        UNIDADES = (
            '',
            'UN ',
            'DOS ',
            'TRES ',
            'CUATRO ',
            'CINCO ',
            'SEIS ',
            'SIETE ',
            'OCHO ',
            'NUEVE ',
            'DIEZ ',
            'ONCE ',
            'DOCE ',
            'TRECE ',
            'CATORCE ',
            'QUINCE ',
            'DIECISEIS ',
            'DIECISIETE ',
            'DIECIOCHO ',
            'DIECINUEVE ',
            'VEINTE '
        )

        DECENAS = (
            'VENTI',
            'TREINTA ',
            'CUARENTA ',
            'CINCUENTA ',
            'SESENTA ',
            'SETENTA ',
            'OCHENTA ',
            'NOVENTA ',
            'CIEN '
        )

        CENTENAS = (
            'CIENTO ',
            'DOSCIENTOS ',
            'TRESCIENTOS ',
            'CUATROCIENTOS ',
            'QUINIENTOS ',
            'SEISCIENTOS ',
            'SETECIENTOS ',
            'OCHOCIENTOS ',
            'NOVECIENTOS '
        )

        MONEDAS = (
            {'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
            {'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
            {'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
            {'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
            {'country': u'Perú', 'currency': 'PEN', 'singular': u'SOL', 'plural': u'SOLES', 'symbol': u'S/.'},
            {'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
        )
        # Para definir la moneda me estoy basando en los código que establece el ISO 4217
        # Decidí poner las variables en inglés, porque es más sencillo de ubicarlas sin importar el país
        # Si, ya sé que Europa no es un país, pero no se me ocurrió un nombre mejor para la clave.

        def __convert_group(n):
            """Turn each group of numbers into letters"""
            output = ''

            if(n == '100'):
                output = "CIEN"
            elif(n[0] != '0'):
                output = CENTENAS[int(n[0]) - 1]

            k = int(n[1:])
            if(k <= 20):
                output += UNIDADES[k]
            else:
                if((k > 30) & (n[2] != '0')):
                    output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
                else:
                    output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
            return output
        #raise osv.except_osv('Alerta', number)
        number=str(round(float(number),2))
        separate = number.split(".")
        number = int(separate[0])

        if int(separate[1]) >= 0:
            moneda = "con " + str(separate[1]).ljust(2,'0') + "/" + "100 " 

        """Converts a number into string representation"""
        converted = ''
        
        if not (0 <= number < 999999999):
            raise osv.except_osv('Alerta', number)
            #return 'No es posible convertir el numero a letras'

        
        
        number_str = str(number).zfill(9)
        millones = number_str[:3]
        miles = number_str[3:6]
        cientos = number_str[6:]
        

        if(millones):
            if(millones == '001'):
                converted += 'UN MILLON '
            elif(int(millones) > 0):
                converted += '%sMILLONES ' % __convert_group(millones)

        if(miles):
            if(miles == '001'):
                converted += 'MIL '
            elif(int(miles) > 0):
                converted += '%sMIL ' % __convert_group(miles)

        if(cientos):
            if(cientos == '001'):
                converted += 'UN '
            elif(int(cientos) > 0):
                converted += '%s ' % __convert_group(cientos)
        if float(number_str)==0:
            converted += 'CERO '
        converted += moneda

        return converted.upper()


