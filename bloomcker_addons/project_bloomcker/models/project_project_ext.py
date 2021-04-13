# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging


class ProjectExt(models.Model):
    _inherit = 'project.project'

    means_ext = fields.Many2many('res.users', string="Recursos")
    quotation_bl = fields.Monetary(string='Cotización Inicial', readonly=True)