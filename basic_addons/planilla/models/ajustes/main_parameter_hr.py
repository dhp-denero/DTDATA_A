from odoo import models, fields, api

class MainParameterHr(models.Model):
    _name = "main.parameter.hr"

    dir_create_file = fields.Char(string='Directorio de Descargas')

    @api.model
    def create(self, vals):
        if len(self.env['main.parameter.hr'].search([])) >= 1:
            raise ValidationError("Solo puede existir un registro a la vez")
        else:
            return super(MainParameterHr,self).create(vals)