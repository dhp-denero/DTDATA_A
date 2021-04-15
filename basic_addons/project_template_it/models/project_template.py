# coding=utf-8
from odoo import fields, models, api


class ProjectTemplate(models.Model):
    _name = 'project.template'

    name = fields.Char(u'Nombre de plantilla')
    template_line_ids = fields.One2many('project.template.line', 'template_id', u'Detalle de plantilla')
    stage_ids = fields.One2many('project.template.stage', 'template_id', u'Etapas')


class ProjectTemplateLine(models.Model):
    _name = 'project.template.line'

    sequence = fields.Integer(u'Secuencia', default=0)
    template_id = fields.Many2one('project.template', u'Plantilla')
    stage_id = fields.Many2one('project.template.stage', u'Etapa', required=True)
    task_id = fields.Many2one('project.template.task', u'Tarea')
    planned_hours = fields.Float(u'Horas planificadas')


class ProjectTemplateStage(models.Model):
    _name = 'project.template.stage'

    template_id = fields.Many2one('project.template', u'Plantilla')
    name = fields.Char(u'Estapa')


class ProjectTemplateTask(models.Model):
    _name = 'project.template.task'

    template_id = fields.Many2one('project.template', u'Plantilla')
    name = fields.Char(u'Tarea')
