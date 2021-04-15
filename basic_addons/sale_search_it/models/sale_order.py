# coding=utf-8
import logging
import pytz
from datetime import datetime
import odoo.addons.decimal_precision as dp

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

SEARCH_TIPO = (
    ('categoria', u'Por categoría'),
    ('codigo', u'Por código'),
    ('descripcion', u'Descripción'),
)

class OrderLineI(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('price_unit')
    def onchange_price_unit(self):
        if(self.price_unit < self.product_id.product_tmpl_id.standard_price):
            return {
                'value':{'price_unit':self._origin.price_unit},
                'warning': {'title': "Warning", 'message': "No puedes poner un precio unitario MENOR al costo"},
            }
            
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    search_codigo = fields.Char(u'Código')
    search_box = fields.Char(u'Buscar')
    search_categ_id = fields.Many2one('product.category', u'Categoría')
    search_tipo = fields.Selection(SEARCH_TIPO, u'Opciones', default='descripcion')
    search_line_ids = fields.One2many('sale.search.line', 'order_id')
    search_completa = fields.Boolean(u'Búsqueda completa', default=False)
    search_barras = fields.Char(u'Código de Barras')
    @api.onchange('search_barras')
    def _onchange_search_barras(self):
        self.search_line_ids = [(6, 0, [])] 
        if(self.search_barras is not False):
            product_ids = self.env['product.product'].search([('barcode','=',self.search_barras)])
            if product_ids.exists():
                self.search_barras = False
                self._generar_lineas_busqueda(product_ids)

            
    @api.multi
    @api.onchange('search_codigo','search_box','search_categ_id')
    def buscar(self):
        self.search_line_ids = [(6, 0, [])]# 6 reeemplazar, o default, [] con nada, solo para grillas
        if(self.search_codigo is False and self.search_box is False and self.search_categ_id.id is False):
            return 
        busqueda = self.search_box and self.search_box.strip() or False #strip borra los espacio en blanco solo inicio y final
        condicion = []
        conteo = 0
        if self.search_codigo and self.search_codigo.strip():
            if not self.search_completa:
                condicion = condicion + ['|', ('default_code', '=', self.search_codigo),
                                         ('barcode', '=', self.search_codigo)]
            else:
                condicion = condicion + ['|', ('default_code', '=ilike', '%{}%'.format(self.search_codigo or '---')),
                                         ('barcode', '=ilike', '%{}%'.format(self.search_codigo.strip() or '---'))]
            conteo += 1

        if self.search_categ_id:
            if not busqueda:
                raise ValidationError(u'Para la búsqueda por categoría debe escribir en la caja de descripción')
            condicion = condicion + [('categ_id', '=', self.search_categ_id.id)]
            conteo += 1

        if busqueda:
            condicion = condicion + [('name', '=ilike', '{}{}%'.format(self.search_completa and '%' or '', busqueda))]
            conteo += 1

        if conteo > 1:
            condicion = ['&' for i in range(conteo - 1)] + condicion

        product_ids = self.env['product.product'].search(condicion)
        if product_ids.exists():
            self._generar_lineas_busqueda(product_ids)


    @api.multi
    def _generar_lineas_busqueda(self, product_ids):
        ids = product_ids.ids
        saldo = self.get_saldo()

        lineas = [(0, False, {
            'product_id': product.id,
            'product_qty': 0,

        }) for product in product_ids]
        self.search_line_ids = lineas
        self._actualizar_lineas_busqueda()

    @api.multi
    def _actualizar_lineas_busqueda(self):
        for line in self.search_line_ids:
            line.pricelist_id = self.pricelist_id
            line.onchange_pricelist_id()

    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self):
        self._actualizar_lineas_busqueda()

    @api.multi
    def agregar_lineas_compra(self):
        seq = 10
        order_lines = []
        if self.search_line_ids:
            for line in self.search_line_ids:
                line.onchange_product_qty()
                if line and line.product_qty > 0:
                    data = {
                        u'qty_delivered': 0,
                        u'product_id': line.product_id.id,
                        u'product_uom': line.product_id.uom_id.id,
                        u'sequence': seq,
                        u'product_uom_qty': line.product_qty,
                        u'name': line.product_id.name,
                        u'price_unit': line.price_unit,
                        u'order_id': self.id,
                    }
                    t = self.env['sale.order.line'].create(data)
                    t.price_unit = line.price_unit
                    order_lines.append(t.id)
                seq = seq + 10
        if order_lines:
            self.search_line_ids = [(6, 0, [])]
            self.search_codigo = False
            self.search_box = False
            self.search_categ_id = False
            self.search_tipo = False
            self.search_completa = False
        else:
            raise ValidationError(_('No hay productos para agregar'))

    @api.multi
    def saldo_search(self, product_ids):
        # self.rebuild_kardex()
        self.env['detalle.simple.fisico.total.d'].search([('producto', 'in', product_ids)])

    @api.multi
    def rebuild_kardex(self):
        year = datetime.utcnow().year
        fiscal_year = self.env['account.fiscalyear'].search([('name', '=', str(year))])
        saldos = self.env['detalle.simple.fisico.total.d.wizard'].create({'fiscalyear_id': fiscal_year.id})
        saldos.do_rebuild()


