# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError
from datetime import datetime

class hr_contract(models.Model):

    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    afiliacion_id = fields.Many2one(
        'planilla.afiliacion', 'AFP', required=True)
    distribucion_analitica_id = fields.Many2one(
        'planilla.distribucion.analitica', string='Distribucion Gastos', required=True)

    cuspp = fields.Char("CUSPP")

    tipo_comision = fields.Selection(
        string=u'Tipo de Comision',
        selection=[(1, 'Flujo'), (2, 'Mixta')]
    )
    suspension_laboral = fields.One2many('hr.labor.suspension','suspension_id')
    situacion_id = fields.Many2one('planilla.situacion', string="Situacion", required=True)
    hourly_worker = fields.Boolean(string="Trabajador por Horas",default=False)
    tipo_trabajador_id = fields.Many2one(
        'planilla.tipo.trabajador', string="Tipo trabajador", required=True)

    otros_5ta_categoria = fields.Char(
        "Otros empleadores por Rentas de 5ta categorías")

    remuneracion_mensual_proyectada = fields.Float(u'Remuneración Mensual Afecta Proyectada')
    gratificacion_fiesta_patria_proyectada = fields.Float(u'Gratificación por Fiestas Patrias Proyectada')
    gratificacion_navidad_proyectada = fields.Float(u'Gratificación por Navidad Proyectada')

    regimen_laboral = fields.Selection(
        string=u'Régimen Laboral',
        selection=[
            ('N', 'N'),
            ('C', 'C'),
            ('M', 'M'),
            ('P', 'P')
        ],
        help="""
            N - Dependiente Normal\n
            C - Dependiente Construccion\n
            M - Dependiente Mineria\n
            P - Dependiente Pesqueria        
        """,
        default='N'
    )
    regimen_laboral_empresa = fields.Selection([
        ('regimengeneral', 'Regimen General'),
        ('pequenhaempresa', u'Pequeña empresa'),
        ('microempresa', 'Micro empresa'),
        ('practicante','Practicante')
    ], string='Regimen Laboral Empresa', help="Tipo de empresa",default="regimengeneral",required=True)


    excepcion_aportador = fields.Selection(
        string=u'Excepcion Aportador',
        selection=[
            ('L', 'L'),
            ('U', 'U'),
            ('J', 'J'),
            ('I', 'I'),
            ('P', 'P'),
            ('O', 'O')
        ],
        help="""L - No corresponde aportar debido a LICENCIA sin renumeracion \n
             U - No corresponde aportar porque existe un subsidio pagado directamente por essalud y en el mes no hubo remuneracion pagada por el empleador \n
             J - No corresponde aportar porque el trabajador se encuentra jubilado \n
             I - No corresponde aportar porque el trabajador pensionado por invalidez en el mes \n
             P - No corresponde aportar debido a que la relacion laboral se iicio en el mes despues del cierre de planillas , el aporte del mes se incluira en el mes siguiente  \n
             O - No corresponde aportar debido a otro motivo , no hubo remuneracion en el mes
        """
    )
