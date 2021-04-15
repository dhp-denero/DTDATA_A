# -*- coding: utf-8 -*-
# Copyright 2015 Guewen Baconnier <guewen.baconnier@camptocamp.com>
# Copyright 2016 Vicent Cubells <vicent.cubells@tecnativa.com>
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "PICKING EN EL INVENTARIO",
    "version": "9.0.1.1.0",
    "category": "stock",
    
    "author": "ITGRUPO-RAPTOR",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock",
		"kardex_it"
    ],

    "data": [
        "views/stock_inventory_view.xml",
		"security/ir.model.access.csv",
    ],
}
