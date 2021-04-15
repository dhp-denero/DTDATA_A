# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2015-Today BrowseInfo (<http://www.browseinfo.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
import time
import tempfile
import binascii
import xlrd
import logging
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from openerp.exceptions import Warning
from openerp import models, fields, exceptions, api, _

_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    id_import = fields.Char('ID_ REFERENCIA')

class GenerateInvoices(models.TransientModel):
    _name = "generate.invoices"

    file = fields.Binary('File')
    import_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select', default='xls')
    invoice_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], string='Invoice Type',
                                    required=True)
    import_by = fields.Selection([('name', 'INV Name (Reference)')], string='Import By', readonly=True, default='name')
    journal_id = fields.Many2one('account.journal','Diario',required=True)
    link_example = fields.Text('Ejemplo Excel',default='/zad_import_invoice/static/description/odooxlsx.xlsx')

    @api.multi
    def create_invoices(self, values):
        invoice_obj = self.env['account.invoice']
        invoice_search = invoice_obj.search([
            ('id_import', '=', str(self.id) + values.get('invoice_name')),
            ('state','=','draft'),
        ])
        line_values = self.invoice_line_values(values)
        if invoice_search:
            if True:  #invoice_search.partner_id.name == values.get('partner') or invoice_search.partner_id.vat == values.get('partner'):
                if invoice_search.currency_id.name == values.get('moneda'):
                    invoice_search.write({
                        'invoice_line_ids': [(0, 0, line_values)],
                    })
                else:
                    raise Warning(_('Currency is different for "%s" .\n Please define same.') % values.get('moneda'))
            else:
                raise Warning(_('Customer name is different for "%s" .\n Please define same.') % values.get('partner'))
        else:
            partner_id = self.find_partner(values.get('partner'))
            currency_id = self.find_currency(values.get('moneda'))
            account = self.find_inv_account(values.get('moneda'))
            serie = self.find_serie(values.get('serie'))
            tipodoc = self.find_typedoc(values.get('tipodoc'))
            vals = {
                'id_import': str(self.id)+ values.get('invoice_name'),
                'name': values.get('glosa'),
                'type': 'out_invoice' if self.invoice_type == 'customer' else 'in_invoice',
                'account_id': account.id,
                'partner_id': partner_id.id,
                'currency_id': currency_id.id,
                'it_type_document':tipodoc.id,
                'serie_id':serie.id if serie else False,
                'reference':values.get('nrocomp'),
                'invoice_line_ids': [(0, 0, line_values)],
                'date_invoice':values.get('fechafac'),
                'journal_id':self.journal_id.id,
                'date':values.get('date'),
            }
            invoice_obj.create(vals)
        return True

    @api.multi
    def invoice_line_values(self, values):
        product_id = self.find_product(values)
        product_account = self.find_product_account(product_id)
        account = self.find_cuenta(values.get('cuenta'))
        impuesto = self.find_impuesto(values.get('impuesto'))
        analitica = self.find_analitica(values.get('ctaanal'))
        line_values = {
            'name': values.get('descrip'),
            'account_id': account and account.id or product_account.id,
            'price_unit': values.get('precio'),
            'quantity': values.get('cantidad'),
            'uom_id': product_id.uom_id and product_id.uom_id.id,
            'product_id': product_id.id,
            'invoice_line_tax_ids': [(6, 0, ([impuesto.id] if impuesto else []) )],
            'account_analytic_id': analitica and analitica.id,
        }
        return line_values

    @api.multi
    def find_impuesto(self,impuesto):
        if impuesto == '' or not impuesto:
            return False
        impuestox = self.env['account.tax'].search([('name','=',impuesto)])
        if len(impuestox) == 0:
            raise Warning('No existe el impuesto: ' + impuesto)
        return impuestox[0]

    @api.multi
    def find_analitica(self,anali):
        if anali == '' or not anali:
            return False
        a_id = self.env['account.analytic.account'].search([('name','=',anali)])
        if len(a_id) == 0:
            return self.env['account.analytic.account'].create( {'name': anali} )
        return a_id[0]

    @api.multi
    def find_serie(self,serie):
        if serie == '' or not serie:
            return False
        seriex = self.env['it.invoice.serie'].search([('name','=',serie)])
        if len(seriex) == 0:
            raise Warning('No existe la serie: ' + serie)
        return seriex[0]

    @api.multi
    def find_cuenta(self,cuenta):
        if cuenta == '' or not cuenta:
            return False
        cuentax = self.env['account.account'].search([('code','=',cuenta)])
        if len(cuentax) == 0:
            raise Warning('No existe la cuenta: ' + cuenta)
        return cuentax[0]

    @api.multi
    def find_typedoc(self,tipodoc):
        tipo = self.env['einvoice.catalog.01'].search([('code','=',tipodoc)])
        if len(tipo) == 0:
            raise Warning('No existe el tipo de documento: ' + tipodoc)
        return tipo[0]



    @api.multi
    def find_product(self, values):
        product_obj = self.env['product.product']
        product_search = product_obj.search(['&', '|',
                                             ('default_code', '=', values.get('producto')),
                                             ('name', '=', values.get('producto')),
                                             ('sale_ok' if self.invoice_type == 'customer' else 'purchase_ok', '=', 1)],
                                            limit=1)
        return product_search and product_search or product_obj.create({'name': values.get('producto'),'name': values.get('producto'),
                                                                        'sale_ok': self.invoice_type == 'customer',
                                                                        'purchase_ok': self.invoice_type != 'customer'})

    @api.multi
    def find_currency(self, name):
        currency_obj = self.env['res.currency']
        currency_search = currency_obj.search([('name', '=', name)])
        if currency_search:
            return currency_search
        else:
            raise Warning(_(' "%s" Currency are not available.') % name)

    @api.multi
    def find_partner(self, name):
        partner_obj = self.env['res.partner']
        partner_search = partner_obj.search([('nro_documento', '=', name), (self.invoice_type, '=', 1)])
        return partner_search and partner_search or partner_obj.create({'name': name,'nro_documento': name,
                                                                        'customer': self.invoice_type == 'customer',
                                                                        'supplier':  self.invoice_type != 'customer'})

    @api.multi
    def find_inv_account(self,moneda):
        if moneda == 'USD':
            if self.invoice_type == 'customer':
                return self.env['account.account'].search([('code','=','1212002')],limit=1)
            else:
                return self.env['account.account'].search([('code','=','4212002')],limit=1)
        else:
            if self.invoice_type == 'customer':
                return self.env['account.account'].search([('code','=','1212001')],limit=1)
            else:
                return self.env['account.account'].search([('code','=','4212001')],limit=1)

    @api.multi
    def find_product_account(self, product_id):
        account_obj = False
        account_id = False
        if self.invoice_type == 'customer':
            # Using Account Income for Customer invoice product lines
            if product_id.property_account_income_id:
                account_obj = product_id.property_account_income_id
            elif product_id.categ_id.property_account_income_categ_id:
                account_obj = product_id.categ_id.property_account_income_categ_id
            else:
                account_income = self.env['ir.property'].search([('name', '=', 'property_account_income_categ_id')])
                account_id = account_income.value_reference.split(",")[1]
        else:
            # Using Account expense for Customer Expense product lines
            if product_id.property_account_expense_id:
                account_obj = product_id.property_account_expense_id
            elif product_id.categ_id.property_account_expense_categ_id:
                account_obj = product_id.categ_id.property_account_expense_categ_id
            else:
                account_expense = self.env['ir.property'].search([('name', '=', 'property_account_expense_categ_id')])
                account_id = account_expense.value_reference.split(",")[1]
        return account_id and self.env['account.account'].browse(account_id) or account_obj

    @api.multi
    def import_invoices(self):
        """Load Inventory data from the CSV file."""
        values = {}
        keys = ['invoice_name', 'partner', 'tipodoc', 'serie', 'nrocomp', 'fechafac', 'moneda', 'producto', 'impuesto', 'descrip', 'cantidad', 'precio','ctaanal','glosa','cuenta','date']	
        if self.import_option == 'csv':
            data = base64.b64decode(self.file)
            file_input = cStringIO.StringIO(data)
            file_input.seek(0)
            reader_info = []
            reader = csv.reader(file_input, delimiter=',')
            # we done need the file header to be imported as data
            next(reader)
            try:
                reader_info.extend(reader)
            except Exception:
                raise exceptions.Warning(_("Not a valid file!"))
            for i in range(len(reader_info)):
                field = map(str, reader_info[i])
                values = dict(zip(keys, field))
                if values:
                    self.create_invoices(values)
        else:
            fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
            # we done need the file header to be imported as data so we start from range index 1
            for row_no in range(1, sheet.nrows):
                line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                        sheet.row(row_no)))
                values = dict(zip(keys, line))
                values.update(values)
                self.create_invoices(values)

