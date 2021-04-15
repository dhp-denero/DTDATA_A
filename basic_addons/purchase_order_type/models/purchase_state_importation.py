# -*- coding: utf-8 -*-
# Copyright 2015 Guewen Baconnier <guewen.baconnier@camptocamp.com>
# Copyright 2016 Vicent Cubells <vicent.cubells@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseStateImportation(models.Model):
    _name = 'purchase.state.importation'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
