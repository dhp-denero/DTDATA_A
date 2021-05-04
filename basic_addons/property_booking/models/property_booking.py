# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
from odoo import _, api, fields, models
from odoo.exceptions import Warning
from odoo.tools import misc


class PropertyCreation(models.Model):
    _name = "property.created"

    @api.one
    @api.depends('asset_id.child_ids')
    def calc_total_tower(self):
        """
        This Method is used to calculate total Tower
        """
        total = 0
        if self.child_ids:
            total = len(self.child_ids.ids)
        self.total_prop_tower = total

    @api.multi
    @api.depends('asset_id.image')
    def _has_image(self):
        for rec in self:
            rec.has_image = bool(rec.image)

    tower_num = fields.Char(
        string='Tower no')
    floor_number = fields.Char(
        string='Floor no')
    asset_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='asset',
        delegate=True,
        required=True,
        ondelete='cascade')
    prefix3 = fields.Selection(
        [('1', 'ABCD'), ('2', '101'),
         ('3', '1001'), ('4', '10001')],
        string='Prefix For Property',
        default='2',
        help='Prefix Or Label For Property.')
    is_sub_property = fields.Boolean(
        string='Sub Property',
        help='Select If your property Is Sub Property.')
    change_lable = fields.Boolean(
        string='Change Label',
        help='Select If you wan\'t to change label.')
    prop_number = fields.Char(
        string='property Number',
        help='property Number.')
    lable_bool = fields.Boolean(
        string='Label Boolean')
    parent_related = fields.Many2one(
        comodel_name='account.asset.asset',
        string='parent property',
        related='asset_id.parent_id',
        ondelete='restrict')
    parent_property_rel = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Parent Property',
        related='parent_related.parent_id',
        ondelete='restrict')
    total_prop_tower = fields.Float(
        compute='calc_total_tower',
        string='Total Tower',
        readonly=True)
    has_image = fields.Boolean(
        compute='_has_image')
    no_avl = fields.Integer(
        string='Available',
        compute='total_property_avl',
        store=True)

    @api.depends('child_ids', 'child_ids.state')
    def total_property_avl(self):
        """
        This method calculate total property available.
        @param self: The object pointer
        """
        for rec in self:
            no_avl = len([(avl_ids.state, avl_ids.id) for avl_ids in
                          rec.child_ids if avl_ids.state != 'book'])
            rec.update({'no_avl': no_avl})
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.multi
    def create_property(self):
        """
        This method create sub properties.
        """
        create_obj = self.env['property.created']
        tower_list = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for property_rec in self:
            if property_rec.is_sub_property and \
                    property_rec.no_of_property == 0 or \
                    property_rec.floor == 0:
                raise Warning(_('Property per floor and number of property\
                 should not be Zero!'))
            values = {'value': property_rec.value,
                      'category_id': property_rec.category_id.id,
                      'furnished': property_rec.furnished,
                      'type_id': property_rec.type_id.id,
                      'parent_id': property_rec.asset_id.id,
                      'ground_rent': property_rec.ground_rent,
                      'floor': property_rec.floor,
                      'no_of_property': property_rec.no_of_property,
                      'state': 'draft',
                      'color': 4,
                      'lable_bool': True,
                      'is_sub_property': True,
                      'street': property_rec.street,
                      'street2': property_rec.street2,
                      'township': property_rec.township,
                      'city': property_rec.city,
                      'state_id': property_rec.state_id.id,
                      'country_id': property_rec.country_id.id,
                      'zip': property_rec.zip,
                      'image': property_rec.image,
                      'property_manager': property_rec.property_manager.id,
                      }
            if property_rec.prefix3 != '1':
                for floor_rec in range(1, int(property_rec.floor) + 1):
                    for pro_rec in range(1, int(property_rec.no_of_property)
                                         + 1):
                        pre3 = str("%." + str(property_rec.prefix3) + "d")
                        values.update({
                            'name': property_rec.name + "-" + str(floor_rec) +
                            str(pre3 % pro_rec),
                            'tower_num': property_rec.name,
                            'prop_number': str(pre3 % pro_rec),
                            'floor_number': floor_rec,
                        })
                        create_obj.create(values)
                property_rec.write({'state': 'new_draft'})
            if property_rec.prefix3 == '1':
                for floor_rec in range(1, int(property_rec.floor) + 1):
                    counter = 0
                    for pro_rec in range(1, int(property_rec.no_of_property)
                                         + 1):
                        values.update({'floor_number': floor_rec})
                        if counter < len(tower_list):
                            values.update({
                                'name': property_rec.name + "-" +
                                str(floor_rec) +
                                tower_list[counter %
                                           len(tower_list)],
                                'tower_num': property_rec.name,
                                'prop_number': tower_list
                                [counter % len(tower_list)],
                            })
                        if counter >= len(tower_list):
                            values.update({
                                'name':
                                    property_rec.name + "-" + str(floor_rec) +
                                    tower_list[counter % len(tower_list)] +
                                    str(counter / 26),
                                'tower_num': property_rec.name,
                                'prop_number': tower_list
                                [counter % len(tower_list)] +
                                str(counter / 26),
                            })
                        create_obj.create(values)
                        counter += 1
                property_rec.write({'state': 'new_draft'})
        return True

    @api.onchange('parent_id')
    def parent_prop_change(self):
        """
        This Method is used to set parent address.
        @param self: The object pointer
        """
        if self.parent_id:
            parent_data = self.parent_id
            self.street = parent_data.street or False
            self.street2 = parent_data.street2 or False
            self.township = parent_data.township or False
            self.city = parent_data.city or False
            self.state_id = parent_data.state_id.id or False
            self.zip = parent_data.zip or False
            self.country_id = parent_data.country_id.id or False
            self.category_id = parent_data.category_id.id or False,
            self.type_id = parent_data.type_id.id or False,

    @api.multi
    def property_unlink(self):
        """
        This Method is used to delete child properties.
        @param self: The object pointer
        """
        for property_rec in self:
            if property_rec.child_ids.ids:
                property_rec.child_ids.unlink()
            property_rec.write({'state': 'draft'})
        return True

    @api.multi
    def unlink(self):
        asset_obj = self.env['account.asset.asset']
        for property_rec in self:
            if property_rec.child_ids and property_rec.child_ids.ids:
                acc_un_ids = asset_obj.search(
                    [('parent_id', 'in', property_rec.child_ids.ids)])
                property_rec.child_ids.unlink()
                acc_un_ids.unlink()
        return super(PropertyCreation, self).unlink()

    @api.multi
    def write(self, vals):
        """
        Overrides orm write method.
        @param self: The object pointer
        """
        rec = super(PropertyCreation, self).write(vals)
        for property_rec in self:
            if property_rec.child_ids and property_rec.child_ids.ids:
                values = {
                    'value': property_rec.value,
                    'category_id': property_rec.category_id.id,
                    'furnished': property_rec.furnished,
                    'ground_rent': property_rec.ground_rent,
                    'type_id': property_rec.type_id.id,
                }
                for asset_brw in property_rec.child_ids:
                    asset_brw.write(values)
        return rec

    @api.multi
    def edit_prop_wizzard(self):
        """
        This Method is used to open a wizard for edit properties.
        @param self: The object pointer
        """
        cr, uid, context = self.env.args
        context = dict(context)
        floor = []
        tower = []
        for res in self:
            property_id2 = res.asset_id.id
            prop_ids = self.search([('parent_id', '=', property_id2)])
            for rec in prop_ids:
                floor.append(str(rec.floor_number))
                tower.append(str(rec.tower_num))
            tower_list = list(set(tower))
            floor_list = list(set(floor))
            context.update(
                {'result3': res.id,
                 'result2': tower_list,
                 'result1': floor_list})
            self.env.args = cr, uid, misc.frozendict(context)
            return {'name': ('Filter Wizard'),
                    'res_model': 'property.wizzard',
                    'type': 'ir.actions.act_window',
                    'view_id': False,
                    'view_mode': 'form',
                    'view_type': 'form',
                    'target': 'new',
                    'context': {'default_property_id': context.get('result3'),
                                'default_floor_count': context.get('result1'),
                                'default_newtower': context.get('result2')},
                    'nodestroy': True,
                    }

    @api.multi
    def split_property(self):
        """
        This Method is used to open a wizard for split properties.
        @param self: The object pointer
        """
        for rec in self:
            if rec.state == 'cancel':
                prop_name = rec.name
                proplist = prop_name.split('->Merge->')
                if len(proplist) > 1:
                    rec.write(
                        {
                            'state': 'draft',
                            'property_manager': False,
                            'name': str(proplist[0])
                        })
                    uncheck_ids = self.search(
                        [('name', '=', _(str(proplist[1])))])
                    if uncheck_ids:
                        for cur_id in uncheck_ids:
                            newlabel = int(
                                cur_id.label_id.name) - int(rec.label_id.name)
                            cur_id.write({'label_id': newlabel})
                else:
                    raise Warning(_('Please select Property which \
                                    are Merged!'))
        return True

    @api.multi
    def merge_prop_wizzard(self):
        """
        This Method is used to open a wizard for merge properties.
        @param self: The object pointer
        """
        cr, uid, context = self.env.args
        context = dict(context)
        if context is None:
            context = {}
        for rec in self:
            context.update({'current_prop': rec.id})
            self.env.args = cr, uid, misc.frozendict(context)
            return {'name': ('Merge Property'),
                    'res_model': 'property.parent.merge.wizard',
                    'type': 'ir.actions.act_window',
                    'view_id': False,
                    'view_mode': 'form',
                    'view_type': 'form',
                    'target': 'new',
                    'context': {
                'default_new_prop_id': context.get('current_prop')
            },
                'nodestroy': True,
            }


