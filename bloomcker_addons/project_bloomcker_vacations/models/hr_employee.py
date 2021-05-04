# -*- coding: utf-8 -*-
from odoo import models, fields, api

class EmployeeExt(models.Model):
    _inherit = 'hr.employee'

    name_total = fields.Char('Nombre Completo', compute='get_name_total')

    def get_name_total(self):
        self.name_total = self.nombres + ' ' + self.a_paterno + ' ' + self.a_materno
