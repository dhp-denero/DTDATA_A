
# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError, UserError
from odoo import api, fields, models, _, exceptions
from datetime import datetime
import re
import time
import collections
import base64


class PlanillaImportWorkedDays(models.Model):

    _name = "planilla.import.worked.days"
    file_imp = fields.Binary(u'Archivo importación Dias de trabajo')
    file_input_lines = fields.Binary(u'Archivo importación Entradas')
    file_sal_error  = fields.Binary('Archivo Errores dias trabajo',readonly=1)
    file_error_entradas  = fields.Binary('Archivo Errores entradas',readonly=1)

    file_imp_text = fields.Char('dias trabajo',default=u'importacion_dias_trabajo.csv')
    file_input_lines_text = fields.Char('dias entradas',default=u'importacion_worked_days.csv')
    sal_name2 = fields.Char('errores dias trabajo',default='errores_importacion_dias_trabajo.csv')
    sal_name3 = fields.Char('errores entradas',default='errores_importacion_entradas.csv')

    record_separator = fields.Char("Separador CSV",default=",",size=1)

    def valida_informacion(self, file_input_lines):
        informacion_csv = base64.b64decode(file_input_lines)
        informacion_array = informacion_csv.strip().split("\n")
        informacion_array.pop(0)
        return informacion_array

    @api.multi
    def procesa_worked_days(self):
        informacion_array = self.valida_informacion(self.file_imp)
        direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file

        list_horrores=[]
        for line in informacion_array:
            line = line.split(self.record_separator)
            payslip = self.env['hr.payslip'].search([('number','=',line[0])])
            if payslip:
                wd = self.env['hr.payslip.worked_days'].search([('payslip_id','=',payslip.id),('code','=',line[2])])
                if wd:
                    wd.number_of_days = line[3]
                    wd.number_of_hours = line[4]
                    wd.minutos = line[5]
                else:
                    list_horrores.append(line)
            else:
                list_horrores.append(line)
        
        horrores = open(direccion + 'horroresimportacion.csv','w+' )
        for item in list_horrores:
            horrores.write("%s\n" % item)
        horrores.close()
        horrores_read = open(direccion + 'horroresimportacion.csv','r' ).read()
        self.file_sal_error = base64.encodestring(horrores_read)

        if len(list_horrores)>0:
            return self.env['planilla.warning'].info(title='Resultado de importacion', message="Hubo errores,verifique la fecha de inicio y fecha de fin sea correcto y revise el archivo de errorers de dias de trabajo y verifique las fechas!!!")
        else:
            return self.env['planilla.warning'].info(title='Resultado de importacion', message="Dias de trabajo importados con exito!!!")

    @api.multi
    def procesa_entradas(self):
        informacion_array = self.valida_informacion(self.file_input_lines)
        direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
        
        list_horrores=[]
        for line in informacion_array:
            line = line.split(self.record_separator)
            payslip = self.env['hr.payslip'].search([('number','=',line[0])])
            if payslip:
                inp = self.env['hr.payslip.input'].search([('payslip_id','=',payslip.id),('code','=',line[2])])
                if inp:
                    inp.amount = line[3]
                else:
                    list_horrores.append(line)
            else:
                list_horrores.append(line)

        horrores = open(direccion + 'horroresimportacion.csv','w+' )
        for item in list_horrores:
            horrores.write("%s\n" % item)
        horrores.close()
        horrores_read = open(direccion + 'horroresimportacion.csv','r' ).read()
        self.file_error_entradas = base64.encodestring(horrores_read)

        if len(list_horrores)>0:
            return self.env['planilla.warning'].info(title='Resultado de importacion', message="Hubo errores,verifique la fecha de inicio y fecha de fin sea correcto y revise el archivo de errorers de entradas!!!")
        else:
            return self.env['planilla.warning'].info(title='Resultado de importacion', message="Entradas importados con exito!!!")

