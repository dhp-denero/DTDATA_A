# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging


class ProjectExt(models.Model):
    _inherit = 'project.task'

    def _get_project_id_domain(self):
        dominio = [(self.id, '=', self.id)]
        return [(self.id, '=', self.id)]

    def _get_means_bl(self):
        self.means_ext = self.project_id.means_ext
        print(self.means_ext)

    milestone_commercial = fields.Boolean(default=False)
    means_ext = fields.Many2many('res.users', string="Recursos", compute="_get_means_bl")
    # user_id = fields.Many2one('res.users', string='Assigned to', index=True, track_visibility='always', domain=lambda self: self._get_project_id_domain())