class PropertyLabel(models.Model):
    _name = "property.label"

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        """
        Added name_get for purpose of displaying name with code number.
        @param self: The object pointer
        """
        res = []
        for rec in self:
            rec_str = ''
            if rec.name:
                rec_str += rec.name
            if rec.code:
                rec_str += rec.code
            res.append((rec.id, rec_str))
        return res

    @api.model
    def name_search(self, name='', args=[], operator='ilike', limit=100):
        """
        Added name_search for purpose to search by name and code
        @param self: The object pointer.
        """
        args += ['|', ('name', operator, name), ('code', operator, name)]
        cuur_ids = self.search(args, limit=limit)
        return cuur_ids.name_get()

    name = fields.Char(
        string='Number of BHK',
        help='Number of BHK')
    code = fields.Char(string='Code',
                       default='BHK',
                       help='Code For BHK')


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    @api.multi
    @api.depends('state')
    def _total_property_available(self):
        """
        This Method is used to calculate total available Properties.
        @param self: The object pointer.
        """
        for property_brw in self:
            tot = self.search_count(
                [('parent_id', '=', property_brw.id), ('state', '=', 'draft')])
            property_brw.Avalbl_property = tot

    @api.multi
    @api.depends('state')
    def _total_property_booked(self):
        """
        This Method is used to used to calculate total Booked Properties.
        @param self: The object pointer.
        """
        for property_brw in self:
            tot = 0.0
            booked_ids = self.search(
                [('parent_id', '=', property_brw.id), ('state', '=', 'book')])
            if booked_ids.ids:
                tot = len(booked_ids.ids)
            property_brw.book_property = tot

    label_id = fields.Many2one(
        comodel_name='property.label',
        string='Label Name',
        help='Name Of Label For Ex. 1-BHK , 2-BHK etc.')
    Avalbl_property = fields.Float(
        string='Available',
        compute='_total_property_available',
        method=True,
        help='It shows how many properties are available')
    book_property = fields.Float(
        compute='_total_property_booked',
        string='Book',
        method=True,
        help='It shows how many properties are booked')
    new_child_ids = fields.One2many(
        comodel_name='account.asset.asset',
        inverse_name='parent_id',
        string='Children Assets')
