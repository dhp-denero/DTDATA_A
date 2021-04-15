from odoo import fields, models , api
class Contratos(models.Model):
    _inherit         = 'hr.contract'
    is_life_essalud  = fields.Boolean()
