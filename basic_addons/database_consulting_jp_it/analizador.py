# -*- coding: utf-8 -*-
from openerp.http import Controller
from openerp.http import request, route
import decimal
import openerp.http as http
from openerp import models, fields, api
import base64
from openerp.osv import osv
import decimal
import sys, traceback
from openerp.tools.translate import _
from lxml.builder import E
from collections import defaultdict
from lxml import etree
from itertools import chain, repeat

def name_boolean_group(id):
	return 'in_group_' + str(id)

def name_selection_groups(ids):
	return 'sel_groups_' + '_'.join(map(str, ids))

def is_boolean_group(name):
	return name.startswith('in_group_')

def is_selection_groups(name):
	return name.startswith('sel_groups_')

def is_reified_group(name):
	return is_boolean_group(name) or is_selection_groups(name)

def get_boolean_group(name):
	return int(name[9:])

def get_selection_groups(name):
	return map(int, name[11:].split('_'))

def partition(f, xs):
	"return a pair equivalent to (filter(f, xs), filter(lambda x: not f(x), xs))"
	yes, nos = [], []
	for x in xs:
		(yes if f(x) else nos).append(x)
	return yes, nos
class res_groups(models.Model):
	_inherit ='res.groups'

	para_configurar_menus = fields.Boolean('Para Configurar Menus')
	configurado = fields.Boolean('Personalización',help=u"Respeta configuración de Menus")


	@api.model
	def get_groups_by_application32(self):
		""" Return all groups classified by application (module category), as a list::

				[(app, kind, groups), ...],

			where ``app`` and ``groups`` are recordsets, and ``kind`` is either
			``'boolean'`` or ``'selection'``. Applications are given in sequence
			order.  If ``kind`` is ``'selection'``, ``groups`` are given in
			reverse implication order.
		"""
		def linearize(app, gs):
			# determine sequence order: a group appears after its implied groups
			order = {g: len(g.trans_implied_ids & gs) for g in gs}
			# check whether order is total, i.e., sequence orders are distinct
			if len(set(order.itervalues())) == len(gs):
				return (app, 'selection', gs.sorted(key=order.get))
			else:
				return (app, 'boolean', gs)

		# classify all groups by application
		by_app, others = defaultdict(self.browse), self.browse()
		for g in self.get_application_groups([]):
			if g.category_id:
				if g.para_configurar_menus:					
					by_app[g.category_id] += g
			else:
				others += g
		# build the result
		res = []
		for app, gs in sorted(by_app.iteritems(), key=lambda (a, _): a.sequence or 0):
			res.append(linearize(app, gs))
		if others:
			res.append((self.env['ir.module.category'], 'boolean', others))


		return res

	

	@api.model
	def _update_user_groups_view(self):
		""" Modify the view with xmlid ``base.user_groups_view``, which inherits
			the user form view, and introduces the reified group fields.
		"""
		if self._context.get('install_mode'):
			# use installation/admin language for translatable names in the view
			user_context = self.env['res.users'].context_get()
			self = self.with_context(**user_context)

		# We have to try-catch this, because at first init the view does not
		# exist but we are already creating some basic groups.
		view = self.env.ref('base.user_groups_view', raise_if_not_found=False)
		if view and view.exists() and view._name == 'ir.ui.view':
			group_no_one = view.env.ref('base.group_no_one')
			xml1, xml2 = [], []
			xml1.append(E.separator(string=_('Application'), colspan="2"))
			for app, kind, gs in self.get_groups_by_application():
				# hide groups in categories 'Hidden' and 'Extra' (except for group_no_one)
				attrs = {}
				if app.xml_id in ('base.module_category_hidden', 'base.module_category_extra', 'base.module_category_usability'):
					attrs['groups'] = 'base.group_no_one'

				if kind == 'selection':
					# application name with a selection field
					field_name = name_selection_groups(gs.ids)
					xml1.append(E.field(name=field_name, **attrs))
					xml1.append(E.newline())
				else:
					# application separator with boolean fields
					app_name = app.name or _('Other')
					xml2.append(E.separator(string=app_name, colspan="4", **attrs))
					for g in gs:
						field_name = name_boolean_group(g.id)
						if g == group_no_one:
							# make the group_no_one invisible in the form view
							xml2.append(E.field(name=field_name, invisible="1", **attrs))
						else:
							xml2.append(E.field(name=field_name, **attrs))

			xml2.append({'class': "o_label_nowrap"})
			xml = E.field(E.group(*(xml1), col="2"), E.group(*(xml2), col="4"), name="groups_id", position="replace")
			xml.addprevious(etree.Comment("GENERATED AUTOMATICALLY BY GROUPS"))
			xml_content = etree.tostring(xml, pretty_print=True, xml_declaration=True, encoding="utf-8")
			view.with_context(lang=None).write({'arch': xml_content})


		view = self.env.ref('database_consulting_jp_it.user_groups_view_itf', raise_if_not_found=False)

		if view and view.exists() and view._name == 'ir.ui.view':
			group_no_one = view.env.ref('base.group_no_one')
			xml1, xml2 = [], []
			xml1.append(E.separator(string='Acceso a Menus', colspan="2"))
			for app, kind, gs in self.get_groups_by_application32():
				# hide groups in categories 'Hidden' and 'Extra' (except for group_no_one)
				attrs = {}
				if app.xml_id in ('base.module_category_hidden', 'base.module_category_extra', 'base.module_category_usability'):
					attrs['groups'] = 'base.group_no_one'
				
				if kind == 'selection':
					pass
				else:
					# application separator with boolean fields
					app_name = app.name or _('Other')
					xml2.append(E.separator(string=app_name, colspan="4", **attrs))
					for g in gs:
						field_name = name_boolean_group(g.id)
						if g == group_no_one:
							# make the group_no_one invisible in the form view
							xml2.append(E.field(name=field_name, invisible="1", **attrs))
						else:
							xml2.append(E.field(name=field_name, **attrs))

			xml2.append({'class': "o_label_nowrap"})
			xml = E.field(E.group(*(xml1), col="2"), E.group(*(xml2), col="4"), name="groups_id", position="replace")
			xml.addprevious(etree.Comment("GENERATED AUTOMATICALLY BY GROUPS"))
			xml_content = etree.tostring(xml, pretty_print=True, xml_declaration=True, encoding="utf-8")
			view.with_context(lang=None).write({'arch': xml_content})
			