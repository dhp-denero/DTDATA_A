# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime


class PlanillaAfpNetXlsx(models.Model):
	_name = 'planilla.afp.net.xlsx'	
	_auto = False

	cuspp = fields.Char('Periodo')
	tipo_doc = fields.Char('Tipo documento')
	identification_id = fields.Char('Identificacion')
	nombres = fields.Char('ruc')
	a_paterno = fields.Char()
	a_materno = fields.Char()
	relacion_laboral = fields.Char('Empresa')
	inicio_relacion_laboral = fields.Char('Tipo Cuenta')
	cese_relacion_laboral = fields.Char('Cuenta')
	excepcion_aportador = fields.Char('Excepcion Aportador')
	remuneracion_asegurable = fields.Float('Remuneracion asegurable',digits=(12,2))
	aporte_fin_provisional = fields.Float('Aporte voluntario con fin provisional',digits=(12,2))
	aporte_sin_fin_provisional = fields.Float('Aporte voluntario sin fin provisional',digits=(12,2))
	aporte_voluntario_empleador = fields.Float('Aporte voluntario empleador',digits=(12,2))
	regimen_laboral = fields.Char('Regimen Laboral')
