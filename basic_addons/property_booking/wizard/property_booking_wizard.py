# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
from odoo import _, api, fields, models
from odoo.exceptions import Warning
from odoo.tools import misc


class PropertWizzard(models.TransientModel):
    _name = "property.wizzard"

    @api.model
    def get_floor(self):
        """
        This Method is used to show floors from active property.
        """
        context = dict(self._context or {})
        rec = []
        if context.get('default_floor_count', False):
            for floor_rec in range(
                    1, len(context['default_floor_count']) + 1):
                res = (str(floor_rec), str(floor_rec))
                rec.append(res)
        return rec

    @api.model
    def get_tower(self):
        """
        This Method is used to show towers
        from active property.
        """
        context = dict(self._context or {})
        rec = []
        if 'default_newtower' in context:
            for tower_rec in context['default_newtower']:
                res = (str(tower_rec), str(tower_rec))
                rec.append(res)
        return rec

    property_created_ids = fields.Many2many(
        comodel_name='property.created',
        relation='rel_wizz_id',
        column1='wizz_id',
        column2='propert_id',
        string='Property Line')
    property_id = fields.Many2one(
        comodel_name='property.created',
        string='Property')
    tower = fields.Selection(
        'get_tower',
        string='Tower',
        help='Prefix Or First Letter Of Tower.')
    newtower = fields.Char(
        string='Prefix Of Tower')
    floor_count = fields.Char(
        string='Number Of Floor',
        help='Number Of Tower.')
    floor = fields.Selection(
        'get_floor',
        string='Floor No.')

    @api.onchange('property_id')
    def property_change(self):
        """
        This Method is used to set child properties
        on change ofproperty_id.
        """
        # res = {}
        rec = []
        if self.property_id:
            property_id2 = self.property_id.asset_id.id
            prop_ids = self.env['property.created'].search(
                [('parent_id', '=', property_id2)])
            rec.append((6, 0, prop_ids.ids))
            self.property_created_ids = rec

    @api.multi
    def property_method(self):
        res = []
        cr, uid, context = self.env.args
        context = dict(context)
        for property_rec in self:
            if property_rec.floor:
                for rec in property_rec.property_created_ids:
                    old_name = rec.name
                    bool_name = old_name.startswith(str(property_rec.tower))
                    if int(rec.floor_number) == int(property_rec.floor) and \
                            bool_name and rec.state != 'cancel':
                        res.append(rec.id)
                    context.update({'result3': res})
                    self.env.args = cr, uid, misc.frozendict(context)
            return {
                'name': ('Property Wizard'),
                'res_model': 'sub.wizzard',
                'type': 'ir.actions.act_window',
                'view_id': False,
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
                'context': {'default_property_created_merged_ids':
                            context.get('result3')},
                'nodestroy': True,
            }


