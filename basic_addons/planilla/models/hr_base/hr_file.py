# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)

class HrFile(models.Model):

    _name = 'hr.file'
    _description = 'File of worker data'

    #Datos Personales
    a_paterno = fields.Char('Apellido Paterno',required=True)
    a_materno = fields.Char('Apellido Materno',required=True)
    nombres = fields.Char('Nombres',required=True)
    sexo = fields.Selection([
            ('male','Hombre'),
            ('female','Mujer'),
            ('other','Otros')
        ],string='Sexo',required=True)
    fec_nac = fields.Date(string='Fecha de Nacimiento',required=True)
    pais = fields.Many2one('res.country','Pais',required=True)
    provincia = fields.Char('Provincia o Estado')
    distrito = fields.Char('Distrito')
    dni = fields.Many2one('planilla.tipo.documento', 'Tipo Documento',required=True)
    num_doc = fields.Char(u'N° de Documento',required=True)
    telefono = fields.Char(u'N° Telefono Domicilio')
    celular = fields.Char(u'N° Telefono Celular',required=True)
    correo = fields.Char('Correo Electronico Personal',required=True)
    carne_essalud = fields.Char(u'N° Carné de ESSALUD')
    grupo_sanguineo = fields.Char('Grupo Sanguineo')
    direccion = fields.Char('Domicilio Actual')
    referencia = fields.Char('Referencia')
    talla_camisa = fields.Char('Talla de Camisa')
    talla_pantalon = fields.Char('Talla de Pantalon')
    talla_polo = fields.Char('Talla de Polo')
    estado_civil = fields.Selection([
            ('single','Soltero(a)'),
            ('married','Casado(a)'),
            ('widower','Viudo(a)'),
            ('divorced','Divorciado'),
            ('conviviente','Conviviente')
        ],string='Estado Civil',required=True)
    nro_hijos = fields.Integer(u'N° de hijos',required=True)
    familiares = fields.One2many('hr.familiar','worker_id',string='Familiares')

    #Datos del conyuge "c = Conyuge"
    c_a_paterno = fields.Char('Apellido Paterno')
    c_a_materno = fields.Char('Apellido Materno')
    c_nombres = fields.Char('Nombres')
    c_fec_nac = fields.Char('Fecha de Nacimiento')
    c_trabajo = fields.Char('Lugar donde labora el Conyuge')
    c_dni = fields.Char('DNI/Carnet de Extranjeria/Pasaporte')

    #Datos de un responsable en caso de emergencia "e = Emergencia"
    e_ape_nom_1 = fields.Char('Apellidos y Nombres')
    e_parentesco_1 = fields.Char('Parentesco')
    e_direccion_1 = fields.Char('Direccion o Teléfono')
    e_ape_nom_2 = fields.Char('Apellidos y Nombres')
    e_parentesco_2 = fields.Char('Parentesco')
    e_direccion_2 = fields.Char('Direccion o Teléfono')

    #Informacion Laboral
    fec_ing = fields.Date(string='Fecha de Ingreso')
    cargo = fields.Char('Cargo a Desempeñar')
    horas = fields.Integer(u'N° de Horas Semanales de Trabajo')
    entidad_finan_sueldo = fields.Char('Nombre de Entidad Financiera')
    cta_sueldo = fields.Char(u'N° CTA. Sueldo')
    entidad_finan_cts = fields.Char('Nombre de Entidad Financiera')
    cta_cts = fields.Char('N° CTA. CTS')
    regimen = fields.Selection([
            ('onp','ONP'),
            ('afp_integra','AFP INTEGRA'),
            ('afp_profuturo','AFP PROFUTURO'),
            ('afp_prima','AFP PRIMA'),
            ('afp_habitat','AFP HABITAT'),
            ('sin_regimen','SIN REGIMEN')
        ],string='¿Cual es su regimen Pensionario?')
    cuspp_afp = fields.Char(u'N° (CUSPP-AFP)')
    fec_afiliacion = fields.Date(string='Fecha de Afiliación')

    estudios = fields.One2many('hr.estudios','e_worker_id',string='Estudios')
    idiomas = fields.One2many('hr.idiomas','i_worker_id',string='Idiomas')

