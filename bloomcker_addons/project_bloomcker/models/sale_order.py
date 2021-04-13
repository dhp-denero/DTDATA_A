# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging


class ProjectExt(models.Model):
    _inherit = 'sale.order'

    def data_for_order_report_bl(self):
        data = []
        ids_category = []
        for i in self.order_line:
            if i.product_id.categ_id not in ids_category:
                ids_category.append(i.product_id.categ_id)
        print(ids_category)
        for i in ids_category:
            for j in self.order_line:
                if i.id == j.product_id.categ_id.id:
                    if not i.name:
                        category = "otro"
                    else:
                        category = str(i.name)
                    registro = {
                        'category':category,
                        'item':1,
                        'name':str(j.product_id.name),
                        'description':str(j.product_id.description),
                        'cant':str(j.product_uom_qty),
                        'und':str(j.product_id.uom_id.display_name),
                        'price':str(j.product_id.list_price)
                    }
                    data.append(registro)
        print(data)
        return data