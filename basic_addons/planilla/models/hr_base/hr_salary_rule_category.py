import time
from datetime import datetime, timedelta
from dateutil import relativedelta

import babel

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval


class HrSalaryRuleCategory(models.Model):
    _inherit = 'hr.salary.rule.category'
    _order = 'secuencia'

    secuencia = fields.Integer(required=False, default=10)
    aparece_en_nomina = fields.Boolean(string='Aparece en nomina',
                                       help="Si esta checado significa que la categoria aparecera en los reportes", default=True, required=False)
    is_ing_or_desc = fields.Selection([
        ('ingreso', 'Ingreso'),
        ('descuento', 'Descuento'),
    ], string='Ingreso o descuento', required=False, default='descuento', help="Decide donde posicionar la columna en el reporte")