class SaleOrderSearchLine(models.TransientModel):
    _name = 'sale.search.line'

    order_id = fields.Many2one('sale.order' )
    product_id = fields.Many2one('product.product', u'Producto')
    product_code = fields.Char(u'Código', related='product_id.default_code')
    uom_id = fields.Many2one('product.uom', related='product_id.uom_id')
    pricelist_id = fields.Many2one('product.pricelist')
    pricelist_currency = fields.Many2one('res.currency', related='pricelist_id.currency_id', string='Moneda')
    price_unit = fields.Float('Precio unit.', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    product_min_qty = fields.Float(string='Cantidad min.')
    product_qty = fields.Float(string='Cantidad', digits=dp.get_precision('Product Unit of Measure'), required=True,
                               default=1.0)
    product_hand_qty = fields.Float(string='Cantidad a mano', digits=dp.get_precision('Product Unit of Measure'),
                                    default=1.0, compute='_compute_cantidad_mano')
    
    check_docena = fields.Boolean('Precio x Volumen') #creacion del nuevo campo

    @api.model
    def create(self,vals):
        t = super(SaleOrderSearchLine,self).create(vals)
        t.onchange_product_qty()
        return t

        
    @api.one
    def write(self,vals):
        t = super(SaleOrderSearchLine,self).write(vals)
        if 'detener' in self.env.context:
            pass
        else:
            dominio=self.pricelist_id.item_ids.filtered(lambda r : r.product_tmpl_id.id == self.product_id.product_tmpl_id.id).sorted(key= lambda t: t.min_quantity)
            if self.check_docena == True:
                ultimo = dominio[-1]
                self.with_context({'detener':1}).write({'price_unit':ultimo.fixed_price,'product_min_qty':ultimo.min_quantity})
            else:
                for x in dominio: #domnio ya esta ordenado, el mayor precio es el primero y el menor esta al ultimo
                    if(self.product_qty >= x.min_quantity):
                        self.with_context({'detener':1}).write({'price_unit':x.fixed_price,'product_min_qty':x.min_quantity})
        return t



    @api.onchange('product_qty','check_docena')
    def onchange_product_qty(self):
        dominio=self.pricelist_id.item_ids.filtered(lambda r : r.product_tmpl_id.id == self.product_id.product_tmpl_id.id).sorted(key= lambda t: t.min_quantity)
        if self.check_docena == True:
            ultimo = dominio[-1]
            self.price_unit = ultimo.fixed_price
            self.product_min_qty = ultimo.min_quantity
        else:
            for x in dominio: #domnio ya esta ordenado, el mayor precio es el primero y el menor esta al ultimo
                if(self.product_qty >= x.min_quantity):
                    self.price_unit = x.fixed_price
                    self.product_min_qty = x.min_quantity
                
    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self):
        price_unit = False
        product_min_qty = False
        if self.product_id and self.pricelist_id:
            filtro = self.pricelist_id.item_ids.filtered(lambda i:
                                                         i.product_id.id == self.product_id.id or
                                                         i.product_tmpl_id.id == self.product_id.product_tmpl_id.id).sorted(key= lambda t: t.min_quantity)
            if filtro.exists():
                price_unit = filtro[0].fixed_price
                product_min_qty = filtro[0].min_quantity
        if not price_unit:
            price_unit = self.product_id.list_price
        self.price_unit = price_unit
        self.product_min_qty = product_min_qty

    @api.depends('order_id.warehouse_id')
    def _compute_cantidad_mano(self):
        for line in self:
            cantidad = False
            location_id = line.order_id.warehouse_id.lot_stock_id
            res = self.env['detalle.simple.fisico.total.d'].search(
                [('producto', '=', line.product_id.id), ('almacen', '=', location_id.id)])
            if res.exists():
                cantidad = sum(res.mapped('saldo'))
            line.product_hand_qty = cantidad

    # @api.depends('product_id', 'pricelist_id')
    # def _compute_pricelist(self):
    #     price_unit = False
    #     product_min_qty = False
    #     if self.product_id and self.pricelist_id:
    #
    #         filtro = self.pricelist_id.item_ids.filter(lambda i: i.product_id.id == self.product_id.id)
    #         if filtro:
    #             price_unit = filtro[0].fixed_price
    #     if not price_unit:
    #         price_unit = self.product_id.list_price
    #     self.price_unit = price_unit
    #     self.product_min_qty = product_min_qty
