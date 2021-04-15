# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import http
from odoo.http import request


class Home(http.Controller):

    @http.route('/web/graph_data', type='json', auth="public")
    def graph_data(self, redirect=None, **kw):
        property_obj = request.env['account.asset.asset']
        proprty_rec = property_obj.search([])
        res = [{'name': 'simulation', 'data': []},
               {'name': 'revenue', 'data': []}]
        category = []
        for proprty in proprty_rec:
            category.append(proprty.name)
            res[0]['data'].append([proprty.name, proprty.simulation])
            res[1]['data'].append([proprty.name, proprty.revenue])
        return [res, category]
