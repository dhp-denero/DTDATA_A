# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Purchase Request to RFQ Change",
    "author": "ITGRUPO-OPCIONAL-COMPATIBLE-BO",
    "version": "10.0.1.0.0",
    "website": "http://www.eficent.com",
    "category": "Purchase Management",
    "depends": [
        "purchase_request",
        "purchase",
        "purchase_order_type",
        "purchase_request_to_rfq"],

    "data": [

        "purchase_request_line_make_purchase_order_view_inherit.xml",
    ],
    "license": 'AGPL-3',
    "installable": True
}
