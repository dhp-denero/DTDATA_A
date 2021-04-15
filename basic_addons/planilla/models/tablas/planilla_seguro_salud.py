from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime
from odoo.exceptions import UserError

class PlanillaSeguroSalud(models.Model):

    _name="planilla.seguro.salud"
    _rec_name ="seguro"

    seguro =fields.Char("Seguro",help="Nombre del seguro Ejm: EsSalud",required=True)
    porcentaje = fields.Float('% ', digits=(12, 2),help="Porcentaje para aplicar en el seguro del contrato del empleado",default=0.0,required=True)