class Familiar(models.Model):

    _name = 'hr.familiar'
    _description = 'Worker Familiars'

    ape_nom = fields.Char('Apellidos y Nombres')
    parentesco = fields.Char('Parentesco')
    fec_nac = fields.Date('Fecha de Nacimiento')
    ocupacion = fields.Char('Ocupacion')
    estado_civil = fields.Char('Estado Civil')
    vive = fields.Selection([('si','Si'),('no','No')],string='Vive',default='si')
    worker_id = fields.Many2one('hr.file', readonly=True)

class Estudios(models.Model):

    _name = 'hr.estudios'
    _description = 'Data of Studies'

    educacion = fields.Selection([
            ('primaria','Primaria'),
            ('secundaria','Secundaria'),
            ('instituto','Inst. Superior'),
            ('universitario','Universitaria'),
            ('maestria','Maestria'),
            ('doctorado','Doctorado')
        ],string='Educación',default='primaria')
    nom_carrera = fields.Char('Nombre de la Carrera Profesional o Especialidad')
    centro_estudios = fields.Char('Nombre del Centro de Estudios')
    anio_inicio = fields.Integer(u'Año de Inicio')
    anio_fin = fields.Integer(u'Año de Término')
    completa = fields.Selection([('completa','Completa'),('incompleta','Incompleta')],string='¿Completa o Incompleta?')
    grado = fields.Selection([
        ('titulado','TITULADO'),
        ('bachiller','BACHILLER'),
        ('egresado','EGRESADO'),
        ('estudiante','ESTUDIANTE')
        ],string='Grado Academico Obtenido')
    pais = fields.Char(string='Pais o Departamento de Centro de Estudios')
    e_worker_id = fields.Many2one('hr.file',readonly=True)

class Idiomas(models.Model):

    _name = 'hr.idiomas'
    _description = 'Knowledge of Idioms'

    nombre = fields.Char(string='Idioma')
    nivel = fields.Selection([
            ('basico','Basico'),
            ('intermedio','Intermedio'),
            ('avanzado','Avanzado'),
            ('materna','Lengua Materna')
        ],string='Nivel',default='basico')
    lugar = fields.Char(string='Centro de Estudio')
    certificacion = fields.Text(string='Defina (Nombre,Nivel,Fecha) de la certificacion')
    i_worker_id = fields.Many2one('hr.file',readonly=True)

class Wizard(models.Model):
    _name = 'hr.wizard'

    def _get_employees_default(self):
        return self.env['hr.employee'].search([])

    files = fields.Many2many('hr.file',string='Empleado')
    employees = fields.Many2many('hr.employee',default=_get_employees_default)
    name = fields.Char()

    @api.multi
    def export_employee(self):
        doc_list = []
        nro_doc_list = []
        for employee in self.employees:
            if employee.tablas_tipo_documento_id != False:
                doc_list.append(employee.tablas_tipo_documento_id)
                nro_doc_list.append(employee.identification_id)
        for record in self:
            if record.files:
                for cont,file in enumerate(record.files):
                    if not file.dni in doc_list or not file.num_doc in nro_doc_list:
                        vals = {
                            "name": (file.a_paterno + " " + file.a_materno + " " + file.nombres).strip(),
                            "condicion": "domiciliado",
                            "tablas_tipo_documento_id": file.dni[0].id,
                            "identification_id": file.num_doc,
                            "nombres": file.nombres,
                            "a_materno": file.a_materno,
                            "a_paterno": file.a_paterno,
                            "gender": file.sexo,
                            "birthday": file.fec_nac,
                            "country_id": file.pais[0].id,
                            "marital": file.estado_civil,
                            "children": file.nro_hijos
                        }
                        self.env['hr.employee'].create(vals)
                
 

