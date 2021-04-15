# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _
from odoo.osv import expression
from odoo.tools import float_is_zero
from odoo.tools import float_compare, float_round, float_repr
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError
import time		
import codecs

