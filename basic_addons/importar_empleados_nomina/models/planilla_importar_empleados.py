#!/usr/bin/python2
# coding: utf-8

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import sys
import io
import base64
import calendar
from xlrd import open_workbook
import xlrd
from datetime import datetime
import decimal
import unicodedata


class PlanillaImportarEmpleados(models.Model):
    _name = "planilla.importar.empleados"
    archivo = fields.Binary(u'Archivo importación')
    archivo_text = fields.Char(
        'dias trabajo', default=u'importacion_dias_trabajo.xls')

    def normalize_str_cell(self,f):
        string_float = repr(f)
        if 'e' in str(f):
            return repr(f)[:-2]
        elif '.' in str(f):
            return repr(f)[:-2]
        else:
            return str(f)
    def is_number_tryexcept(self,s):
        """ Returns True is string is a number. """
        try:
            float(s)
            return repr(s)[:-2]
        except ValueError:
            return s

    @api.multi
    def procesa_empleados(self):
        f = open("tmp_import_empleado.xls", "wb")
        f.write(self.archivo.decode('base64'))
        f.close()
        informacion_csv = base64.b64decode(self.archivo)
        wb = open_workbook("tmp_import_empleado.xls",
                           encoding_override="utf-8")
        s = wb.sheet_by_index(0)
        values = []
        for row in range(1, s.nrows):
            col_value = []
            if (s.cell(row, 0).value) == "":
                continue
            for col in range(s.ncols):
                value = (s.cell(row, col).value)

                if col == 12:
                    # y,m,d=xlrd.xldate_as_tuple(value, workbook_datemode)
                    a1_as_datetime = datetime(
                        *xlrd.xldate_as_tuple(value, wb.datemode))
                    # print a1_as_datetime.month
                    # print a1_as_datetime.day
                    # print a1_as_datetime.year
                    value = a1_as_datetime
                col_value.append(value)
                # sys.stdout.write(str(value))
            values.append(col_value)

        for record in values:
            # informacion distrito
            res_country_state = {
                'name': record[11],
                'code': record[11],
                'country_id': 175
            }
            info_country_state = self.env['res.country.state'].search(
                [('name', '=', res_country_state['name']), ('code', '=', res_country_state['code']), ('country_id', '=', res_country_state['country_id'])])

            if not info_country_state.id:
                info_country_state = self.env['res.country.state'].create(
                    res_country_state)

            # informacion direccion
            data_street = {
                'name': record[1]+' '+record[2]+' '+record[3],
                'street': record[10],
                'district_id': info_country_state.id,
            }
            data_street_id = self.env['res.partner'].search(
                [('name', '=', data_street['name']), ('street', '=', data_street['street']), ('district_id', '=', data_street['district_id'])])

            if not data_street_id.id:
                data_street_id = self.env['res.partner'].create(
                    data_street)

            # informacion titulo trabajo
            jod_data = {
                'name': record[8],
            }
            job_data_id = self.env['hr.job'].search(
                [('name', '=', jod_data['name'])])
            if not job_data_id.id:
                job_data_id = self.env['hr.job'].create(jod_data)
            # informacion departamento trabajo
            department_data = {
                'name': record[9],
                'analytic_account':25,# este campo es exclusivo de prescott
            }
            department_id = self.env['hr.department'].search(
                [('name', '=', department_data['name'])])
            if not department_id.id:
                department_id = self.env['hr.department'].create(
                    department_data)
            # informacion banco
            bank_data_id = {
                'name': record[16]
            }
            bank_id = self.env['res.bank'].search(
                [('name', '=', bank_data_id['name'])])
            if not bank_id.id:
                bank_id = self.env['res.bank'].create(bank_data_id)

            # informacion cuenta bancaria
            account_bank_data_id = {
                'acc_number': str(record[15]),#self.normalize_str_cell((record[15])),#repr(record[15])[:-2],#self.float_to_str(record[15]),
                'bank_id': bank_id.id,
                'currency_id': 164 if record[19] == 'SOL' else 3
            }
            account_bank_id = self.env['res.partner.bank'].search(
                [('acc_number', '=', account_bank_data_id['acc_number'])])
            if not account_bank_id.id:
                account_bank_id = self.env['res.partner.bank'].create(
                    account_bank_data_id)
            # informacion banco
            bank_data_cts_id = {
                'name': record[18]
            }
            bank_cts_id = self.env['res.bank'].search(
                [('name', '=', bank_data_cts_id['name'])])
            if not bank_cts_id.id:
                bank_cts_id = self.env['res.bank'].create(bank_data_cts_id)

            # informacion cuenta bancaria cts
            account_bank_cts_data_id = {
                'acc_number': str(record[17]),#self.normalize_str_cell((record[17])),
                'bank_id': bank_cts_id.id,
                'currency_id': 164 if record[19] == 'SOL' else 3
            }
            account_bank_cts_id = self.env['res.partner.bank'].search(
                [('acc_number', '=', account_bank_cts_data_id['acc_number'])] )
            if not account_bank_cts_id.id:
                account_bank_cts_id = self.env['res.partner.bank'].create(
                    account_bank_cts_data_id)
            resource_data_id = {
                'name': record[1] +' '+record[2]+' '+record[3]
            }
            resource_id = self.env['resource.resource'].search(
                [('name', '=', resource_data_id['name'])])
            if not resource_id.id:
                resource_id = self.env['resource.resource'].create(
                    resource_data_id)

            try:
                dni=repr(record[0])
                dni=dni[:-2] if '.' in dni else unicodedata.normalize('NFKD', record[0] ).encode('ascii','ignore')
            except ValueError:
                dni=unicodedata.normalize('NFKD', record[0]  ).encode('ascii','ignore')
            # informacion empleado
            data = {
                'identification_id': dni,
                'a_paterno': record[1],
                'a_materno': record[2],
                'nombres':record[3],
                'tablas_tipo_documento_id': 2,
                'resource_id': resource_id.id,
                'gender': 'male' if record[4] == 'M' else 'female',
                'marital': 'conviviente' if record[5] == 'Casado/Conviviente' else 'single' if record[5]=='Soltero' else 'divorced',
                'children': int(record[6]),
                'job_id': job_data_id.id,
                'department_id': department_id.id,
                'address_home_id': data_street_id.id,
                'birthday': record[12],
                'place_of_birth': record[13],
                'bank_account_id': account_bank_id.id,
                'bank_account_cts_id': account_bank_cts_id.id
            }
            self.env['hr.employee'].create(data)
            # break


    #FIXME: solo fue para corregir las cuentas de banco borrame en el futuro
    @api.multi
    def corregir(self):

        # a = self.env['res.partner.bank'].browse(int(row['banco']) )
        # print a.acc_number
        # a.acc_number= self.normalize_str_cell(a.acc_number)
        f = open("tmp_import_empleado.xls", "wb")
        f.write(self.archivo.decode('base64'))
        f.close()
        informacion_csv = base64.b64decode(self.archivo)
        wb = open_workbook("tmp_import_empleado.xls",
                        encoding_override="utf-8")
        s = wb.sheet_by_index(0)
        values = []
        for fila in range(1, s.nrows):
            col_value = []
            try:
                dni=repr(s.cell(fila, 0).value)
                # print "el dni es ",dni
                dni=dni[:-2] if '.' in dni else unicodedata.normalize('NFKD', s.cell(fila, 0).value ).encode('ascii','ignore')
            except ValueError:
                dni=unicodedata.normalize('NFKD', s.cell(fila, 0).value  ).encode('ascii','ignore')
            # print dni
            query = """
            select identification_id as dni ,he.bank_account_id as banco from
            hr_employee he
            inner join
            res_partner_bank rpb
            on he.bank_account_id = rpb.id
            where  he.identification_id ='"""+dni+"""'
            """
            # print query
            self.env.cr.execute(query)
            datos  = self.env.cr.dictfetchone()
            if datos:
                # print datos
                a = self.env['res.partner.bank'].browse(int(datos['banco']) )
                value = self.normalize_str_cell(s.cell(fila, 15).value )
                if '.' in str(value):
                    value=value[:-2]
                # print value
                # print a.acc_number
                a.acc_number = value
            else:
                print "CORRIGEME A MA NOOOOOOOOOOO",dni
