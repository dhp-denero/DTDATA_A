# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError,ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime, date, timedelta
import traceback
from lxml import etree
from StringIO import StringIO
import time

# esta tabla la uso para generar la planilla dinamicamente


class PlanillaPlanillaTabular(models.Model):

    _name = "planilla.tabular"


class PlanillaPlanillaTabularWizard(models.TransientModel):

    _name = "planilla.planilla.tabular.wizard"

    fecha_ini = fields.Date("Fecha inicio", required="1",
                            default=lambda self: self._default_fecha_ini())
    fecha_fin = fields.Date("Fecha fin", required="1",
                            default=lambda self: self._default_fecha_fin())

    @api.model
    def _default_fecha_ini(self):
        todayDate = date.today()
        return todayDate.replace(day=1)

    @api.model
    def _default_fecha_fin(self):
        return fields.Date.from_string(fields.Date.context_today(self))


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
                min(t.id) as id,
                min(t.payslip_id) as payslip_id,
                min(t.sequence) as sequence,
                sum(t.total) as total
                from (
                    select distinct
                    case when hc.regimen_laboral_empresa = 'practicante' then e.name_related ||' (practicante)' else e.name_related end,
                    e.identification_id,
                    pa.entidad,
                    hc.id,
                    hp.id as payslip_id,
                    hpl.sequence,
                    hpl.total
                    from hr_payslip hp
                    inner join hr_payslip_line hpl on hp.id=hpl.slip_id
                    inner join hr_employee e on e.id = hp.employee_id
                    inner join hr_contract hc on hc.id = hp.contract_id
                    inner join planilla_afiliacion pa on pa.id = hc.afiliacion_id
                    where date_from = '%s'
                    and date_to = '%s'
                    and hpl.code in (%s))t
                inner join hr_payslip hp on hp.id = t.payslip_id
                group by t.name_related,hp.employee_id,t.sequence
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


    @api.multi
    def do_rebuild(self):
        self.reconstruye_tabla(self.fecha_ini,self.fecha_fin)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'planilla.tabular',
            'view_type': 'form',
            'view_mode': 'tree',
            'target': 'current'
        }