# deprecado 09/11/2018
    # tipo_seguro = fields.Selection(
    #     string=u'Tipo Seguro',
    #     selection=[
    #         ('essalud', 'EsSalud'),
    #         ('eps', 'EPS'),
    #     ],
    #     help="""
    #     """,
    #     default='essalud',
    #     required=True
    # )
    seguro_salud_id = fields.Many2one('planilla.seguro.salud', 'Seguro de salud',ondelete='set null')
    fecha_record = fields.Date()
    jornada = fields.Selection([
        ('one','1 dia a la semana'),
        ('two','2 dias a la semana'),
        ('three','3 dias a la semana'),
        ('four','4 dias a la semana'),
        ('five','5 dias a la semana'),
        ('six','6 dias a la semana'),
        ],'Jornada Laboral',default='six')
    sctr = fields.Many2one('planilla.sctr','SCTR')

    def get_first_contract(self, employee, last_contract=False):
        domain = [('employee_id', '=', employee.id), ('date_start', '<=', last_contract.date_start)] if last_contract else [('employee_id', '=', employee.id)]
        Contracts = self.search(domain, order='date_start desc')
        aux, roll_back = None, None
        delimiter = len(Contracts)
        if delimiter > 1:
            for c, Contract in enumerate(Contracts):
                if Contract.situacion_id.codigo == '0' and c == 0:
                    aux = [Contract, c]
                    continue
                if Contract.situacion_id.codigo == '0' and aux and c - aux[1] == 1:
                    return aux[0]
                if Contract.situacion_id.codigo == '0' and aux and not c - aux[1] == 1:
                    return roll_back
                if Contract.situacion_id.codigo == '0' and not aux:
                    return roll_back
                if Contract.situacion_id.codigo != '0' and delimiter - 1 == c:
                    return Contract
                roll_back = Contract
        else:
            return Contracts

    @api.model
    def exist_contract(self, employee, date_from, date_to):

        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to),
                    ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to),
                    ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|',
                    ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee), '|',
                        '|'] + clause_1 + clause_2 + clause_3
        dat = self.env['hr.contract'].search(clause_final)
        return dat

    @api.model
    def exist_contract_with_id(self, employee, date_from, date_to, id):
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to),
                    ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to),
                    ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|',
                    ('date_end', '=', False), ('date_end', '>=', date_to)]

        clause_final = [('employee_id', '=', employee), ('id',
                                                         '!=', id), '|', '|'] + clause_1 + clause_2 + clause_3
        dat = self.env['hr.contract'].search(clause_final)
        return dat

    @api.multi
    def write(self, vals):
        if 'flag' not in vals:
            date_start = vals['date_start'] if 'date_start' in vals else self.date_start
            date_end = vals['date_end'] if 'date_end' in vals else self.date_end
            employee_id = vals['employee_id'] if 'employee_id' in vals else self.employee_id.id

            num_row = self.search([('employee_id','=',employee_id), ('id', '!=', self.id),('state','=','draft')])

            if len(num_row)>0:
                raise ValidationError('Ya existe un contrato con estado Nuevo para este empleado. Solo puede existir un contrato con estado Nuevo. Regularize y vuelva a intentar')


            if not date_end:


                dat = self.env['hr.contract'].search([('employee_id', '=', employee_id), ('id', '!=', self.id), 
                ('date_start', '>=', date_start),('date_end', '=', False)  ])

                if dat:
                    raise ValidationError(
                        _('La fecha del contrato se esta intersecando con otro rango de fechas del empleado (%s - %s)' % (dat.date_start, dat.date_end)))
                    return False

                dat = self.env['hr.contract'].search([('employee_id', '=', employee_id), ('id', '!=', self.id), 
                ('date_start', '<=', date_start),('date_end', '=', False)  ])

                if dat:
                    raise ValidationError(
                        _('Solo puede existir un solo contrato con fecha de fin en blanco. El empleado tiene un contrato con fechas de inicio %s pero no tiene fecha_fin %s' % (dat.date_start, dat.date_end)))
                    return False

                dat = self.env['hr.contract'].search([('employee_id', '=', employee_id), ('id', '!=', self.id), 
                ('date_start', '<=', date_start), ('date_end', '>=', date_start)])
                if dat:
                    raise ValidationError(
                        _('La fecha del contrato se esta intersecando con otro rango de fechas del empleado (%s - %s)' % (dat.date_start, dat.date_end)))
                    return False

            num_row = self.exist_contract_with_id(
                employee_id, date_start, date_end, self.id)

            if len(num_row) > 0:
                raise ValidationError(
                    _('La fecha del contrato se esta intersecando con otro rango de fechas del empleado (%s - %s)' % (num_row.date_start, num_row.date_end)))
                return False
            if 'department_id' in vals:
                self.employee_id.department_id=vals['department_id']
            return super(hr_contract, self).write(vals)
        else:
            del vals['flag']
            return super(hr_contract, self).write(vals)

    @api.model
    def create(self, vals):

        num_row = self.search([('employee_id','=',vals['employee_id']),('state','=','draft')])

        if len(num_row)>0:
            raise ValidationError('Ya existe un contrato con estado Nuevo para este empleado.Solo puede existir un contrato con estado Nuevo. Regularize y vuelva a intentar')

        num_row = self.exist_contract(
            vals['employee_id'], vals['date_start'], vals['date_end'])

        if len(num_row) > 0:
            raise ValidationError(
                _('El empleado ya tiene un contrato en las fechas %s %s ') % (vals['date_start'], vals['date_end']))
            return False
        t= super(hr_contract, self).create(vals)
        t.employee_id.department_id=vals['department_id']
        return t

    @api.multi
    def copy(self, default=None):
        default = dict(default or {})
        default.update({'date_start': '1000-01-01', 'date_end': ''})
        default_return_value = super(hr_contract, self).copy(default)
        return default_return_value

class hr_labor_suspension(models.Model):
    _name = 'hr.labor.suspension'

    suspension_id = fields.Many2one('hr.contract',readonly=True)
    tipo_suspension_id = fields.Many2one('planilla.tipo.suspension', string="Tipo suspension")
    motivo = fields.Char("Motivo")
    nro_dias = fields.Integer("N° dias")
    periodos = fields.Many2one('hr.payslip.run','Periodo')