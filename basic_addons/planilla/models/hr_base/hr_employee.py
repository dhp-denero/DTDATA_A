# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from dateutil import relativedelta

import babel

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _rec_name = 'store_name'

    tablas_tipo_documento_id = fields.Many2one('planilla.tipo.documento', 'Tipo Documento')
    identification_id = fields.Char(string='Identification No', groups='hr.group_hr_user',required=True)
    
    condicion = fields.Selection([
        ('domiciliado', 'Domiciliado'),
        ('nodomiciliado', 'No Domiciliado'),
    ], string='Condicion', required=True, default='domiciliado', help="Domiciliado o No Domiciliado")

    a_paterno = fields.Char('Apellido Paterno')
    a_materno = fields.Char('Apellido Materno')
    nombres = fields.Char('Nombres')


    bank_account_cts_id = fields.Many2one('res.partner.bank', string='Cuenta CTS',
        domain="[('partner_id', '=', address_home_id)]", help='Cuenta CTS', groups='hr.group_hr_user')


    bacts_acc_number_rel = fields.Char(string=u"Número de cuenta",related='bank_account_cts_id.acc_number')
    bacts_bank_id_rel = fields.Many2one(
        'res.bank', string="Banco",related='bank_account_cts_id.bank_id')
    bacts_currency_id_rel = fields.Many2one(
        'res.currency', string="Moneda",related='bank_account_cts_id.currency_id')

    bank_account_id_acc_number_rel = fields.Char(string=u"Número de cuenta", related='bank_account_id.acc_number')
    bank_account_id_bank_id_rel = fields.Many2one(
        'res.bank',string="Banco", related='bank_account_id.bank_id')
    bank_account_id_currency_id_rel = fields.Many2one(
        'res.currency',string="Moneda", related='bank_account_id.currency_id')

    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced'),
        ('conviviente','Conviviente')
    ], string='Marital Status', groups='hr.group_hr_user')

    personal_email = fields.Char("Correo Personal")
    emergency_contact = fields.Char("Contacto de Emergencia")
    men = fields.Integer("Varones")
    women = fields.Integer("Mujeres")
    ultima_vacacion_id = fields.Many2one('hr.ultima.vacacion')
    fecha_vacacion = fields.Date()
    rol_lines = fields.One2many('hr.rol.vacaciones.line','employee_id')
    direccion = fields.Char('Direccion')

    @api.multi
    def name_get(self):
        result = []
        for employee in self:
            name = "%s %s %s"%(employee.nombres,employee.a_paterno,employee.a_materno)
            result.append([employee.id,name])
        return result

    @api.depends('a_paterno','a_materno','nombres')
    def _get_name(self):
        for i in self:
            i.store_name = "%s %s %s"%(i.a_paterno or '',i.a_materno or '',i.nombres or '')
    store_name = fields.Char(compute=_get_name,store=True)
    
    @api.onchange('a_paterno','a_materno','nombres')
    def onchange_name_last_fp(self):
        self.name = ( (self.a_paterno if self.a_paterno else '') + " " + (self.a_materno if self.a_materno else '' ) + " " + (self.nombres if self.nombres else '' ) ).strip()

    @api.multi
    def get_wizard(self):
        return self.env['hr.ultima.vacacion'].get_wizard(self.ids)
    
    @api.multi
    def drop_contracts(self):
        for employee in self.ids:
            contracts = self.env['hr.employee'].browse(employee).contract_ids
            if len(contracts) > 0:
                for contract in contracts:
                    contract.write({'situacion_id':self.env['planilla.situacion'].search([('codigo','=','0')],limit=1).id,
                                    'flag':True})
        return self.env['planilla.warning'].info(title='Resultado', message="Se cambio la situacion de todos los contratos de los empleados seleccionados a la situacion 'BAJA'")
    
    @api.multi
    def refresh_employee_name(self):
        for employee in self.ids:
            emp = self.env['hr.employee'].browse(employee)
            emp.store_name = "%s %s %s"%(emp.a_paterno or '',emp.a_materno or '',emp.nombres or '')

    @api.multi
    def crear_contratos(self):
        employees = self.env['hr.employee'].search([])
        for employee in employees:
            if len(employee.contract_ids) < 1:
                self.env['hr.contract'].create({'employee_id':employee.id,
                            'afiliacion_id':7,
                            'date_start':'2019-02-01',
                            'date_end':'',
                            'department_id':14,
                            'distribucion_analitica_id':6,
                            'name':'Contrato '+str(employee.id),
                            'situacion_id':5,
                            'tipo_trabajador_id':7,
                            'type_id':1,
                            'wage':900})
    @api.model
    def create(self,vals):
        if 'identification_id' in vals:
            employees = self.env['hr.employee'].search([])
            for employee in employees:
                if vals['identification_id'].strip() == employee.identification_id:
                    raise UserError('No se puede generar dos empleados con el mismo DNI')
        return super(HrEmployee,self).create(vals)
    
    @api.multi
    def write(self,vals):
        if 'identification_id' in vals:
            employee = self.env['hr.employee'].search([('id','!=',self.id),('identification_id','=',vals['identification_id'].strip())])
            if len(employee) > 0:
                raise UserError('No pueden existir dos empleados con el mismo DNI')
        return super(HrEmployee,self).write(vals)