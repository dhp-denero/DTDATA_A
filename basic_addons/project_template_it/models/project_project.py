# coding=utf-8
from odoo import fields, models, api


class ProjectProject(models.Model):
    _inherit = 'project.project'

    template_id = fields.Many2one('project.template', u'Plantilla de proyecto')

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        ret = super(ProjectProject, self).create(vals)
        if ret and ret.id and ret.template_id:
            self.init_from_template(ret)
        return ret

    def init_from_template(self, project):
        stage_obj = self.env['project.task.type']
        task_obj = self.env['project.task']
        template_line_ids = project.template_id.template_line_ids
        template_stage_ids = template_line_ids.mapped('stage_id')

        # stages = [(s.id,
        #            stage_obj.create(dict(
        #                name=s.name,
        #                projects=[(6, False, [project.id])]
        #            ))) for s in template_stage_ids]
        stages = [(s.id,
                   stage_obj.create(dict(
                       name=s.name
                   ))) for s in template_stage_ids]

        project.write(dict(
            type_ids=[(6, False, [stage.id for _, stage in stages])]
        ))
        for (index, stage) in stages:
            lines_by_stage = template_line_ids.filtered(lambda l: l.stage_id.id == index)

            for line in lines_by_stage:
                if line.task_id:
                    task = line.task_id
                    task_vals = dict(
                        stage_id=stage.id,
                        name=task.name,
                        sequence=line.sequence,
                        project_id=project.id,
                        planned_hours=line.planned_hours)
                    task_obj.create(task_vals)