class PlanillaImportWorkedDaysWizard(models.TransientModel):
    _name = "planilla.import.worked.days.wizard"

    payslip_run_id = fields.Many2one('hr.payslip.run','Nomina')
    worked_days_ids = fields.Many2many('planilla.worked.days','wd_import_wizard_default_rel','wizard_id','worked_day_id','Parametros Tareos')

    @api.multi
    def generate_excel(self):
        import io
        from xlsxwriter.workbook import Workbook

        try:
            direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
        except: 
            raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
        workbook = Workbook(direccion +'plantilla_wd.xlsx')

        boldbord = workbook.add_format({'bold': True})
        boldbord.set_border(style=2)
        boldbord.set_align('center')
        boldbord.set_align('vcenter')
        boldbord.set_text_wrap()
        boldbord.set_font_size(10)
        boldbord.set_bg_color('#DCE6F1')
        boldbord.set_font_name('Times New Roman')

        especial1 = workbook.add_format()
        especial1.set_align('center')
        especial1.set_align('vcenter')
        especial1.set_border(style=1)
        especial1.set_text_wrap()
        especial1.set_font_size(10)
        especial1.set_font_name('Times New Roman')

        especial3 = workbook.add_format({'bold': True})
        especial3.set_align('center')
        especial3.set_align('vcenter')
        especial3.set_border(style=1)
        especial3.set_text_wrap()
        especial3.set_bg_color('#DCE6F1')
        especial3.set_font_size(15)
        especial3.set_font_name('Times New Roman')

        numberdos = workbook.add_format({'num_format':'0'})
        numberdos.set_border(style=1)
        numberdos.set_font_size(10)
        numberdos.set_font_name('Times New Roman')

        dateformat = workbook.add_format({'num_format':'d-m-yyyy'})
        dateformat.set_border(style=1)
        dateformat.set_font_size(10)
        dateformat.set_font_name('Times New Roman')

        hourformat = workbook.add_format({'num_format':'hh:mm'})
        hourformat.set_align('center')
        hourformat.set_align('vcenter')
        hourformat.set_border(style=1)
        hourformat.set_font_size(10)
        hourformat.set_font_name('Times New Roman')

        import sys
        reload(sys)
        sys.setdefaultencoding('iso-8859-1')

        ##########ASISTENCIAS############
        worksheet = workbook.add_worksheet("PLANTILLA")
        worksheet.set_tab_color('blue')

        x = 0
        worksheet.write(x,0,"PLANILLA",boldbord)
        worksheet.write(x,1,"DNI",boldbord)
        worksheet.write(x,2,"CODIGO",boldbord)
        worksheet.write(x,3,"DIAS",boldbord)
        worksheet.write(x,4,"HORAS",boldbord)
        worksheet.write(x,5,"MINUTOS",boldbord)
        worksheet.write(x,6,"NOMBRE",boldbord)
        x=1

        for payslip in self.payslip_run_id.slip_ids:
            for wd in self.worked_days_ids:
                worksheet.write(x,0,payslip.number if payslip.number else '',especial1)
                worksheet.write(x,1,payslip.employee_id.identification_id if payslip.employee_id.identification_id else '',especial1)
                worksheet.write(x,2,wd.codigo if wd.codigo else '',especial1)
                worksheet.write(x,3,0,numberdos)
                worksheet.write(x,4,0,numberdos)
                worksheet.write(x,5,0,numberdos)
                worksheet.write(x,6,payslip.employee_id.name_related if payslip.employee_id.name_related else '',especial1)
                x += 1

        tam_col = [11,10,9,10,10,10]

        worksheet.set_column('A:A', tam_col[0])
        worksheet.set_column('B:B', tam_col[1])
        worksheet.set_column('C:C', tam_col[2])
        worksheet.set_column('D:D', tam_col[3])
        worksheet.set_column('E:E', tam_col[4])
        worksheet.set_column('F:F', tam_col[5])

        workbook.close()

        f = open(direccion + 'plantilla_wd.xlsx', 'rb')
        
        vals = {
            'output_name': 'Plantilla WD - %s.xlsx'%(self.payslip_run_id.name),
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


class PlanillaImportInputsWizard(models.TransientModel):
    _name = "planilla.import.inputs.wizard"

    payslip_run_id = fields.Many2one('hr.payslip.run','Nomina')
    inputs_ids = fields.Many2many('planilla.inputs.nomina','input_import_wizard_default_rel','wizard_id','input_id','Inputs')

    @api.multi
    def generate_excel(self):
        import io
        from xlsxwriter.workbook import Workbook

        try:
            direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
        except: 
            raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
        workbook = Workbook(direccion +'plantilla_input.xlsx')

        boldbord = workbook.add_format({'bold': True})
        boldbord.set_border(style=2)
        boldbord.set_align('center')
        boldbord.set_align('vcenter')
        boldbord.set_text_wrap()
        boldbord.set_font_size(10)
        boldbord.set_bg_color('#DCE6F1')
        boldbord.set_font_name('Times New Roman')

        especial1 = workbook.add_format()
        especial1.set_align('center')
        especial1.set_align('vcenter')
        especial1.set_border(style=1)
        especial1.set_text_wrap()
        especial1.set_font_size(10)
        especial1.set_font_name('Times New Roman')

        especial3 = workbook.add_format({'bold': True})
        especial3.set_align('center')
        especial3.set_align('vcenter')
        especial3.set_border(style=1)
        especial3.set_text_wrap()
        especial3.set_bg_color('#DCE6F1')
        especial3.set_font_size(15)
        especial3.set_font_name('Times New Roman')

        numberdos = workbook.add_format({'num_format':'0'})
        numberdos.set_border(style=1)
        numberdos.set_font_size(10)
        numberdos.set_font_name('Times New Roman')

        dateformat = workbook.add_format({'num_format':'d-m-yyyy'})
        dateformat.set_border(style=1)
        dateformat.set_font_size(10)
        dateformat.set_font_name('Times New Roman')

        hourformat = workbook.add_format({'num_format':'hh:mm'})
        hourformat.set_align('center')
        hourformat.set_align('vcenter')
        hourformat.set_border(style=1)
        hourformat.set_font_size(10)
        hourformat.set_font_name('Times New Roman')

        import sys
        reload(sys)
        sys.setdefaultencoding('iso-8859-1')

        ##########ASISTENCIAS############
        worksheet = workbook.add_worksheet("PLANTILLA")
        worksheet.set_tab_color('blue')

        x = 0
        worksheet.write(x,0,"PLANILLA",boldbord)
        worksheet.write(x,1,"DNI",boldbord)
        worksheet.write(x,2,"CODIGO",boldbord)
        worksheet.write(x,3,"MONTO",boldbord)
        worksheet.write(x,4,"NOMBRE",boldbord)
        x=1

        for payslip in self.payslip_run_id.slip_ids:
            for inp in self.inputs_ids:
                worksheet.write(x,0,payslip.number if payslip.number else '',especial1)
                worksheet.write(x,1,payslip.employee_id.identification_id if payslip.employee_id.identification_id else '',especial1)
                worksheet.write(x,2,inp.codigo if inp.codigo else '',especial1)
                worksheet.write(x,3,0,numberdos)
                worksheet.write(x,4,payslip.employee_id.name_related if payslip.employee_id.name_related else '',especial1)
                x += 1

        tam_col = [11,10,9,10]

        worksheet.set_column('A:A', tam_col[0])
        worksheet.set_column('B:B', tam_col[1])
        worksheet.set_column('C:C', tam_col[2])
        worksheet.set_column('D:D', tam_col[3])
        workbook.close()

        f = open(direccion + 'plantilla_input.xlsx', 'rb')
        
        vals = {
            'output_name': 'Plantilla Input - %s.xlsx'%(self.payslip_run_id.name),
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