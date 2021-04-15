# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from datetime import date, datetime
from odoo.exceptions import ValidationError, UserError
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red, black, blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, Table, PageBreak
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import simpleSplit
from cgi import escape
import base64
import io
from xlsxwriter.workbook import Workbook
import sys
reload(sys)
sys.setdefaultencoding('iso-8859-1')
import os
import copy
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import StringIO
import time
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

import calendar
from datetime import date, datetime
from openerp.osv import osv
from math import modf
from decimal import *
import traceback
from lxml import etree
from StringIO import StringIO
import time

class HrPayslipRun(models.Model):
	_inherit = ['hr.payslip.run']

	@api.multi
	def exportar_planilla_tabular_xlsx(self):
		if len(self.ids) > 1:
			raise UserError(
				'Solo se puede mostrar una planilla a la vez, seleccione solo una nómina')

		self.env['planilla.planilla.tabular.wizard'].reconstruye_tabla(self.date_start,self.date_end)

		try:
			direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		workbook = Workbook(direccion+'planilla_tabular.xls')
		worksheet = workbook.add_worksheet(
			str(self.id)+'-'+self.date_start+'-'+self.date_end)
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
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'right'})
		formatLeft = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'font_size': fontSize})
		formatLeftColor = workbook.add_format(
			{'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'bg_color': '#99CCFF', 'font_size': fontSize})
		styleFooterSum = workbook.add_format(
			{'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'right', 'font_size': fontSize, 'top': 1, 'bottom': 2})
		styleFooterSum.set_bottom(6)
		numberdos.set_font_size(fontSize)
		bord = workbook.add_format()
		bord.set_border(style=1)
		bord.set_text_wrap()
		# numberdos.set_border(style=1)

		title = workbook.add_format({'bold': True, 'font_name': 'Arial'})
		title.set_align('center')
		title.set_align('vcenter')
		# title.set_text_wrap()
		title.set_font_size(18)
		company = self.env['res.company'].search([], limit=1)[0]

		x = 0

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		worksheet.merge_range(
			'D1:O1', u"PLANILLA DE SUELDOS Y SALARIOS", title)
		worksheet.set_row(x, 29)
		x = x+2

		worksheet.write(x, 0, u"Empresa:", bold)
		worksheet.write(x, 1, company.name, formatLeft)

		x = x+1
		worksheet.write(x, 0, u"Mes:", bold)
		worksheet.write(
			x, 1, self.get_mes(int(self.date_end[5:7]) if self.date_end else 0).upper()+"-"+self.date_end[:4], formatLeft)

		x = x+3

		header_planilla_tabular = self.env['ir.model.fields'].search(
			[('name', 'like', 'x_%'), ('model', '=', 'planilla.tabular')], order="create_date")
		worksheet.write(x, 0, header_planilla_tabular[0].field_description, formatLeftColor)
		for i in range(1, len(header_planilla_tabular)):
			worksheet.write(x, i, header_planilla_tabular[i].field_description, boldbord)

		worksheet.write(x,i+1,'Aportes ESSALUD',boldbord)
		worksheet.set_row(x, 50)

		fields = ['\"'+column.name+'\"' for column in header_planilla_tabular]
		x = x+1

		filtro = []

		query = 'select %s from planilla_tabular' % (','.join(fields))

		self.env.cr.execute(query)
		datos_planilla = self.env.cr.fetchall()
		range_row = len(datos_planilla[0] if len(datos_planilla) > 0 else 0)
		total_essalud = 0

		for i in range(len(datos_planilla)):
			# print(datos_planilla[i][0])
			for j in range(range_row):

				if j == 0 or j == 1:

					worksheet.write(x, j, datos_planilla[i][j] if datos_planilla[i][j] else '0.00', formatLeft)
				else:
					worksheet.write(x, j, datos_planilla[i][j] if datos_planilla[i][j] else '0.00', numberdos)
			essalud = self.env['hr.payslip'].browse(datos_planilla[i][5]).essalud
			worksheet.write(x,j+1,essalud,formatLeft)
			total_essalud += essalud
			x = x+1
		x = x + 1
		datos_planilla_transpuesta = zip(*datos_planilla)
		for j in range(5, len(datos_planilla_transpuesta)):
			worksheet.write(x, j, sum([float(d) for d in datos_planilla_transpuesta[j]]), styleFooterSum)

		worksheet.write(x,j+1,total_essalud,styleFooterSum)

		# seteando tamaño de columnas
		col_widths = self.get_col_widths(datos_planilla)
		worksheet.set_column(0,0, col_widths[0]-10)
		worksheet.set_column(1,1, col_widths[1]-7)
		worksheet.set_column(2,2, col_widths[0]-10)
		worksheet.set_column(3,3, col_widths[0])

		for i in range(4, len(col_widths)):

			worksheet.set_column(i, i, col_widths[i])

		worksheet.set_column('E:E',None,None,{'hidden':True})
		worksheet.set_column('F:F',None,None,{'hidden':True})

		workbook.close()

		f = open(direccion+'planilla_tabular.xls', 'rb')

		vals = {
			'output_name': 'planilla_tabular.xls',
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

class PlanillaPlanillaTabularWizard(models.TransientModel):

    _inherit = "planilla.planilla.tabular.wizard"

    @api.multi
    def reconstruye_tabla(self,date_start,date_end):
        query_extension = """
        CREATE EXTENSION if not exists tablefunc;
        """
        self.env.cr.execute(query_extension)

        planilla_ajustes = self.env['planilla.ajustes'].search([], limit=1)
        if not planilla_ajustes.planilla_tabular_columnas:
            raise UserError('Falta configurar Columnas para planilla tabular en Parametros/Parametros Boletas de Pago/')
        planilla_tabular_columnas = planilla_ajustes.planilla_tabular_columnas.strip().split(',')
        reglas_salariales_array = ['\''+x[:8]+'\',' for x in planilla_tabular_columnas]
        reglas_salariales_search = ''.join(reglas_salariales_array)
        reglas_salariales_search = reglas_salariales_search[:-1]

        query_larger_structure = """
            WITH RECURSIVE t(id, parent_id,name,rulename) AS (
            SELECT t.id, t.parent_id,t.name,sr.name as rulename FROM hr_payroll_structure t
                inner join hr_structure_salary_rule_rel srl
                on srl.struct_id = t.id
                inner join hr_salary_rule sr
                on sr.id = srl.rule_id
            WHERE parent_id is null
            UNION
            SELECT hr_payroll_structure.id, hr_payroll_structure.parent_id,hr_payroll_structure.name,sr.name as rulename
                FROM hr_payroll_structure
                JOIN t ON hr_payroll_structure.parent_id = t.id
                inner join hr_structure_salary_rule_rel srl
                on srl.struct_id = t.id
                inner join hr_salary_rule sr
                on sr.id = srl.rule_id
            ) SELECT id,name,count(id) as count FROM t
            group by id,name
            order by count desc
            limit 1;
        """

        self.env.cr.execute(query_larger_structure)
        structure_data = self.env.cr.dictfetchone()

        query_salary_rules_columns = """
        select sr.name,sr.code
        from hr_salary_rule sr
        where sr.code in (%s) and sr.appears_on_payslip='t'
        order by sr.sequence
        """ % reglas_salariales_search
        self.env.cr.execute(query_salary_rules_columns)
        salary_rules_colums = self.env.cr.dictfetchall()
        im = self.env['ir.model'].search(
            [('model', '=', 'planilla.tabular')])[0]

        # eliminando datos y columnas anteriores
        informacion = self.env['planilla.tabular'].search([])
        for info in informacion:
            info.id
            info.unlink()
        query_eliminar_columnas = """
        delete from ir_model_fields
        where model_id ="""+str(im.id)+""" and name like 'x_%'
        """


        res_del = self.env.cr.execute(query_eliminar_columnas)

        planilla_tree_view = self.env['ir.model.data'].xmlid_to_object(
            'planilla.view_planilla_tabular_tree')
        arch_in = etree.XML(
            bytes(bytearray(planilla_tree_view.arch, encoding='utf-8')))
        start_concepts = arch_in.xpath("//tree")[0]
        for ch in start_concepts:
            ch.getparent().remove(ch)

        fields = ''
        fields += 'x_employee_id text,'

        self.env['ir.model.fields'].create({
            'model_id': im.id,
            'name': 'x_employee_id',
            'field_description': 'EMPLEADO',
            'ttype': 'char',
            'state': 'manual',
        })
        etree.SubElement(start_concepts, "field",
                         name='x_employee_id', sum='x_employee_id')
        fields += 'x_dni text,'

        self.env['ir.model.fields'].create({
            'model_id': im.id,
            'name': 'x_dni',
            'field_description': 'DNI',
            'ttype': 'char',
            'state': 'manual',
        })
        etree.SubElement(start_concepts, "field", name='x_dni', sum='x_dni')

        fields += 'x_afiliacion_id text,'

        self.env['ir.model.fields'].create({
            'model_id': im.id,
            'name': 'x_afiliacion_id',
            'field_description': 'AFILIACION',
            'ttype': 'char',
            'state': 'manual',
        })
        etree.SubElement(start_concepts, "field",
                         name='x_afiliacion_id', sum='x_afiliacion_id')

        fields += 'x_cta_analitica text,'

        self.env['ir.model.fields'].create({
            'model_id': im.id,
            'name': 'x_cta_analitica',
            'field_description': u'CTA. ANALÍTICA',
            'ttype': 'char',
            'state': 'manual',
        })
        etree.SubElement(start_concepts, "field",
                         name='x_afiliacion_id', sum='x_afiliacion_id')

        fields += 'x_contract_id int,'

        self.env['ir.model.fields'].create({
            'model_id': im.id,
            'name': 'x_contract_id',
            'field_description': 'CONTRATO',
            'ttype': 'integer',
            'state': 'manual',
        })
        etree.SubElement(start_concepts, "field",
                         name='x_contract_id', sum='x_contract_id')

        fields += 'x_payslip_id int,'

        self.env['ir.model.fields'].create({
            'model_id': im.id,
            'name': 'x_payslip_id',
            'field_description': 'NOMINA',
            'ttype': 'integer',
            'state': 'manual',
        })
        etree.SubElement(start_concepts, "field",
                         name='x_afiliacion_id', sum='x_afiliacion_id')

        start_time = time.time()

        rules = []
        # insertando nuevas columnas
        for salary_rule in salary_rules_colums:
            fields += '"x_'+salary_rule['code'] + '" numeric,'

            pmodel_vals = {
                'model_id': im.id,
                'name': 'x_'+salary_rule['code'],
                'field_description': salary_rule['name'],
                'ttype': 'float',
                'state': 'manual',
            }
            rules.append(pmodel_vals)

            self.env['ir.model.fields'].create(pmodel_vals)
            etree.SubElement(start_concepts, "field", name='x_' +
                             salary_rule['code'], sum='x_'+salary_rule['code'])
        planilla_tree_view.write({'arch': etree.tostring(
            arch_in, xml_declaration=True, encoding="utf-8")})
        planilla_tree_view.refresh()

        fields = fields[:-1] if len(fields) > 0 else fields
        query_pivot_table = """
        SELECT * FROM crosstab(
            $$
                select
                t.name_related as name_related,
                min(t.identification_id) as identification_id,
                min(t.entidad) as entidad,
                min(t.codigo) as cta_analitica,
                min(t.id) as id,
                min(t.payslip_id) as payslip_id,
                min(t.sequence) as sequence,
                sum(t.total) as total

                from (
                    select distinct
                    case when hc.regimen_laboral_empresa = 'practicante' then trim(both from e.nombres)||' '||trim(both from e.a_paterno)||' '||trim(both from e.a_materno)||' (practicante)' else trim(both from e.nombres)||' '||trim(both from e.a_paterno)||' '||trim(both from e.a_materno) end as name_related,
                    e.identification_id,
                    pa.entidad,
                    pda.codigo,
                    hc.id,
                    hp.id as payslip_id,
                    hpl.sequence,
                    hpl.total
                    from hr_payslip hp
                    inner join hr_payslip_line hpl on hp.id=hpl.slip_id
                    inner join hr_employee e on e.id = hp.employee_id
                    inner join hr_contract hc on hc.id = hp.contract_id
                    inner join planilla_afiliacion pa on pa.id = hc.afiliacion_id
                    left join planilla_distribucion_analitica pda on pda.id = hc.distribucion_analitica_id
                    where date_from = '%s'
                    and date_to = '%s'
                    and hpl.code in (%s))t
                inner join hr_payslip hp on hp.id = t.payslip_id
                group by t.name_related,hp.employee_id,t.sequence,t.codigo
                order by 1,2
            $$,
                $$  select sr.sequence
                    from hr_salary_rule sr
                    where sr.appears_on_payslip='t'
                    and sr.code in (%s)
                    order by sr.sequence
                $$
            ) AS (
            %s
            );

        """ % (date_start, date_end,reglas_salariales_search, reglas_salariales_search,fields)
        # ELIMINAR CAMPO fields
        # print(query_pivot_table)
        self.env.cr.execute(query_pivot_table)
        data = self.env.cr.dictfetchall()
        for line in data:
            if self.env['hr.contract'].browse(line['x_contract_id']).regimen_laboral_empresa == 'practicante':
                result = 0
            else:
                rules = self.env['planilla.ajustes'].search([],limit=1).essalud_rules
                sub_days = self.env['planilla.ajustes'].search([],limit=1).cod_dias_subsidiados
                afecto,sub_total = 0,0
                for rule in rules:
                    word = "x_%s"%(rule.code)
                    if word in line:
                        if rule.category_id.code == 'DES_AFE':
                            afecto -= line[word] if line[word] else 0
                        else:
                            afecto += line[word] if line[word] else 0
                for sub_day in sub_days:
                    word = "x_%s"%(sub_day.codigo)
                    if word in line:
                        sub_total += line[word] if line[word] else 0
                if sub_total > 0:
                    result = afecto * 0.09
                else:
                    if afecto >= 930.0:
                        result = afecto * 0.09
                    if afecto < 930:
                        result = 930 * 0.09
                    if afecto == 0:
                        result = 0
            self.env['hr.payslip'].browse(line['x_payslip_id']).write({'essalud':result})



        # insertando nuevos registros
        for reg in data:
            self.env['planilla.tabular'].create(reg)


