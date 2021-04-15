
from odoo import api, fields, models, _

class ResourceCalendar(models.Model):
    _name = 'resource.calendar'
    _inherit = 'resource.calendar'


    global_leave_ids = fields.One2many(
        'resource.calendar.leaves', 'calendar_id', 'Global Leaves',
        domain=[('resource_id', '=', False)]
        )


class ResourceAps(models.Model):
    _inherit = 'resource.resource'

    resource_task_ids = fields.One2many('project.task.resource.link', 'resource_id', 'Resources')
