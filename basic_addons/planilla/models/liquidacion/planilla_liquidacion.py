# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime, date, timedelta
import calendar
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import sys
import io
from xlsxwriter.workbook import Workbook
import base64
from dateutil.relativedelta import *

from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red , black , blue, gray, white, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table
from reportlab.lib.units import  cm,mm
from reportlab.lib.utils import simpleSplit
import os
import decimal
class PlanillaLiquidacion(models.Model):
    _name = "planilla.liquidacion"
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
    ], string=u"Año", required="1")

    month = fields.Selection([
        (1, "Enero"),
        (2, "Febrero"),
        (3, "Marzo"),
        (4, "Abril"),
        (5, "Mayo"),
        (6, "Junio"),
        (7, "Julio"),
        (8, "Agosto"),
        (9, "Setiembre"),
        (10, "Octubre"),
        (11, "Noviembre"),
        (12, "Diciembre"),
    ], string="Mes", required="1")

    # no se esta usando abajo 
    date_start = fields.Date()
    date_end = fields.Date()

    tipo_cambio = fields.Float("Tipo de Cambio", required=True, default=1)

    plus_9 = fields.Boolean("Considerar Bono 9%")

    calcular_meses_dias = fields.Boolean("calcular meses y dias")


    planilla_cts_lines = fields.One2many(
        'planilla.liquidacion.cts.line', 'planilla_liquidacion_id', u'Línea CTS')
    planilla_gratificacion_lines = fields.One2many(
        'planilla.liquidacion.gratificacion.line', 'planilla_liquidacion_id', u'Línea Gratificacion')
    planilla_vacaciones_lines = fields.One2many(
        'planilla.liquidacion.vacaciones.line', 'planilla_liquidacion_id', u'Línea Vacaciones')
    planilla_indemnizacion_lines = fields.One2many(
        'planilla.liquidacion.indemnizacion.line', 'planilla_liquidacion_id', u'Línea Indemnizacion')


    def is_number_tryexcept(self,s):
        """ Returns True is string is a number. """
        try:
            float(s)
            return True
        except ValueError:
            return False

    @api.multi
    def unlink(self):
        nomina = self.env['hr.payslip.run'].search([('date_start', '=', self.date_start), 
                                                    ('date_end', '=', self.date_end)])
        nomina.write({'liqui_flag':False})
        super(PlanillaLiquidacion,self).unlink()

    @api.multi
    def cabezera(self,c,wReal,hReal,company):
        import os
        try:
            direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
        except:
            raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')

        c.setFont("Arimo-Bold", 6)
        c.setFillColor(black)
        endl = 12
        pos_inicial = hReal-10
        pagina = 1

        c.drawCentredString((wReal/2.00),pos_inicial, "LIQUIDACIÓN DE BENEFICIOS SOCIALES")
        pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
        c.drawCentredString((wReal/2.00),pos_inicial, "LIQUIDACIÓN DE BENEFICIOS SOCIALES QUE OTORGA")
        pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
        c.drawCentredString((wReal/2.00),pos_inicial,company.name)

        imgdata = base64.b64decode(company.logo_web)
        new_image_handle = open(direccion+'company_logo_tmp.jpg', 'wb')
        new_image_handle.write(imgdata)
        new_image_handle.close()
        if new_image_handle:
            c.drawImage(direccion+'company_logo_tmp.jpg',20, hReal-40, width=120, height=50,mask='auto')

    @api.multi
    def verify_linea(self,c,wReal,hReal,posactual,valor,pagina):
        if posactual <10:
            company = self.env['res.company'].search([], limit=1)[0]
            c.showPage()
            self.cabezera(c,wReal,hReal,company)

            c.setFont("Arimo-Bold", 6)
            return pagina+1,hReal-60
        else:
            return pagina,posactual-valor

    @api.multi
    def get_liquidacion_wizard(self):
        return {
            'name': 'Exportar liquidacion pdf',
            "type": "ir.actions.act_window",
            "res_model": "planilla.liquidacion.pdf.wizard",
            'view_type': 'form',
            'view_mode': 'form',
            "views": [[False, "form"]],
            "target": "new",
            'context': {'current_id': self.id,'employees':[line.employee_id.id for line in self.planilla_vacaciones_lines]}            
        }


    @api.multi
    def get_certificado_wizard(self):
        return {
            'name': 'Exportar certificado pdf',
            "type": "ir.actions.act_window",
            "res_model": "planilla.liquidacion.pdf.certificado.wizard",
            'view_type': 'form',
            'view_mode': 'form',
            "views": [[False, "form"]],
            "target": "new",
            'context': {'current_id': self.id,'employees':[line.employee_id.id for line in self.planilla_vacaciones_lines]}            
        }



    @api.multi
    def get_liquidacion_pdf(self,employee_ids):
        if not hasattr(employee_ids, '__iter__'):
            employee_ids = [employee_ids]
        self.reporteador(employee_ids)
        direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
        vals = {
            'output_name': 'Planilla_liquidacion.pdf',
            'output_file': open(direccion+"planilla_tmp.pdf", "rb").read().encode("base64"),
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
    def reporteador(self, employee_ids):
        company = self.env['res.company'].search([], limit=1)[0]
        print(company.logo_web)
        reload(sys)
        sys.setdefaultencoding('iso-8859-1')
        width , height = A4  # 595 , 842
        wReal = width- 30
        hReal = height - 90
        direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
        c = canvas.Canvas(direccion+"planilla_tmp.pdf", pagesize=A4)
        inicio = 0
        pos_inicial = hReal-60
        endl = 9
        font_size = 6
        pagina = 1
        textPos = 0
        ruta_modulo= os.path.join(os.path.dirname(os.path.abspath(__file__)))
        pdfmetrics.registerFont(TTFont('Arimo-Bold',ruta_modulo+ '/../../fonts/Arimo-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('Arimo-BoldItalic',ruta_modulo+ '/../../fonts/Arimo-BoldItalic.ttf'))
        pdfmetrics.registerFont(TTFont('Arimo-Italic', ruta_modulo+ '/../../fonts/Arimo-Italic.ttf'))
        pdfmetrics.registerFont(TTFont('Arimo-Regular', ruta_modulo+'/../../fonts/Arimo-Regular.ttf'))

        helper = self.env['planilla.helpers']
        hllv = self.planilla_vacaciones_lines.search([('employee_id','in',employee_ids),('planilla_liquidacion_id','=',self.id)])
        for i in hllv:
            self.cabezera(c,wReal,hReal,company)
            hllg = self.planilla_gratificacion_lines.search([('employee_id','=',i.employee_id.id),('planilla_liquidacion_id','=',self.id)])[0]
            hllc = self.planilla_cts_lines.search([('employee_id','=',i.employee_id.id),('planilla_liquidacion_id','=',self.id)])[0]
            indemnizacion = self.planilla_indemnizacion_lines.search([('employee_id','=',i.employee_id.id),('planilla_liquidacion_id','=',self.id)])[0]
            # employee_id = self.env['hr.employee'].search([''])

            total_sum = 0

            c.setFont("Arimo-Bold", font_size)
            c.drawString( 30 , pos_inicial, u"DATOS PERSONALES")
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            c.drawString( 40 , pos_inicial, u"Apellidos y Nombres")
            c.drawString( 140 , pos_inicial, u":")
            c.setFont("Arimo-Regular", font_size)
            c.drawString( 150 , pos_inicial, i.contract_id.employee_id.name_related if i.contract_id.employee_id.name_related else '')
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            c.setFont("Arimo-Bold", font_size)
            c.drawString( 40 , pos_inicial, u"DNI Nº")
            c.drawString( 140 , pos_inicial, u":")
            c.setFont("Arimo-Regular", font_size)
            c.drawString( 150 , pos_inicial, i.contract_id.employee_id.identification_id if i.contract_id.employee_id.identification_id else '')
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            c.setFont("Arimo-Bold", font_size)
            c.drawString( 40 , pos_inicial, u"Cargo")
            c.drawString( 140 , pos_inicial, u":")
            c.setFont("Arimo-Regular", font_size)
            c.drawString( 150 , pos_inicial, i.contract_id.employee_id.job_id.name if i.contract_id.employee_id.job_id.name else '')
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            c.setFont("Arimo-Bold", font_size)
            c.drawString( 40 , pos_inicial, u"Fecha de Ingreso")
            c.drawString( 140 , pos_inicial, u":")
            c.setFont("Arimo-Regular", font_size)
            c.drawString( 150 , pos_inicial, i.contract_id.date_start if i.contract_id.date_start else '')
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            c.setFont("Arimo-Bold", font_size)
            c.drawString( 40 , pos_inicial, u"Fecha de Cese")
            c.drawString( 140 , pos_inicial, u":")
            c.setFont("Arimo-Regular", font_size)
            c.drawString( 150 , pos_inicial, i.contract_id.date_end if i.contract_id.date_end else '')
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)			
            c.setFont("Arimo-Bold", font_size)
            c.drawString( 40 , pos_inicial, u"Motivo")
            c.drawString( 140 , pos_inicial, u":")
            c.setFont("Arimo-Regular", font_size)
            c.drawString( 150 , pos_inicial,  '')
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            c.setFont("Arimo-Bold", font_size)
            c.drawString( 40 , pos_inicial, u"Afiliación")
            c.drawString( 140 , pos_inicial, u":")
            c.setFont("Arimo-Regular", font_size)
            c.drawString( 150 , pos_inicial, i.contract_id.afiliacion_id.entidad if i.contract_id.afiliacion_id.entidad else '')
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            c.setFont("Arimo-Bold", font_size)
            c.drawString( 40 , pos_inicial, u"Último Sueldo Básico")
            c.drawString( 140 , pos_inicial, u":")
            c.setFont("Arimo-Regular", font_size)
            c.drawString( 150 , pos_inicial, ('{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.contract_id.wage )) if i.basico else "0.00") + " "*4 + u"NUEVOS SOLES")
            c.setFont("Arimo-Bold", font_size)
            c.drawString( 240 , pos_inicial, u"Tipo de Cambio")
            c.drawString( 280 , pos_inicial, u":")
            c.setFont("Arimo-Regular", font_size)
            c.drawString( 290 , pos_inicial, str(self.tipo_cambio) if self.tipo_cambio else '0.00')
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)


            c.setFont("Arimo-Bold", font_size)
            c.drawString( 40 , pos_inicial, u"Tiempo de Servicio")
            c.drawString( 140 , pos_inicial, u":")
            if i.contract_id.date_start and i.contract_id.date_end:
                fmt = '%Y-%m-%d'
                f1 = datetime.strptime(i.contract_id.date_start,  fmt)
                f2 =datetime.strptime(i.contract_id.date_end, fmt)
                fr = relativedelta(f2,f1) + relativedelta(days=1)
                txt = ""

                res = self.env['planilla.helpers'].days360(f1,f2+relativedelta(days=1))
                meses = int(res/30)
                anios = int(meses/12)
                # meses1 = meses - int(meses/12)
                meses1 = meses - (anios*12)
                dias = res-(meses*30)
                


                if fr.years:
                    txt += str(anios) + u" AÑO(S) "
                if fr.months:
                    txt += str(meses1) + u" MES(ES)"
                if fr.days:
                    txt += str(dias) + u" DÍA(S)"
                c.setFont("Arimo-Regular", font_size)
                c.drawString( 150 , pos_inicial, txt)




            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*2,pagina)

            c.setFont("Arimo-Bold", font_size)
            c.drawString( 30 , pos_inicial, u"BASES DE CÁLCULO")
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            basraw = i.basico
            # afraw  = self.env['hr.parameters'].search([('num_tipo','=',10001)])[0].monto if i.contract_id.employee_id.children_number else 0
            # if i.contract_id.employee_id.is_practicant:
            #     afraw /= 2
            # basraw -= afraw
            # if i.contract_id.wage:
            #     c.setFont("Arimo-Bold", font_size)
            #     c.drawString( 40 , pos_inicial, u"BÁSICO")
            #     c.drawString( 170 , pos_inicial, u":")
            #     c.setFont("Arimo-Regular", font_size)
            #     c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % basraw )) if basraw else '')
            #     pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            # if hllc.a_familiar:
            #     c.setFont("Arimo-Bold", font_size)
            #     c.drawString( 40 , pos_inicial, u"ASIG. FAMILIAR")
            #     c.drawString( 170 , pos_inicial, u":")
            #     c.setFont("Arimo-Regular", font_size)
            #     # hp = self.env['hr.parameters'].search([('num_tipo','=',10001)])
            #     c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" %  hllc.a_familiar )) if  hllc.a_familiar else '')
            #     pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            # if i.nocturnal_surcharge_mean:
            #     c.setFont("Arimo-Bold", font_size)
            #     c.drawString( 40 , pos_inicial, u"PROM. SOBRETAZA NOCTURNA")
            #     c.drawString( 170 , pos_inicial, u":")
            #     c.setFont("Arimo-Regular", font_size)
            #     c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.nocturnal_surcharge_mean )) if i.nocturnal_surcharge_mean else '')
            #     pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            # if i.sixth_gratification:
            #     c.setFont("Arimo-Bold", font_size)
            #     c.drawString( 40 , pos_inicial, u"1/6 ULTIMA GRATIF.")
            #     c.drawString( 170 , pos_inicial, u":")
            #     c.setFont("Arimo-Regular", font_size)
            #     c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.sixth_gratification )) if i.sixth_gratification else '')
            #     pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            # pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)



            c.setFont("Arimo-Bold", font_size)
            c.drawString( 30 , pos_inicial, u"1. COMPENSACIÓN POR TIEMPO DE SERVICIOS")
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            c.setFont("Arimo-Bold", font_size)
            fi = i.fecha_computable.split('-') if i.fecha_computable else ''
            fc = i.fecha_cese.split('-') if i.fecha_cese else ''
            str_fi = (self.env['planilla.helpers'].date_to_month(int(fi[1]))+" "+fi[0]) if i.fecha_computable else '_'*8
            str_fc = (self.env['planilla.helpers'].date_to_month(int(fc[1]))+" "+fc[0]) if i.fecha_cese else '_'*8
            c.drawString( 30 , pos_inicial, u"(Periodo "+str_fi+" A "+str_fc+")")
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            if hllc.cts_a_pagar:
                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"CTS")
                c.drawString( 170 , pos_inicial, u":")
                c.setFont("Arimo-Regular", font_size)
                c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllc.cts_a_pagar )) if hllc.cts_a_pagar else "0.00")
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"Tiempo")
                c.drawString( 170 , pos_inicial, u":")
                tiempo_cts = ""
                if hllc.meses:
                    tiempo_cts += str(int(hllc.meses)) + u" Mes(es) "
                if hllc.dias:
                    tiempo_cts += str(int(hllc.dias)) + u" Día(s) "
                c.setFont("Arimo-Regular", font_size)
                c.drawString( 200 , pos_inicial, tiempo_cts)
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            if False:
                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"Inters. CTS")
                c.drawString( 170 , pos_inicial, u":")
                c.setFont("Arimo-Regular", font_size)
                c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % 0 )) )
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

            c.setFont("Arimo-Bold", font_size)
            c.drawString( 30 , pos_inicial, u"2. VACACIONES")
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            c.setFont("Arimo-Bold", font_size)
            fi = i.fecha_computable.split('-') if i.fecha_computable else ''
            fc = i.fecha_cese.split('-') if i.fecha_cese else ''
            str_fi = (self.env['planilla.helpers'].date_to_month(int(fi[1]))+" "+fi[0]) if i.fecha_computable else '_'*8
            str_fc = (self.env['planilla.helpers'].date_to_month(int(fc[1]))+" "+fc[0]) if i.fecha_cese else '_'*8
            c.drawString( 30 , pos_inicial, u"(Periodo "+str_fi+" A "+str_fc+")")
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

            if i.vacaciones_truncas:
                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"Vacaciones Truncas")
                c.drawString( 170 , pos_inicial, u":")
                c.setFont("Arimo-Regular", font_size)
                c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.vacaciones_truncas )) if i.vacaciones_truncas else "0.00" )
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            # if i.fall_due_holidays:
            #     c.setFont("Arimo-Bold", font_size)
            #     c.drawString( 40 , pos_inicial, u"Remuneración Vacacional")
            #     c.drawString( 170 , pos_inicial, u":")
            #     c.setFont("Arimo-Regular", font_size)
            #     c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.fall_due_holidays )) if i.fall_due_holidays else "0.00")
            #     pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            # if i.compensation:
            #     c.setFont("Arimo-Bold", font_size)
            #     c.drawString( 40 , pos_inicial, u"Vacaciones Indem.")
            #     c.drawString( 170 , pos_inicial, u":")
            #     c.setFont("Arimo-Regular", font_size)
            #     c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.compensation )) if i.compensation else "0.00")
            #     pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"Tiempo")
                c.drawString( 170 , pos_inicial, u":")
                tiempo_vac = ""
                if i.meses:
                    tiempo_vac += str(int(i.meses)) + u" Mes(es) "
                if i.dias:
                    tiempo_vac += str(int(i.dias)) + u" Día(s) "
                c.setFont("Arimo-Regular", font_size)
                c.drawString( 200 , pos_inicial, tiempo_vac)
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

            c.setFont("Arimo-Bold", font_size)
            c.drawString( 30 , pos_inicial, u"3. GRATIFICACIONES")
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            c.setFont("Arimo-Bold", font_size)
            fi = hllg.fecha_computable.split('-') if hllg.fecha_computable else ''
            fc = hllg.fecha_cese.split('-') if hllg.fecha_cese else ''
            str_fi = (self.env['planilla.helpers'].date_to_month(int(fi[1]))+" "+fi[0]) if hllg.fecha_computable else '_'*8
            str_fc = (self.env['planilla.helpers'].date_to_month(int(fc[1]))+" "+fc[0]) if hllg.fecha_cese else '_'*8
            c.drawString( 30 , pos_inicial, u"(Periodo "+str_fi+" A "+str_fc+")")
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            if hllg:
                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"Gratificación Trunca")
                c.drawString( 170 , pos_inicial, u":")
                c.setFont("Arimo-Regular", font_size)
                c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllg.total_gratificacion )) if hllg.total_gratificacion else "0.00" )
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"BONIF EX.L. 30334")
                c.drawString( 170 , pos_inicial, u":")
                c.setFont("Arimo-Regular", font_size)
                c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllg.plus_9 )) if hllg.plus_9 else "0.00" )
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)


                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"Tiempo")
                c.drawString( 170 , pos_inicial, u":")
                tiempo_grat = ""
                tiempo_grat += str(int(hllg.meses)) + u" Mes(es) "
                # tiempo_grat += str(int(hllg.dias)) + u" Día(s) "
                c.setFont("Arimo-Regular", font_size)
                c.drawString( 200 , pos_inicial,tiempo_grat)
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)


            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

            c.setFont("Arimo-Bold", font_size)
            c.drawString( 30 , pos_inicial, u"4. LIQUIDACIÓN")
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            if hllc:
                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"CTS")
                c.drawString( 170 , pos_inicial, u":")
                c.setFont("Arimo-Regular", font_size)
                c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllc.cts_a_pagar )) if hllc.cts_a_pagar  else "0.00")
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            if i.vacaciones_truncas:
                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"Vacaciones Truncas")
                c.drawString( 170 , pos_inicial, u":")
                c.setFont("Arimo-Regular", font_size)
                c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.vacaciones_truncas )) if i.vacaciones_truncas else "0.00" )
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            if hllg.total_gratificacion:
                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"Gratificación Trunca")
                c.drawString( 170 , pos_inicial, u":")
                c.setFont("Arimo-Regular", font_size)
                c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllg.total_gratificacion )) if hllg.total_gratificacion else "0.00" )
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            print indemnizacion
            if indemnizacion.monto>0.0:
                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"Indemnizacion")
                c.drawString( 170 , pos_inicial, u":")
                c.setFont("Arimo-Regular", font_size)
                c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % indemnizacion.monto )) if indemnizacion.monto else "0.00" )
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

            # hfcdl = self.env['hr.five.category.devolucion.lines'].search([('devolucion_id.period_id','=',self.period_id.id),('employee_id','=',hllg.employee_id.id)])
            # if len(hfcdl):
            # 	hfcdl = hfcdl[0]
            # 	if hfcdl.monto_devolver < 0:
            # 		c.setFont("Arimo-Bold", font_size)
            # 		c.drawString( 40 , pos_inicial, u"Devolucion Imp. Renta 5ta Categ.")
            # 		c.drawString( 170 , pos_inicial, u":")
            # 		c.setFont("Arimo-Regular", font_size)
            # 		c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % (hfcdl.monto_devolver*-1) )))
            # 		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            # 	else:
            # 		c.setFont("Arimo-Bold", font_size)
            # 		c.drawString( 40 , pos_inicial, u"Retención Imp. Renta 5ta Categ.")
            # 		c.drawString( 170 , pos_inicial, u":")
            # 		c.setFont("Arimo-Regular", font_size)
            # 		c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % (hfcdl.monto_devolver) )))
            # 		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

            # if (i.interes+hllg.interes+hllv.interes) > 0:
            #     c.setFont("Arimo-Bold", font_size)
            #     c.drawString( 40 , pos_inicial, u"Intereses Liquidación")
            #     c.drawString( 170 , pos_inicial, u":")
            #     c.setFont("Arimo-Regular", font_size)
            #     c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % (i.interes+hllg.interes+hllv.interes) )))
            #     pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            if hllg.plus_9:
                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"BONIF EX.L. 30334")
                c.drawString( 170 , pos_inicial, u":")
                c.setFont("Arimo-Regular", font_size)
                c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllg.plus_9 )) if hllg.plus_9 else "0.00" )
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            # if hllv.fall_due_holidays:
            #     c.setFont("Arimo-Bold", font_size)
            #     c.drawString( 40 , pos_inicial, u"Remuneración Vacacional")
            #     c.drawString( 170 , pos_inicial, u":")
            #     c.setFont("Arimo-Regular", font_size)
            #     c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllv.fall_due_holidays )) if hllv.fall_due_holidays else "0.00")
            #     pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            # if hllv.compensation:
            #     c.setFont("Arimo-Bold", font_size)
            #     c.drawString( 40 , pos_inicial, u"Vacaciones Indem")
            #     c.drawString( 170 , pos_inicial, u":")
            #     c.setFont("Arimo-Regular", font_size)
            #     c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllv.compensation )) if hllv.compensation else "0.00")
            #     pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)			
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)


            c.setFont("Arimo-Bold", font_size)
            c.drawString( 30 , pos_inicial, u"OTROS INGRESOS")
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            tot_ingresos = i.total_vacaciones + hllc.cts_a_pagar + hllg.total_gratificacion + hllg.plus_9 +indemnizacion.monto
            # for item in hllv.ingresos_lines:
            #     if item.monto:
            #         c.setFont("Arimo-Bold", font_size)
            #         c.drawString( 40 , pos_inicial, item.concepto_id.name)
            #         c.drawString( 170 , pos_inicial, u":")
            #         c.setFont("Arimo-Regular", font_size)
            #         c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % item.monto )) )
            #         tot_ingresos += item.monto
            #         pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            c.setFont("Arimo-Bold", font_size)
            c.drawString( 40 , pos_inicial, u"Total Ingresos")
            c.setFont("Arimo-Bold", font_size)
            c.drawRightString( 330 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % tot_ingresos )) if tot_ingresos else "0.00" )
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*2,pagina)
            c.setFont("Arimo-Bold", font_size)
            c.drawString( 40 , pos_inicial, u"Aportes Trabajador")
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

            # if i.onp:
            #     c.setFont("Arimo-Bold", font_size)
            #     c.drawString( 40 , pos_inicial, u"ONP")
            #     c.drawString( 170 , pos_inicial, u":")
            #     c.setFont("Arimo-Regular", font_size)
            #     c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.onp )) if i.onp else "0.00" )
            #     pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

            if i.contract_id.afiliacion_id.entidad.lower()!='onp':
                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"AFP. PENSIONES")
                c.drawString( 170 , pos_inicial, u":")
                c.setFont("Arimo-Regular", font_size)
                c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.afp_jub )) if i.afp_jub else "0.00" )
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"AFP. COM. PORC.")
                c.drawString( 170 , pos_inicial, u":")
                c.setFont("Arimo-Regular", font_size)
                c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.afp_com )) if i.afp_com else "0.00" )
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"AFP. SEGUROS")
                c.drawString( 170 , pos_inicial, u":")
                c.setFont("Arimo-Regular", font_size)
                c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.afp_si )) if i.afp_si else "0.00" )
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

                #onp
                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"IMPORTE ONP")
                c.drawString( 170 , pos_inicial, u":")
                c.setFont("Arimo-Regular", font_size)
                c.drawRightString( 250 , pos_inicial, "0.00" )
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

            else:
                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"AFP. PENSIONES")
                c.drawString( 170 , pos_inicial, u":")
                c.setFont("Arimo-Regular", font_size)
                c.drawRightString( 250 , pos_inicial, "0.00")
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"AFP. COM. PORC.")
                c.drawString( 170 , pos_inicial, u":")
                c.setFont("Arimo-Regular", font_size)
                c.drawRightString( 250 , pos_inicial, "0.00" )
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"AFP. SEGUROS")
                c.drawString( 170 , pos_inicial, u":")
                c.setFont("Arimo-Regular", font_size)
                c.drawRightString( 250 , pos_inicial, "0.00")
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

                c.setFont("Arimo-Bold", font_size)
                c.drawString( 40 , pos_inicial, u"IMPORTE ONP")
                c.drawString( 170 , pos_inicial, u":")
                c.setFont("Arimo-Regular", font_size)
                c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.onp )) if i.onp else "0.00" )
                pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

            # if i.afp_2p:
            #     c.setFont("Arimo-Bold", font_size)
            #     c.drawString( 40 , pos_inicial, u"AFP. 2%")
            #     c.drawString( 170 , pos_inicial, u":")
            #     c.setFont("Arimo-Regular", font_size)
            #     c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.afp_2p )) if i.afp_2p else "0.00" )
            #     pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            # if i.afp_jub:
            #     c.setFont("Arimo-Bold", font_size)
            #     c.drawString( 40 , pos_inicial, u"IMPORTE ONP")
            #     c.drawString( 170 , pos_inicial, u":")
            #     c.setFont("Arimo-Regular", font_size)
            #     c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.afp_jub )) if i.afp_jub else "0.00" )
            #     pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

            tot_descuentos = i.onp + i.afp_jub + i.afp_si + i.afp_com 
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            c.setFont("Arimo-Bold", font_size)
            c.drawString( 30 , pos_inicial, u"OTROS DESCUENTOS")
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

            # for item in i.descuentos_lines:
            #     if item.concepto_id.payroll_group != '4':
            #         if item.monto:
            #             c.setFont("Arimo-Bold", font_size)
            #             c.drawString( 40 , pos_inicial, item.concepto_id.name)
            #             c.drawString( 170 , pos_inicial, u":")
            #             c.setFont("Arimo-Regular", font_size)
            #             c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % item.monto )) )
            #             tot_descuentos += item.monto
            #             pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)			
            c.setFont("Arimo-Bold", font_size)
            c.drawString( 40 , pos_inicial, u"Total Descuentos")
            c.setFont("Arimo-Bold", font_size)
            c.drawRightString( 330 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % tot_descuentos )) if tot_descuentos else "0.00")
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

            c.setFont("Arimo-Bold", font_size)
            c.drawString( 40 , pos_inicial, u"Total a Pagar")
            c.setFont("Arimo-Bold", font_size)
            c.drawRightString( 330 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % (tot_ingresos - tot_descuentos) )) if (tot_ingresos - tot_descuentos) else "0.00")
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*2,pagina)

            c.setFont("Arimo-Bold", font_size)
            c.drawString( 30 , pos_inicial, u"Neto a Pagar al Trabajador")
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            c.setFont("Arimo-Regular", font_size)
            c.drawString( 40 , pos_inicial, u"SON")
            c.setFont("Arimo-Bold", font_size)
            tot_tot = tot_ingresos - tot_descuentos
            c.drawString( 55 , pos_inicial, helper.number_to_letter(tot_tot) + " soles")
            #str(float(tot_tot.replace(',',''))).capitalize()
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*3,pagina)

            c.setFont("Arimo-Regular", font_size)
            # isd = i.issue_date.split('-' ) if i.issue_date else ''
            isd = i.contract_id.date_end.split('-') if i.contract_id.date_end else ''
            c.drawString( 300 , pos_inicial, ("Arequipa " + isd[2] + " de "+self.env['planilla.helpers'].date_to_month(int(isd[1]))+" del "+isd[0]) if i.contract_id.date_end else '_'*28)
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)			
            txt = u"Dpto. de personal"
            c.drawCentredString( 100 , pos_inicial, u"_"*len(txt)*2)
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            c.drawCentredString( 100 , pos_inicial, txt)
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            c.drawCentredString( 100 , pos_inicial, company.name)
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*2,pagina)

            c.setFont("Arimo-Bold", font_size)
            c.drawString( 30 , pos_inicial, u"CONSTANCIA DE RECEPCIÓN")
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*4,pagina)

            style = getSampleStyleSheet()["Normal"]
            style.leading = 12
            style.alignment = 4

            paragraph1 = Paragraph(
                "<font size=6>" + u"Declaro estar conforme con la presente liquidación, haber recibido el importe de la misma así como el importe correspondiente a todas y cada una de  mis remuneraciones y beneficios no teniendo que reclamar en el futuro, quedando asi concluida la relación laboral. </font>",
                style
            )

            data= [[ paragraph1 ]]
            t=Table(data,colWidths=(515), rowHeights=(40))
            t.setStyle(TableStyle([
            ('TEXTFONT', (0, 0), (-1, -1), 'Arimo-Regular'),
            ('FONTSIZE',(0,0),(-1,-1),font_size)
            ]))
            t.wrapOn(c,40,pos_inicial)
            t.drawOn(c,40,pos_inicial)
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*3,pagina)

            c.setFont("Arimo-Regular", font_size)		
            txt = i.contract_id.employee_id.name_related
            c.drawCentredString( 250 , pos_inicial, u"_"*len(txt)*2)
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            c.drawCentredString( 250 , pos_inicial, txt)
            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
            c.drawCentredString( 250 , pos_inicial, i.contract_id.employee_id.identification_id if i.contract_id.employee_id.identification_id else '')

            pagina += 1
            c.showPage()
            inicio = 0
            pos_inicial = hReal-100
            pagina = 1
            textPos = 0
        c.save()

    @api.multi
    @api.depends('year', 'month')
    @api.onchange('year', 'month')
    def change_dates(self):
		if(self.year is not False and self.month is not False):
			self.ensure_one()
			self.date_start = date(int(self.year), self.month, 1)
			self.date_end = date(int(self.year), self.month,
								 calendar.monthrange(int(self.year), self.month)[1])

    @api.multi
    def write(self, vals):
        if vals and ("year" in vals or "month" in vals):
            vals['date_start'] = date(int(self.year), self.month, 1)
            vals['date_end'] = date(int(self.year), self.month, calendar.monthrange(
                int(self.year), self.month)[1])

        return super(PlanillaLiquidacion, self).write(vals)

    @api.model
    def create(self, vals):
        if len(self.search([('year', '=', vals['year']), ('month', '=', vals['month'])])) >= 1:
            raise UserError(
                "Ya existe un registros %s" % (vals['year']))
        else:
            vals['date_start'] = date(int(vals['year']), int(vals['month']) , 1)
            vals['date_end'] = date(int(vals['year']), int(vals['month']) , calendar.monthrange(
                int(vals['year']), int(vals['month']) )[1])
            return super(PlanillaLiquidacion, self).create(vals)


    def get_excel(self):
        # -------------------------------------------Datos---------------------------------------------------
        reload(sys)
        sys.setdefaultencoding('iso-8859-1')
        output = io.BytesIO()

        direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
        workbook = Workbook(direccion+'Liquidacion%s-%s.xlsx' % (self.year, self.month))
        worksheet = workbook.add_worksheet(
            'gratificacion%s-%s.xlsx' % (self.year, self.month))
        worksheet.set_tab_color('red')

        lines = self.planilla_gratificacion_lines
        self.env['planilla.gratificacion'].getSheetGratificacion(workbook,worksheet,lines,self.year)
        
        lines = self.planilla_cts_lines
        worksheet = workbook.add_worksheet(
            'CTS%s-%s.xlsx' % (self.year, self.month))
        worksheet.set_tab_color('green')
        self.env['planilla.cts'].getCTSSheet(workbook,worksheet,lines,self.year)
            
        lines = self.planilla_vacaciones_lines
        worksheet = workbook.add_worksheet(
            'Vacaciones%s-%s.xlsx' % (self.year, self.month))
        worksheet.set_tab_color('blue')
        self.getLiquidacionSheet(workbook,worksheet,lines)


            
        workbook.close()

        f = open(direccion+'Liquidacion%s-%s.xlsx' % (self.year, self.month), 'rb')

        vals = {
            'output_name': 'Liquidacion%s-%s.xlsx' % (self.year, self.month),
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
    def getLiquidacionSheet(self,workbook,worksheet,lines):

        worksheet.set_landscape()  # Horizontal
        worksheet.set_paper(9)  # A-4
        worksheet.set_margins(left=0.75, right=0.75, top=1, bottom=1)
        worksheet.fit_to_pages(1, 0)  # Ajustar por Columna

        fontSize = 8
        bold = workbook.add_format(
            {'bold': True, 'font_name': 'Arial', 'font_size': fontSize})
        normal = workbook.add_format()
        boldbord = workbook.add_format({'bold': True, 'font_name': 'Arial'})
        # boldbord.set_border(style=1)
        boldbord.set_align('center')
        boldbord.set_align('bottom')
        boldbord.set_text_wrap()
        boldbord.set_font_size(fontSize)
        boldbord.set_bg_color('#99CCFF')
        numberdos = workbook.add_format(
            {'num_format': '#,##0.00', 'font_name': 'Arial', 'align': 'right'})
        formatLeft = workbook.add_format(
            {'num_format': '#,##0.00', 'font_name': 'Arial', 'align': 'left', 'font_size': fontSize})
        formatLeftColor = workbook.add_format(
            {'bold': True, 'num_format': '#,##0.00', 'font_name': 'Arial', 'align': 'left', 'bg_color': '#99CCFF', 'font_size': fontSize})
        styleFooterSum = workbook.add_format(
            {'bold': True, 'num_format': '#,##0.00', 'font_name': 'Arial', 'align': 'right', 'font_size': fontSize, 'top': 1, 'bottom': 2})
        styleFooterSum.set_bottom(6)
        numberdos.set_font_size(fontSize)
        bord = workbook.add_format()
        bord.set_border(style=1)
        bord.set_text_wrap()
        # numberdos.set_border(style=1)
        formatMoneyWithBorder = workbook.add_format(
            {'valign': 'vcenter', 'align': 'right', 'border': 1, 'num_format': '#,##0.00'})

        title = workbook.add_format({'bold': True, 'font_name': 'Arial'})
        title.set_align('vcenter')
        # title.set_text_wrap()
        title.set_font_size(15)
        company = self.env['res.company'].search([], limit=1)[0]

        x = 0

        import sys
        reload(sys)
        sys.setdefaultencoding('iso-8859-1')
        worksheet.merge_range('A1:B1', company.name.strip(), title)
        worksheet.merge_range('A2:D2', "VACACIONES", bold)
        x = x+2

        x = x+1
        worksheet.write("A3", u"Mes:", bold)
        worksheet.write("B3",dict(self._fields['month'].selection).get(self.month),bold)

        x = x+3

        columnas = ["Orden",
                    "Nro Documento",
                    "Apellido\nPaterno",
                    "Apellido\nMaterno",
                    "Nombres",
                    "Fecha\nComputo",
                    "Fecha\nCese",
                    "Faltas",
                    "Basico",
                    u"Prom Bonificación",
                    u"Prom Comision",
                    "PROM. HRS\n EXTRAS",
                    "Rem\nCom",
                    'Meses',
                    'Dias',
                    'Monto\npor mes',
                    'Monto\npor dia',
                    "Vacaciones\nDevengadas",
                    "Vacaciones\nTruncas",
                    "Total\nVacaciones",
                    "ONP",
                    "AFP\nJUB",
                    "AFP\nSI",
                    "AFP\nCOM",
                    u"Neto\nTotal"]
        # fil = 4
        worksheet.write(
            x, 0,columnas[0], formatLeftColor)
        for i in range(1, len(columnas)):
            worksheet.write(x, i, columnas[i], boldbord)

        worksheet.set_row(x, 50)

        x = x+1

        filtro = []

        # query = 'select %s from planilla_tabular' % (','.join(fields))
        query = """
        select  id,
        identification_number,
        last_name_father ,
        last_name_mother ,
        names ,
        fecha_computable ,
        fecha_cese   ,        
        faltas        ,    
        basico         ,    
        comision        ,     
        bonificacion     ,       
        horas_extras_mean ,            
        remuneracion_computable,        
        meses           ,
        dias           ,
        monto_x_mes     ,    
        monto_x_dia      ,    
        vacaciones_devengadas        ,     
        vacaciones_truncas            ,
        total_vacaciones            ,
        onp   ,
        afp_jub,       
        afp_si  ,    
        afp_com  ,     
        neto_total              
        from planilla_liquidacion_vacaciones_line where planilla_liquidacion_id =%d
        
        """%(self.id)
        self.env.cr.execute(query)
        datos_planilla = self.env.cr.fetchall()
        range_row = len(datos_planilla[0] if len(datos_planilla) > 0 else 0)
        x_ini=x
        for i in range(len(datos_planilla)):
            for j in range(range_row):
                if j == 0 or j == 1:
                    worksheet.write(
                        x, j, datos_planilla[i][j] if datos_planilla[i][j] else '0.00', formatLeft)
                else:
                    if self.is_number_tryexcept(datos_planilla[i][j]):
                        worksheet.write_number(
                            x, j, float(datos_planilla[i][j]) if datos_planilla[i][j] else 0.00, numberdos)
                    else:
                        worksheet.write(
                            x, j, datos_planilla[i][j] if datos_planilla[i][j] else '5.00', numberdos)
            x = x+1
        x = x + 1

        j=7
        tmp_i=0
        for i in range(7,len(datos_planilla[0])):
            worksheet.write(x, j, '=SUM(%s%d:%s%d)' %(chr(ord('H')+tmp_i), x_ini+1, chr(ord('H')+tmp_i) , x), styleFooterSum)
            j+=1
            tmp_i+=1

        helper_liquidacion = self.env['planilla.helpers']
        # seteando tamaño de columnas
        col_widths =helper_liquidacion.get_col_widths(datos_planilla)
        
        worksheet.set_column(0, 0, col_widths[0])
        worksheet.set_column(1, 1, col_widths[1]-7)
        for i in range(2, len(col_widths)):
            worksheet.set_column(i, i, col_widths[i])


    @api.multi
    def calcular_liquidacion(self):
        self.planilla_gratificacion_lines.unlink()
        self.planilla_cts_lines.unlink()
        self.planilla_vacaciones_lines.unlink()
        self.planilla_indemnizacion_lines.unlink()

        mes_periodo = self.month
        days = calendar.monthrange(int(self.year), mes_periodo)[1]
        date_start_liquidacion = date(int(self.year), mes_periodo, 1)
        date_end_liquidacion = date(int(self.year), mes_periodo, days)

        date_start_liquidacion_cts = date(int(self.year), mes_periodo, 1)
        date_end_liquidacion_cts = date(int(self.year), mes_periodo, days)

        date_start_liquidacion_vacaciones = date(
            int(self.year), mes_periodo, 1)
        date_end_liquidacion_vacaciones = date(
            int(self.year), mes_periodo, days)

        if mes_periodo >= 1 and mes_periodo <= 6:
            rango_inicio_contrato = date(int(self.year), 6, 1)
            rango_fin_contrato = date(int(self.year), 6, 30)
            rango_inicio_planilla = date(int(self.year), 1, 1)
            rango_fin_planilla = date(int(self.year), 6, 30)
        else:
            rango_inicio_contrato = date(int(self.year), 12, 1)
            # rango_fin_contrato = date(int(self.year), 12, 31) #30 nov
            rango_fin_contrato = date(int(self.year), 11, 30)  # 30 nov
            rango_inicio_planilla = date(int(self.year), 7, 1)
            # rango_fin_planilla = date(int(self.year), 12, 31)
            rango_fin_planilla = date(int(self.year), 11, 30)

        if mes_periodo >= 5 and mes_periodo <= 10:  # mayo a octubre
            rango_inicio_planilla_cts = date(int(self.year), 5, 1)
            rango_fin_planilla_cts = date(int(self.year), 10, 31)
            # se usa para sacar los dia del periodo anterior
            anho_periodo_anterior_cts = int(self.year)
            tipo_cts = '12'
            tipo_gratificacion = '07'

        elif mes_periodo >= 1 and mes_periodo <= 4:  # enero a abril
            rango_inicio_planilla_cts = date(int(self.year)-1, 11, 1)
            rango_fin_planilla_cts = date(int(self.year), 4, 30)
            # se usa para sacar los dia del periodo anterior
            anho_periodo_anterior_cts = int(self.year)-1
            tipo_cts = '07'
            tipo_gratificacion = '12'
        else:  # solo queda noviembre y diciembre
            rango_inicio_planilla_cts = date(int(self.year), 11, 1)
            rango_fin_planilla_cts = date(int(self.year)+1, 4, 30)
            # se usa para sacar los dia del periodo anterior
            anho_periodo_anterior_cts = int(self.year)
            tipo_cts = '07'
            tipo_gratificacion ='07'

        if mes_periodo == 12:
            tipo_gratificacion = '12'

        contratos_empleado = self.env['hr.contract'].search(
            [('date_end', '>=', date_start_liquidacion_vacaciones), 
            ('date_end', '<=', date_end_liquidacion_vacaciones),
            ('regimen_laboral_empresa','not in',['practicante','microempresa']),
            ])
        
        for e,contrato in enumerate(contratos_empleado,1):
            # 1 busco los contratos de ese empleado
            contratos_empleado = self.env['hr.contract'].search(
                [('employee_id', '=', contrato.employee_id.id), 
                ('date_end', '<=', contrato.date_end)], order='date_end desc')
            if len(contratos_empleado) > 0:    
                # datetime
                fecha_ini = fields.Date.from_string(
                    contratos_empleado[0].date_start)
                fecha_fin_contrato = fields.Date.from_string(
                    contratos_empleado[0].date_end)
                # 2 busco los contratos anteriores que esten continuos(no mas de un dia de diferencia entre contratos)
                for i in range(1, len(contratos_empleado)):
                    c_empleado = contratos_empleado[i]
                    fecha_fin = fields.Date.from_string(c_empleado.date_end)
                    if abs(((fecha_fin)-(fecha_ini)).days) == 1:
                        fecha_ini = fields.Date.from_string(c_empleado.date_start)
                if self.month == 12:
                    grati = self.env['planilla.gratificacion'].search([('year','=',self.year),('tipo','=',self.month)])
                    employee_filtered = filter(lambda g:g.employee_id.id == contrato.employee_id.id,grati.planilla_gratificacion_lines)
                    if not employee_filtered:
                        self.calcular_gratificacion(contrato, rango_inicio_planilla, rango_fin_planilla,
                                                    fecha_ini, fecha_fin_contrato, date_start_liquidacion, date_end_liquidacion,e)
                else:
                    self.calcular_gratificacion(contrato, rango_inicio_planilla, rango_fin_planilla,
                                                    fecha_ini, fecha_fin_contrato, date_start_liquidacion, date_end_liquidacion,e)
                self.calcular_cts(contrato, rango_inicio_planilla_cts, rango_fin_planilla_cts,
                                  fecha_ini, fecha_fin_contrato, date_start_liquidacion, date_end_liquidacion, anho_periodo_anterior_cts, tipo_cts,tipo_gratificacion,e)
                self.calcular_vacaciones(
                    contrato, date_start_liquidacion_vacaciones, date_end_liquidacion_vacaciones, fecha_ini, fecha_fin_contrato,e)
        
        nomina = self.env['hr.payslip.run'].search([('date_start', '=', self.date_start), 
                                                    ('date_end', '=', self.date_end)])
        nomina.write({'liqui_flag':True})

        return self.env['planilla.warning'].info(title='Resultado de importacion', message="SE CALCULO LIQUIDACION DE MANERA EXITOSA!")

    @api.multi
    def calcular_gratificacion(self, contrato, rango_inicio_planilla, rango_fin_planilla, fecha_ini, fecha_fin, date_start_liquidacion, date_end_liquidacion,e):
        self.ensure_one()
        ultimo_mes_no_cuenta = False
        helper_liquidacion = self.env['planilla.helpers']
        parametros_gratificacion = self.env['planilla.gratificacion'].get_parametros_gratificacion()    
        if fecha_ini < rango_inicio_planilla:
            fecha_computable = rango_inicio_planilla
        else:
            fecha_computable = fecha_ini

        dias_mes_cese = calendar.monthrange(
            int(self.year), fecha_fin.month)[1]

        # meses = helper_liquidacion.diferencia_meses_gratificacion(
        #     fecha_computable, fecha_fin)

        meses, dias = helper_liquidacion.diferencia_meses_dias(
                fecha_computable, fecha_fin)
        if not self.calcular_meses_dias:
            dias = 0

        fecha_inicio_nominas = date(
            fecha_computable.year, fecha_computable.month, 1)
        fecha_fin_nominas = date(fecha_fin.year, fecha_fin.month, calendar.monthrange(fecha_fin.year, fecha_fin.month)[1])
        fecha_fin_nominas = fecha_fin - relativedelta(months=0)
        fecha_fin_nominas = date(fecha_fin_nominas.year, fecha_fin_nominas.month, calendar.monthrange(
            fecha_fin_nominas.year, fecha_fin_nominas.month)[1])

        sql = """
            select min(hp.id),sum(hwd.number_of_days) as days,min(hp.name) as name
            from hr_payslip hp
            inner join hr_contract hc on hc.id = hp.contract_id
            inner join hr_payslip_worked_days hwd on hwd.payslip_id = hp.id
            where hp.date_from >= '%s'
            and hp.date_to <= '%s'
            and hp.employee_id = %d
            and hc.regimen_laboral_empresa not in ('practicante','microempresa')
            and hwd.code in (%s)
            group by hp.employee_id, hp.payslip_run_id
        """%(fecha_inicio_nominas,
            fecha_fin_nominas,
            contrato.employee_id.id,
            ','.join("'%s'"%(wd.codigo) for wd in parametros_gratificacion.cod_wds))
        self.env.cr.execute(sql)
        conceptos = self.env.cr.dictfetchall()

        verificar_meses, _ = helper_liquidacion.diferencia_meses_dias(
            fecha_inicio_nominas, fecha_fin_nominas)
        if len(conceptos) != verificar_meses:
            fecha_encontradas = ' '.join(['\t-'+x['name']+'\n' for x in conceptos])
            if not fecha_encontradas:
                fecha_encontradas = '"No tiene nominas"'
            raise UserError(
                'Error en GRATIFICACION: El empleado %s debe tener nominas desde:\n %s hasta %s pero solo tiene nominas en las siguientes fechas:\n %s \nfaltan %d nominas, subsanelas por favor ' % (
                    contrato.employee_id.name_related, fecha_inicio_nominas, fecha_fin_nominas, fecha_encontradas, abs(len(
                        conceptos) - (verificar_meses))
                ))
        lines = []
        if contrato.hourly_worker:
            payslips = self.env['hr.payslip'].search([('employee_id','=',contrato.employee_id.id),
                                                        ('date_from','>=',rango_inicio_planilla),
                                                        ('date_to','<=',rango_fin_planilla)])
            for payslip in payslips:
                lines.append(next(iter(filter(lambda l:l.code == 'BAS',payslip.line_ids)),None))
            basico = sum([line.amount for line in lines])/6.0
        else:
            basico = helper_liquidacion.getBasicoByDate(date(fecha_fin_nominas.year,fecha_fin_nominas.month,1),fecha_fin_nominas,contrato.employee_id.id,parametros_gratificacion.cod_basico.code,True )  # conceptos[0].basico if conceptos else 0.0
        if parametros_gratificacion.cod_dias_faltas:
            faltas = helper_liquidacion.getSumFaltas(fecha_inicio_nominas,fecha_fin_nominas,contrato.employee_id.id,parametros_gratificacion.cod_dias_faltas.codigo ) #sum([x.dias_faltas for x in conceptos])
        else:
            faltas = 0
        afam = helper_liquidacion.getAsignacionFamiliarByDate(date(fecha_fin_nominas.year,fecha_fin_nominas.month,1),fecha_fin_nominas,contrato.employee_id.id,parametros_gratificacion.cod_asignacion_familiar.code )  #conceptos[0].asignacion_familiar if conceptos else 0.0

        comisiones_periodo, promedio_bonificaciones, promedio_horas_trabajo_extra = helper_liquidacion.calcula_comision_gratificacion_hrs_extras(
            contrato, fecha_inicio_nominas, fecha_fin_nominas, meses, fecha_fin)

        bonificacion_9 = 0
        bonificacion = promedio_bonificaciones
        comision = comisiones_periodo
        rem_computable = basico + bonificacion+comision + afam + promedio_horas_trabajo_extra
        if contrato.regimen_laboral_empresa == 'pequenhaempresa':
                rem_computable = rem_computable/2.0
        monto_x_mes = round(rem_computable/6.0, 2)
        monto_x_dia = round(monto_x_mes/30.0, 2)
        monto_x_meses = round(
            monto_x_mes*meses, 2) if meses != 6 else rem_computable
        monto_x_dias = round(monto_x_dia*dias, 2)
        total_faltas = round(monto_x_dia*faltas, 2)
        total_gratificacion = (monto_x_meses+monto_x_dias)-total_faltas

        if self.plus_9:
            if contrato.seguro_salud_id:
                bonificacion_9 =contrato.seguro_salud_id.porcentaje / \
                    100.0*float(total_gratificacion)
        vals = {
            'planilla_liquidacion_id': self.id,
            'orden':e,
            'employee_id': contrato.employee_id.id,
            'identification_number': contrato.employee_id.identification_id,
            'last_name_father': contrato.employee_id.a_paterno,
            'last_name_mother': contrato.employee_id.a_materno,
            'names': contrato.employee_id.nombres,
            'fecha_ingreso': fecha_ini,
            'fecha_computable': fecha_computable,
            'fecha_cese': fecha_fin,
            'meses': meses,
            'dias': dias,
            'faltas': faltas,
            'basico': basico,
            'a_familiar': afam,
            'comision': comisiones_periodo,
            'bonificacion': bonificacion,
            'horas_extras_mean': promedio_horas_trabajo_extra,
            'remuneracion_computable': rem_computable,
            'monto_x_mes': monto_x_mes,
            'monto_x_dia': monto_x_dia,
            'monto_x_meses': monto_x_meses,
            'monto_x_dias': monto_x_dias,
            'total_faltas': total_faltas,
            'total_gratificacion': total_gratificacion,
            'plus_9': bonificacion_9,
            'total': total_gratificacion+bonificacion_9
        }

        self.planilla_gratificacion_lines.create(vals)
        return True

    @api.multi
    def calcular_cts(self, contrato, rango_inicio_planilla, rango_fin_planilla, fecha_ini, fecha_fin, date_start_liquidacion, date_end_liquidacion, anho_periodo_anterior_cts, tipo_cts,tipo_gratificacion,e):
        self.ensure_one()
        ultimo_mes_no_cuenta = False
        helper_liquidacion = self.env['planilla.helpers']
        parametros_gratificacion = self.env['planilla.gratificacion'].get_parametros_gratificacion()

        # el resto se queda
        dias = 0
        dias_mes_cese = calendar.monthrange(
            int(fecha_fin.month), fecha_fin.month)[1]
        meses = 0
        if rango_inicio_planilla <= fecha_ini and rango_fin_planilla >= fecha_ini:
            fecha_computable = fecha_ini
        else:
            fecha_computable = rango_inicio_planilla

        meses, dias = helper_liquidacion.diferencia_meses_dias(
            fecha_computable, fecha_fin)

        fecha_inicio_nominas = date(
            fecha_computable.year, fecha_computable.month, 1)
        fecha_fin_nominas = fecha_fin - relativedelta(months=0)
        fecha_fin_nominas = date(fecha_fin_nominas.year, fecha_fin_nominas.month, calendar.monthrange(
            fecha_fin_nominas.year, fecha_fin_nominas.month)[1])

        sql = """
            select min(hp.id),sum(hwd.number_of_days) as days,min(hp.name) as name
            from hr_payslip hp
            inner join hr_contract hc on hc.id = hp.contract_id
            inner join hr_payslip_worked_days hwd on hwd.payslip_id = hp.id
            where hp.date_from >= '%s'
            and hp.date_to <= '%s'
            and hp.employee_id = %d
            and hc.regimen_laboral_empresa not in ('practicante','microempresa')
            and hwd.code in (%s)
            group by hp.employee_id, hp.payslip_run_id
        """%(fecha_inicio_nominas,
            fecha_fin_nominas,
            contrato.employee_id.id,
            ','.join("'%s'"%(wd.codigo) for wd in parametros_gratificacion.cod_wds)
            )
        self.env.cr.execute(sql)
        conceptos = self.env.cr.dictfetchall()

        # meses-1#meses-1 if ultimo_mes_no_cuenta else meses
        verificar_meses, _ = helper_liquidacion.diferencia_meses_dias(
            fecha_inicio_nominas, fecha_fin_nominas)

        if len(conceptos) != verificar_meses:
            fecha_encontradas = ' '.join(
                ['\t-'+x['name']+'\n' for x in conceptos])
            if not fecha_encontradas:
                fecha_encontradas = '"No tiene nominas"'
            raise UserError(
                'Error en CTS: El empleado %s debe tener nominas desde:\n %s hasta %s pero solo tiene nominas en las siguientes fechas:\n %s \nfaltan %d nominas, subsanelas por favor ' % (
                    contrato.employee_id.name_related, fecha_inicio_nominas, fecha_fin_nominas, fecha_encontradas, abs(len(
                        conceptos) - (verificar_meses))
                ))
        lines = []
        if contrato.hourly_worker:
            payslips = self.env['hr.payslip'].search([('employee_id','=',contrato.employee_id.id),
                                                        ('date_from','>=',rango_inicio_planilla),
                                                        ('date_to','<=',rango_fin_planilla)])
            for payslip in payslips:
                lines.append(next(iter(filter(lambda l:l.code == 'BAS',payslip.line_ids)),None))
            basico = sum([line.amount for line in lines])/6.0
        else:
            basico = helper_liquidacion.getBasicoByDate(date(fecha_fin_nominas.year,fecha_fin_nominas.month,1),fecha_fin_nominas,contrato.employee_id.id,parametros_gratificacion.cod_basico.code,True)  # conceptos[0].basico if conceptos else 0.0
        if parametros_gratificacion.cod_dias_faltas:
            faltas = helper_liquidacion.getSumFaltas(fecha_inicio_nominas,fecha_fin_nominas,contrato.employee_id.id,parametros_gratificacion.cod_dias_faltas.codigo ) #sum([x.dias_faltas for x in conceptos])
        else:
            faltas = 0
        afam = helper_liquidacion.getAsignacionFamiliarByDate(date(fecha_fin_nominas.year,fecha_fin_nominas.month,1),fecha_fin_nominas,contrato.employee_id.id,parametros_gratificacion.cod_asignacion_familiar.code )  #conceptos[0].asignacion_familiar if conceptos else 0.0

        if fecha_fin.month == 7 and fecha_fin.day > 15:
            query_gratificacion = """
            select total_gratificacion/6.0 as gratificacion from planilla_gratificacion pg 
            inner join planilla_gratificacion_line pgl 
            on pgl.planilla_gratificacion_id= pg.id 
            where employee_id =%d and year='%s' and tipo='%s' 
            """ % (contrato.employee_id, fecha_fin.year, '07')
        else:
            query_gratificacion = """
            select total_gratificacion/6.0 as gratificacion from planilla_gratificacion pg 
            inner join planilla_gratificacion_line pgl 
            on pgl.planilla_gratificacion_id= pg.id 
            where employee_id =%d and year='%s' and tipo='%s' 
            """ % (contrato.employee_id, anho_periodo_anterior_cts, tipo_gratificacion)

        self.env.cr.execute(query_gratificacion)
        gratificacion = self.env.cr.dictfetchone()
        gratificacion = gratificacion['gratificacion'] if gratificacion else 0.0

        query_dias_pasados = """
        select dias_proxima_fecha as dias_cts_periodo_anterior from planilla_cts pc 
        inner join planilla_cts_line pcl 
        on pc.id= pcl.planilla_cts_id
        where employee_id=%d    and year='%s' and tipo='%s'
        """ % (contrato.employee_id, anho_periodo_anterior_cts, tipo_cts)

        self.env.cr.execute(query_dias_pasados)
        dias_cts_periodo_anterior = self.env.cr.dictfetchone()
        dias_cts_periodo_anterior = dias_cts_periodo_anterior[
            'dias_cts_periodo_anterior'] if dias_cts_periodo_anterior else 0
        dias = dias+dias_cts_periodo_anterior

        helper_liquidacion = self.env['planilla.helpers']
        comisiones_periodo, promedio_bonificaciones, promedio_horas_trabajo_extra = helper_liquidacion.calcula_comision_gratificacion_hrs_extras(
            contrato, fecha_computable, fecha_fin_nominas, meses, fecha_fin)

        bonificacion = promedio_bonificaciones
        comision = comisiones_periodo

        rem_computable = basico+afam + gratificacion + bonificacion + comision + promedio_horas_trabajo_extra
        if contrato.regimen_laboral_empresa == 'pequenhaempresa':
                rem_computable = rem_computable/2.0
        monto_x_mes = round(rem_computable/12.0, 2)
        monto_x_dia = round(monto_x_mes/30.0, 2)
        monto_x_meses = round(monto_x_mes*meses, 2)
        monto_x_dias = round(monto_x_dia*dias, 2)
        total_faltas = round(monto_x_dia*faltas, 2)

        cts_soles = monto_x_dias+monto_x_meses-total_faltas
        cts_interes = 0.0
        otros_dtos = 0.0
        cts_a_pagar = (cts_soles+cts_interes)-otros_dtos

        tipo_cambio_venta = self.tipo_cambio
        cts_dolares = round(cts_a_pagar/tipo_cambio_venta, 2)
        cuenta_cts = contrato.employee_id.bacts_acc_number_rel
        banco = contrato.employee_id.bacts_bank_id_rel.id

        vals = {
            'planilla_liquidacion_id': self.id,
            'orden':e,
            'employee_id': contrato.employee_id.id,
            'contract_id': contrato.id,
            'identification_number': contrato.employee_id.identification_id,
            'last_name_father': contrato.employee_id.a_paterno,
            'last_name_mother': contrato.employee_id.a_materno,
            'names': contrato.employee_id.nombres,
            'fecha_ingreso': fecha_ini,
            'fecha_computable': fecha_computable,
            'fecha_cese': fecha_fin,
            'basico': basico,
            'a_familiar': afam,
            'gratificacion': gratificacion,
            'horas_extras_mean': promedio_horas_trabajo_extra,
            'bonificacion': bonificacion,
            'comision': comisiones_periodo,
            'base': rem_computable,
            'monto_x_mes': monto_x_mes,
            'monto_x_dia': monto_x_dia,
            'faltas': faltas,
            'meses': meses,
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
            'banco': banco
        }

        self.planilla_cts_lines.create(vals)
        return True

    @api.multi
    def calcular_vacaciones(self, contrato, date_start_liquidacion, date_end_liquidacion, fecha_ini, fecha_fin,e):
        self.ensure_one()
        helper_liquidacion = self.env['planilla.helpers']
        parametros_gratificacion = self.env['planilla.gratificacion'].get_parametros_gratificacion()
        '''
            se toma como base el año actual por ejm si su contrato inicia 2015-05-13
            se tendria que cambiar a 2019-05-13 esto solo si el mes de la liquidacion
            es mayor al mes en que se esta iniciando el contrato
        '''
        if self.month >= fecha_ini.month:
            fecha_ini = date(int(self.year), fecha_ini.month, fecha_ini.day)
        else:
            fecha_ini = date(int(self.year)-1, fecha_ini.month, fecha_ini.day)

        fecha_computable = fecha_fin - relativedelta(months=+6)

        dias = 0
        dias_mes_cese = calendar.monthrange(
            int(fecha_fin.month), fecha_fin.month)[1]
        if fecha_computable < fecha_ini:
            fecha_computable = fecha_ini
        dias_del_mes_fin = calendar.monthrange(
            int(self.year), fecha_fin.month)[1]


        meses, _ = helper_liquidacion.diferencia_meses_dias(
            fecha_ini, fecha_fin)

        mes_tmp = date(fecha_fin.year, fecha_fin.month, fecha_ini.day)
        if mes_tmp > fecha_fin:
            dias = abs(mes_tmp-fecha_fin)+timedelta(days=1)
            dias = 31-dias.days
        else:
            if fecha_fin.day == dias_mes_cese and fecha_ini.day == 1:
                dias = 0
                meses += 1
            else:
                dias = abs(fecha_ini.day-fecha_fin.day)+1

        meses, dias = helper_liquidacion.diferencia_meses_dias(
            fecha_ini, fecha_fin)

        # 4 sacando basico afam y faltas
        if fecha_fin.month-fecha_ini.month == 0:
            # solo esta un mes o menos, no hay nomina anterior
            basico = contrato.wage
            faltas = 0.0
            afam = 0.0
            comisiones_periodo = 0.0
            promedio_bonificaciones = 0.0
            promedio_horas_trabajo_extra = 0.0
            fecha_computable = date(
                fecha_fin.year, fecha_ini.month, fecha_ini.day)
        else:
            fecha_inicio_nominas = date(fecha_ini.year, fecha_ini.month, 1)
            fecha_fin_nominas = fecha_fin - relativedelta(months=0)
            fecha_fin_nominas = date(fecha_fin_nominas.year, fecha_fin_nominas.month, calendar.monthrange(
                fecha_fin_nominas.year, fecha_fin_nominas.month)[1])

            sql = """
                select min(hp.id),sum(hwd.number_of_days) as days,min(hp.name) as name
                from hr_payslip hp
                inner join hr_contract hc on hc.id = hp.contract_id
                inner join hr_payslip_worked_days hwd on hwd.payslip_id = hp.id
                where hp.date_from >= '%s'
                and hp.date_to <= '%s'
                and hp.employee_id = %d
                and hc.regimen_laboral_empresa not in ('practicante','microempresa')
                and hwd.code in (%s)
                group by hp.employee_id, hp.payslip_run_id
            """%(fecha_inicio_nominas,fecha_fin_nominas,contrato.employee_id.id,
                ','.join("'%s'"%(wd.codigo) for wd in parametros_gratificacion.cod_wds))
            self.env.cr.execute(sql)
            conceptos = self.env.cr.dictfetchall()

            verificar_meses, _ = helper_liquidacion.diferencia_meses_dias(
                fecha_inicio_nominas, fecha_fin_nominas)

            if len(conceptos) != verificar_meses:
                fecha_encontradas = ' '.join(['\t-'+x['name']+'\n' for x in conceptos])
                if not fecha_encontradas:
                    fecha_encontradas = '"No tiene nominas"'
                raise UserError(
                    'Error en VACACIONES: El empleado %s debe tener nominas desde:\n %s hasta %s pero solo tiene nominas en las siguientes fechas:\n %s \nfaltan %d nominas, subsanelas por favor ' % (
                        contrato.employee_id.name_related, fecha_inicio_nominas, fecha_fin_nominas, fecha_encontradas, abs(len(
                            conceptos) - (verificar_meses))
                    ))
            if contrato.hourly_worker:
                payslips = self.env['hr.payslip'].search([('employee_id','=',contrato.employee_id.id),
                                                            ('date_from','>=',rango_inicio_planilla),
                                                            ('date_to','<=',rango_fin_planilla)])
                for payslip in payslips:
                    lines.append(next(iter(filter(lambda l:l.code == 'BAS',payslip.line_ids)),None))
                basico = sum([line.amount for line in lines])/6.0
            else:
                basico = helper_liquidacion.getBasicoByDate(date(fecha_fin_nominas.year,fecha_fin_nominas.month,1),fecha_fin_nominas, contrato.employee_id.id,parametros_gratificacion.cod_basico.code,True)  # conceptos[0].basico if conceptos else 0.0
            
            if parametros_gratificacion.cod_dias_faltas:
                faltas = helper_liquidacion.getSumFaltas(fecha_inicio_nominas,fecha_fin_nominas, contrato.employee_id.id,parametros_gratificacion.cod_dias_faltas.codigo ) #sum([x.dias_faltas for x in conceptos])
            else:
                faltas = 0
            helper_liquidacion = self.env['planilla.helpers']
            meses_comisiones = fecha_fin.month-fecha_computable.month
            comisiones_periodo, promedio_bonificaciones, promedio_horas_trabajo_extra = helper_liquidacion.calcula_comision_gratificacion_hrs_extras(
                contrato, fecha_computable, fecha_fin_nominas, meses_comisiones, fecha_fin)

        bonificacion = promedio_bonificaciones
        comision = comisiones_periodo        
        afam = 93.0 if contrato.employee_id.children > 0 else 0.0

        rem_computable = basico + afam + bonificacion + comision + promedio_horas_trabajo_extra
        if contrato.regimen_laboral_empresa == 'pequenhaempresa':
                rem_computable = rem_computable/2.0
        monto_x_mes = round(rem_computable/12.0, 2)
        monto_x_dia = round(monto_x_mes/30.0, 2)
        monto_x_meses = round(monto_x_mes*meses, 2)
        monto_x_dias = round(monto_x_dia*dias, 2)
        total_faltas = round(monto_x_dia*faltas, 2)

        vacaciones_truncas = monto_x_meses+monto_x_dias
        vacaciones_devengadas = 0
        total_vacaciones = vacaciones_truncas+vacaciones_devengadas

        afiliacion_lines = self.env['planilla.afiliacion.line'].search(
            [('fecha_ini', '=', date_start_liquidacion), ('fecha_fin', '=', date_end_liquidacion)])

        query_afiliacion = """
        select lower(pa.entidad) as entidad,pa.fondo,segi,comf,comm from planilla_afiliacion_line pal
        inner join planilla_afiliacion pa
        on pa.id = pal.planilla_afiliacion_id
        where fecha_ini= '%s' and fecha_fin ='%s' and planilla_afiliacion_id=%d
        """ % (date_start_liquidacion, date_end_liquidacion, contrato.afiliacion_id)

        self.env.cr.execute(query_afiliacion)
        afiliacion = self.env.cr.dictfetchone()
        onp = 0
        afp_jub = 0
        afp_si = 0
        afp_com = 0

        if contrato.afiliacion_id.entidad.lower() == 'onp':
            onp = contrato.afiliacion_id.fondo/100*total_vacaciones
        else:
            afp_jub = contrato.afiliacion_id.fondo/100*total_vacaciones
            afp_si = contrato.afiliacion_id.prima_s/100*total_vacaciones
            afp_com = contrato.afiliacion_id.com_mix/100*total_vacaciones

        neto_total = total_vacaciones - (onp+afp_jub+afp_si+afp_com)

        vals = {
            'planilla_liquidacion_id': self.id,
            'orden':e,
            'employee_id': contrato.employee_id.id,
            'contract_id': contrato.id,
            'identification_number': contrato.employee_id.identification_id,
            'last_name_father': contrato.employee_id.a_paterno,
            'last_name_mother': contrato.employee_id.a_materno,
            'names': contrato.employee_id.nombres,
            'fecha_ingreso': fecha_ini,
            'fecha_computable': fecha_computable,
            'fecha_cese': fecha_fin,
            'faltas': faltas,
            'basico': basico,
            'afam': afam,
            'comision': comision,
            'bonificacion': bonificacion,
            'horas_extras_mean': promedio_horas_trabajo_extra,
            'remuneracion_computable': rem_computable,
            'meses': meses,
            'dias': dias,
            'monto_x_mes': monto_x_meses,
            'monto_x_dia': monto_x_dias,
            'vacaciones_devengadas': '',
            'vacaciones_truncas': vacaciones_truncas,
            'total_vacaciones': total_vacaciones,
            'onp': onp,
            'afp_jub': afp_jub,
            'afp_si': afp_si,
            'afp_com': afp_com,
            'neto_total': neto_total
        }

        self.planilla_vacaciones_lines.create(vals)
        vals = {
            'planilla_liquidacion_id': self.id,
            'orden':e,
            'employee_id': contrato.employee_id.id,
            'contract_id': contrato.id,
            'identification_number': contrato.employee_id.identification_id,
            'last_name_father': contrato.employee_id.a_paterno,
            'last_name_mother': contrato.employee_id.a_materno,
            'names': contrato.employee_id.nombres,
            'fecha_ingreso': fecha_ini,
            'fecha_cese': fecha_fin
        }
        self.planilla_indemnizacion_lines.create(vals)


        return True
