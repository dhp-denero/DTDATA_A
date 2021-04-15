# -*- coding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import sys
from datetime import datetime
import os
import decimal
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red, black, blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, PageBreak, Spacer
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import simpleSplit
from cgi import escape
from reportlab import platypus


class PlanillaCtsLiquidacionSemestral(models.TransientModel):
    _name = "planilla.cts.liquidacion.semestral.wizard"

    encargado = fields.Many2one('hr.employee', "Encargado", required=1)
    fecha_deposito = fields.Date("Fecha", required=1)

    @api.multi
    def get_pdf(self):
        reload(sys)
        planilla_ajustes = self.env['planilla.ajustes'].get_parametros_ajustes(
        )
        sys.setdefaultencoding('iso-8859-1')
        width, height = A4  # 595 , 842
        wReal = width - 30
        hReal = height - 40
        try:
            direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
        except: 
            raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
        doc = SimpleDocTemplate(direccion+"CTS.pdf", pagesize=A4)

        colorfondo = colors.lightblue
        elements = []
        # Definiendo los estilos de la cabecera.
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='LeftBold',
                                  fontSize=10,
                                  fontName='Times-Bold',

                                  ))
        styles.add(ParagraphStyle(name='Left',
                                  fontSize=10,
                                  fontName='Times-Roman',
                                  ))
        styles.add(ParagraphStyle(name='Tab',
                                  fontSize=10,
                                  fontName='Times-Roman',
                                  leftIndent=20,

                                  ))
        styles.add(ParagraphStyle(name='RightBold',
                                  fontSize=10,
                                  fontName='Times-Bold',
                                  alignment=TA_RIGHT,
                                  ))

        styles.add(ParagraphStyle(name='Right',
                                  fontSize=10,
                                  alignment=TA_RIGHT,
                                  fontName='Times-Roman',
                                  ))
        estilo_c = [
            ('SPAN', (0, 0), (1, 0)),
            ('SPAN', (2, 0), (3, 0)),
            ('ALIGN', (2, 0), (3, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]
        # ------------------------------------------------------Insertando Data-----------------------------------------
        lines = self.env['planilla.cts.line'].search(
            [('planilla_cts_id', '=', self.env.context['active_id'])])
        for line in lines:
            employee = self.env['hr.employee'].search(
                [('id', '=', line.employee_id.id)])
            name = line.names + ' ' + line.last_name_father + ' ' + line.last_name_mother
            # --------------------------------------------------Cabecera
            # a = Image(direccion+"calquipalleft.png")
            # a.drawHeight = 50
            # a.drawWidth = 95
            # b = Image(direccion+"calquipalright.png")
            # b.drawHeight = 60
            # b.drawWidth = 80
            cabecera = [['', '', '', ''], ]
            table_c = Table(cabecera, colWidths=[
                            120]*2, rowHeights=50, style=estilo_c)
            elements.append(table_c)
            elements.append(Spacer(0, 8))
            # ----------------------------------------------------Datos
            cadt = [[u'LIQUIDACIÓN DE DEPÓSITO SEMESTRAL DE CTS']]
            t = Table(cadt, colWidths=[450], rowHeights=[20])
            t.setStyle(TableStyle(
                [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, -1), (-1, -1), 'TOP'),
                    ('FONTSIZE', (0, 0), (-1, -1), 14),
                    ('FONT', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ]
            ))
            elements.append(t)
            elements.append(Spacer(0, 20))
            rc = self.env['res.company'].search([])[0]
            employee_name = employee.a_paterno+' '+employee.a_materno + \
                ' '+employee.nombres if employee.nombres else ''
            text = u"""<b>"""+(rc.name if rc.name else '')+u"""</b> con RUC <b>Nº """+(planilla_ajustes.ruc if planilla_ajustes.ruc else '')+"""</b>, domiciliada en """+(rc.street if rc.street else '')+""",
                                representado por su <b>"""+(self.encargado.job_id.name if self.encargado.job_id.name else '')+(u' Señor ' if self.encargado.gender == 'male' else u' Señora ')+self.encargado.name_related+u"""</b>,
                                en aplicación del artículo 24º del TUO del D.Leg Nº 650, Ley de Compensación por Tiempo de
                                Servicios, aprobado mediante el D.S. Nº 001-97-TR,
                                otorga a <b>"""+employee_name+u"""</b>,
                                la presente constancia del depósito de su compensación por Tiempo de Servicios realizado el %d de %s del %d""" % (fields.Date.from_string(self.fecha_deposito).day,self.env['planilla.helpers'].date_to_month(fields.Date.from_string(self.fecha_deposito).month), fields.Date.from_string(self.fecha_deposito).year)+u""" en la cuenta CTS """ + (u'(Dólares Americanos)' if employee.bacts_currency_id_rel.name == 'USD' else '(Soles)') + u"""
                    <b>Nº """+(line.cta_cts if line.cta_cts else '')+"""</b> del <b>"""+(line.banco.name if line.banco.name else '')+u"""</b>, por los siguientes montos y periodos:"""
            elements.append(Paragraph(text, styles["Justify"]))
            periodo = ''
            if line.planilla_cts_id.tipo == '07':
                periodo = 'Del 01 de Mayo del ' + line.planilla_cts_id.year + \
                    ' al 31 de Octubre del ' + line.planilla_cts_id.year
            else:
                periodo = 'Del 01 de Noviembre del ' + \
                    str(int(line.planilla_cts_id.year)-1) + \
                    ' al 30 de Abril del ' + line.planilla_cts_id.year
            periodo = periodo + ': ' + \
                str(line.meses) + ' meses, ' + str(line.dias) + u' días'
            datat = [
                [Paragraph('<b>1. <u>FECHA DE INGRESO</u>: </b>'+datetime.strptime(str(
                    line.fecha_ingreso), '%Y-%m-%d').strftime("%d/%m/%Y"), styles["Left"]), '', ''],
                [Paragraph('2. <u>PERIODO QUE SE LIQUIDA</u>:',
                           styles["LeftBold"]), '', ''],
                [Paragraph(periodo, styles["Tab"]), '', ''],
                [Paragraph('3. <u>REMUNERACION COMPUTABLE</u>:',
                           styles["LeftBold"]), '', ''],
                [Paragraph('-  Básico', styles["Tab"]), 'S/.', Paragraph(
                    '{:,.2f}'.format(decimal.Decimal("%0.2f" % line.basico)), styles["Right"])],
                [Paragraph('-  Asignación Familiar', styles["Tab"]), 'S/.', Paragraph(
                    '{:,.2f}'.format(decimal.Decimal("%0.2f" % line.a_familiar)), styles["Right"])],
                [Paragraph('-  Horas Extra', styles["Tab"]), 'S/.', Paragraph('{:,.2f}'.format(
                    decimal.Decimal("%0.2f" % line.horas_extras_mean)), styles["Right"])],
                [Paragraph('-  Gratificaciones', styles["Tab"]), 'S/.', Paragraph(
                    '{:,.2f}'.format(decimal.Decimal("%0.2f" % line.gratificacion)), styles["Right"])],
                [Paragraph('-  Bonificación', styles["Tab"]), 'S/.', Paragraph(
                    '{:,.2f}'.format(decimal.Decimal("%0.2f" % line.bonificacion)), styles["Right"])],
                [Paragraph('-  Comisión', styles["Tab"]), 'S/.', Paragraph(
                    '{:,.2f}'.format(decimal.Decimal("%0.2f" % line.comision)), styles["Right"])],
                [Paragraph('-  Feriados Trabajados', styles["Tab"]), 'S/.', Paragraph(
                    '{:,.2f}'.format(decimal.Decimal("%0.2f" % 0.00)), styles["Right"])],
                # [Paragraph('-  Inasistencias',styles["Tab"]),'S/.',Paragraph('{:,.2f}'.format(decimal.Decimal("%0.2f" % line.absences_total)),styles["Right"])],
            ]

            # conceptos = []
            n_lines = 0
            # for con in line.conceptos_lines:
            #     conceptos.append([Paragraph('-  '+con.concepto_id.name,styles["Tab"]),'S/.',Paragraph('{:,.2f}'.format(decimal.Decimal("%0.2f" % con.monto)),styles["Right"])])
            #     n_lines += 1
            # datat += conceptos

            datat += [[Paragraph('TOTAL', styles["RightBold"]), 'S/.', Paragraph('{:,.2f}'.format(decimal.Decimal("%0.2f" % line.base)), styles["RightBold"])],
                      ['', '', ''],
                      [Paragraph('<u>CALCULO</u>', styles["LeftBold"]), '', ''],
                      [Paragraph('  -  Por los meses completos:',
                                 styles["LeftBold"]), '', ''],
                      [Paragraph("S/. {0} ÷ 12 x {1} mes(es)".format(str(line.base), str(line.meses)), styles["Tab"]), 'S/.',
                       Paragraph('{:,.2f}'.format(decimal.Decimal("%0.2f" % line.monto_x_meses)), styles["Right"])],
                      [Paragraph('  -  Por los dias completos:',
                                 styles["LeftBold"]), '', ''],
                      [Paragraph("S/. {0} ÷ 12 ÷ 30 x {1} día(s)".format(str(line.base), str(line.dias)), styles["Tab"]),
                       'S/.', Paragraph('{:,.2f}'.format(decimal.Decimal("%0.2f" % line.monto_x_dias)), styles["Right"])],
                      [Paragraph('  -  Faltas:', styles["LeftBold"]), '', ''],
                      [Paragraph("S/. {0} ÷ 12 ÷ 30 x {1} día(s)".format(str(line.base), str(line.faltas)), styles["Tab"]),
                       'S/. ', Paragraph('{:,.2f}'.format(decimal.Decimal("%0.2f" % -line.total_faltas)), styles["Right"])],
                      [Paragraph('TOTAL', styles["RightBold"]), 'S/.', Paragraph('{:,.2f}'.format(
                          decimal.Decimal("%0.2f" % line.cts_soles)), styles["RightBold"])],
                      ['', '', ''], ]

            table2 = Table(datat, colWidths=[350, 20, 80])
            table2.setStyle(TableStyle(
                [
                    # ('BOX',(0,0),(-1,-1),2, colors.black),
                    # ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('FONT', (0, 0), (-1, -1), 'Times-Bold'),
                    ('ALIGN', (0, 2), (-1, 2), 'RIGHT'),
                    ('LINEABOVE', (2, 11+n_lines),
                     (2, 11+n_lines), 1.3, colors.black),
                    ('LINEABOVE', (2, 20+n_lines),
                     (2, 20+n_lines), 1.3, colors.black),
                ]
            ))
            elements.append(Spacer(0, 1))
            elements.append(table2)
            if employee.bacts_currency_id_rel.name == 'USD':
                datat = [
                    [Paragraph('MONTO DEPOSITADO (*)', styles["LeftBold"]), '$', Paragraph(
                        '{:,.2f}'.format(decimal.Decimal("%0.2f" % line.cts_dolares)), styles["RightBold"])],
                    ['', '', ''],
                    [Paragraph("(*) Moneda Extranjera: Tipo de Cambio {0}".format(
                        str(line.tipo_cambio_venta)), styles["LeftBold"]), '', ''],
                    ['', '', ''],
                ]
                table3 = Table(datat, colWidths=[350, 20, 80])
                table3.setStyle(TableStyle(
                    [
                        # ('BOX',(0,0),(-1,-1),2, colors.black),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('FONT', (0, 0), (-1, -1), 'Times-Bold'),
                        ('BOX', (2, 0), (2, 0), 1.3, colors.black),
                    ]
                ))
                elements.append(table3)
            elements.append(Spacer(0, 50))
            dataf = [
                [(rc.name if rc.name else ''), '', employee_name],
                ['EMPLEADOR', '', "DNI: " +
                    employee.identification_id if employee.identification_id else ''],
                ['', '', 'TRABAJADOR(A)'],
            ]
            table4 = Table(dataf, colWidths=[200, 50, 200])
            table4.setStyle(TableStyle(
                [
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('FONT', (0, 0), (-1, -1), 'Times-Bold'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('LINEABOVE', (0, 0), (0, 0), 1.1, colors.black),
                    ('LINEABOVE', (2, 0), (2, 0), 1.1, colors.black),
                ]
            ))
            elements.append(table4)
            elements.append(PageBreak())
        doc.build(elements)

        f = open(direccion+'CTS.pdf', 'rb')

        vals = {
            'output_name': 'CTS.pdf',
            'output_file': f.read().encode("base64"),
        }

        sfs_id = self.env['planilla.export.file'].create(vals)

        return {
            "type": "ir.actions.act_window",
            "res_model": "planilla.export.file",
            "views": [[False, "form"]],
            "res_id": sfs_id.id,
            "target": "new",
        }
