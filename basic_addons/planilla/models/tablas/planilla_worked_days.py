from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime


class PlanillaWorkedDays(models.Model):
    _name = "planilla.worked.days"
    _rec_name = "descripcion"
    _description = "Dias trabajados para cargarse en la planilla"

    codigo = fields.Char("Codigo", required=True)
    descripcion = fields.Char("Descripcion")
    dias = fields.Integer("Dias")
    horas = fields.Integer("Horas")
    minutos = fields.Integer("Minutos")
    tasa_monto = fields.Integer("Tasa o Monto")
