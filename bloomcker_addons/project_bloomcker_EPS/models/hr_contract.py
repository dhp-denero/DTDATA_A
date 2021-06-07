# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging


class ContractsExt(models.Model):
    _inherit = 'hr.contract'

    plan_eps = fields.Char('Plan EPS')