class PropertyParentMergeWizard(models.TransientModel):
    _name = "property.parent.merge.wizard"

    new_prop_id = fields.Many2one(
        comodel_name='property.created',
        string='Property')
    new_property_created_ids = fields.Many2many(
        comodel_name='property.created',
        relation='rel_new_wizz_id',
        column1='new_wizz_id',
        column2='new_propert_id',
        string='Property Line123')
    main_property_id = fields.Many2one(
        comodel_name='property.created',
        string='Main Property')

    @api.onchange('new_prop_id')
    def onchange_property(self):
        if self.new_prop_id:
            prop_merge_obj = self.new_prop_id
            pareid = prop_merge_obj.asset_id and prop_merge_obj.asset_id.id
            property_ids = self.env['property.created'].search(
                [('parent_id', '=', pareid), ('state', '=', 'draft')]).ids
            return {'domain': {
                'new_property_created_ids':
                [('id', 'in', property_ids)],
                'main_property_id':
                [('id', 'in', property_ids)]
            }
            }

    @api.onchange('main_property_id')
    def onchange_mainproperty(self):
        if self.main_property_id:
            prop_merge_obj = self.new_prop_id
            pareid = prop_merge_obj.asset_id.id
            property_ids = self.env['property.created'].search(
                [('parent_id', '=', pareid)]).ids
            main_id = self.main_property_id.id
            child_ids = property_ids
            if main_id in child_ids:
                child_ids.remove(int(main_id))
            return {'domain': {
                'new_property_created_ids':
                [('id', 'in', child_ids)]}}

    @api.multi
    def property_merge_parent(self):
        """
        This method is used to merge child properties
        from property form view.
        """
        data_prop = []
        for rec in self:
            activeids = rec.new_property_created_ids
            mainid = rec.main_property_id
            if mainid.id:
                if len(activeids.ids) == 0:
                    raise Warning(
                        _("Please select atleast one property for merge."))
            if activeids.ids:
                for rec_brw in activeids:
                    data_prop += rec_brw.read(['state',
                                               'parent_id', 'floor_number'])
                for main_rec_brw in mainid:
                    data_prop += main_rec_brw.read(
                        ['state', 'parent_id', 'floor_number'])
                for data in data_prop:
                    if not data['parent_id']:
                        raise Warning(
                            _("Please select sub properties. \n Not \
                            parent property!"))
                states = [data['state']
                          for data in data_prop if data['state'] != 'draft']
                if states:
                    raise Warning(
                        _("Only Available state properties are allowed \
                        to be merged!"))
                parents = list(set([x['parent_id'][0] for x in data_prop]))
                if len(parents) != 1:
                    raise Warning(
                        _("Please select sub properties from the same Parent \
                        property!"))
                check_property = False
                maxm = 0
                prop_f_no = 0
                prop_p_no = False
                for main_prop in mainid:
                    check_property = main_prop
                    prop_f_no = int(main_prop.floor_number)
                    prop_p_no = str(main_prop.prop_number)
                    if main_prop.label_id:
                        maxm = int(main_prop.label_id.name)
                for prop in activeids:
                    maxm += int(prop.label_id.name)
                    vals = {
                        'name': prop.name + "->" + "Merge" + "->" +
                        check_property.name,
                        'state': 'cancel',
                    }
                    floor_no = list(
                        set([x['floor_number'][0] for x in data_prop]))
                    if len(floor_no) != 1:
                        if int(prop.floor_number) in (prop_f_no + 1,
                                                      prop_f_no - 1) and \
                                str(prop.prop_number)\
                                == prop_p_no:
                            prop.write(vals)
                        else:
                            raise Warning(
                                _("Please select sub properties from the same \
                                Floors!"))
                    prop.write(vals)
                requ_id = self.env['property.label'].search(
                    [('name', '=', int(maxm))])
                if len(requ_id.ids) != 1 and int(maxm) != 0:
                    raise Warning(
                        _('Please Create label of %s ' % (
                            str(maxm) + " " + str(prop.label_id.code))))
                check_property.write({'label_id': maxm})
        return {'type': 'ir.actions.act_window_close'}


class PropertySubWizard(models.TransientModel):
    _name = "sub.wizzard"

    property_created_merged_ids = fields.Many2many(
        comodel_name='property.created',
        relation='rel_wizz_id21',
        column1='wizz_id21',
        column2='propert_id21',
        string='Property Line')
    name_prop_name = fields.Char(
        string='New Name Of Property',
        help='New Name Of Property.')
    is_other = fields.Boolean(
        string='Is Shop',
        help='Check if it is other property.')
    furnish = fields.Selection(
        [('none', 'None'),
         ('semi_furnished', 'Semi Furnished'),
         ('full_furnished', 'Full Furnished')],
        string='Furnishing',
        default='full_furnished',
        help='Furnishing.')

    @api.multi
    def sub_method(self):
        """
        This method is used to update property values.
        """
        if self._context is None:
            self._context = {}
        for res in self:
            label_change = False
            for rec in res.property_created_merged_ids:
                if not res.is_other:
                    label_change = rec.label_id.id
                old_name = rec.name
                new_name = old_name.replace(
                    str(rec.tower_num), str(res.name_prop_name))
                stval = {'name': new_name,
                         'tower_num': res.name_prop_name,
                         'furnished': res.furnish,
                         'property_manager': rec.property_manager.id,
                         'state': rec.state,
                         'label_id': label_change,
                         }
                rec.write(stval)
        return True
