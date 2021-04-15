from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime
from odoo.exceptions import UserError


class DistribucionAnalitica(models.Model):

    _name="planilla.distribucion.analitica"
    _rec_name='codigo'
    
    codigo=fields.Char("Codigo",required="1")
    descripcion=fields.Text("Descripcion")
    cuenta_analitica_lines = fields.One2many("planilla.distribucion.analitica.lines",'distribucion_analitica_id','cuenta_analitica_lines')
    
    @api.constrains('cuenta_analitica_lines')
    def constraint_porcentaje(self):
        porcentaje_total=sum([x.porcentaje for x in self.cuenta_analitica_lines])
        if porcentaje_total != 100.0:
            raise UserError('Los porcentajes Deben Sumar 100')


class DistribucionAnaliticaLine(models.Model):

    _name="planilla.distribucion.analitica.lines"

    distribucion_analitica_id = fields.Many2one('planilla.distribucion.analitica')
    cuenta_analitica_id = fields.Many2one("account.analytic.account",string="Cuenta Analitica",required="1")
    porcentaje=fields.Float("Porcentaje",required="1")
