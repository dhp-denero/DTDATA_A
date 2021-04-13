# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging


class ProjectExt(models.Model):
    _inherit = 'crm.lead'
    project_bl = fields.Many2one('project.project' ,'Proyecto Asociado')
    show_button_project = fields.Boolean(compute='_get_default_stage_project')

    def create_project_ext_bl(self):
        """Este metodo crea un proyecto enlasado a la oportunidad correpondiente"""
        usuarios = self.env['res.users'].search([])
        if not self.project_bl:
            registro = {
            'name':self.name,
            'company_id':self.company_id.id,
            'type': "account"
            }
            account_analytic = self.env['account.analytic.account'].create(registro)
            registro = {
                'name':self.name,
                'use_tasks':True,
                'allow_timesheets':True,
                'use_issues':True,
                'partner_id':self.partner_id.id,
                'analytic_account_id': account_analytic.id,
                'quotation_bl': self.planned_revenue
            }
            project = self.env['project.project'].create(registro)
            self.project_bl = project.id
            return project.id
        else:
            raise UserError(('Ya existe un proyecto asociado a esta oportunidad.'))

    @api.one
    def _get_default_stage_project(self):
        """Este metodo retorna un check para mostrar el boton de crear proyecto"""
        if self.env['crm.stage'].search([])[-1] == self.stage_id:
            self.show_button_project = True
        else:
            self.show_button_project = False