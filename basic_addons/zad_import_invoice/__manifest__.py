# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 BrowseInfo(<http://www.browseinfo.in>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Import Invoices from Excel or CSV File',
    'version': '10.0.0.1.0',
    'sequence': 4,
    'summary': '',
    "price": 18.99,
    "currency": 'EUR',
    'description': """
        This module used for import multiple Invoices from Excel file.
         Import Invoice lines from CSV or Excel file. 
    """,
    'author': 'Zadsolutions, Omar Abdulaziz',
    'website': 'www.zadsolutions.com',
    'category': 'Accounting',
    'depends': ['account_accountant'],
    'data': [
        "wizard/generate_invoices_view.xml",
    ],
    'qweb': [
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}

