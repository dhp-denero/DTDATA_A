from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models


from datetime import datetime


class PlanillaInputsNomina(models.Model):
    _name = "planilla.inputs.nomina"
    _rec_name="descripcion"
    _description = "contiene: descuentos,5ta categoria,vacaciones,gratificaciones,compensacion por tiempos de servicio,etc"


    codigo=fields.Char("Codigo",required=True)
    descripcion=fields.Char("Descripcion")

