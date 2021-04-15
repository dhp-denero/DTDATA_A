# -*- coding: utf-8 -*-

import datetime
import json
import werkzeug
from odoo import http
from odoo.http import request
from odoo import tools
from odoo.addons.website.models.website import slug, unslug
from odoo.exceptions import UserError
from odoo.osv.orm import browse_record
from odoo.tools.translate import _
from odoo import SUPERUSER_ID
from odoo.tools import html2plaintext

from odoo.addons.website_form.controllers.main import WebsiteForm
from openerp.addons.website_blog.controllers.main import WebsiteBlog

class WebsiteBlog(WebsiteBlog):

	@http.route(['/blog/get_blog_content'], type='http', auth='public', website=True)
	def get_blog_content_data(self, **post):
		value={}
		if post.get('blog_config_id')!='false':
			collection_data=request.env['blog.configure'].browse(int(post.get('blog_config_id')))
			value.update({'blog_slider':collection_data})
		return request.render("theme_laze.blog_slider_content", value)

class WebsiteForm(WebsiteForm):

    @http.route('/website_form/create_leads', type='http', auth="public", methods=['POST'], website=True)
    def website_form_lead(self,**kwargs):
        model_record = request.env['ir.model'].search([('model', '=', 'crm.lead'), ('website_form_access', '=', True)])
        if not model_record:
            return json.dumps(False)

        try:
            data = self.extract_data(model_record, request.params)
        # If we encounter an issue while extracting data
        except ValidationError, e:
            # I couldn't find a cleaner way to pass data to an exception
            return json.dumps({'error_fields' : e.args[0]})

        try:
            id_record = self.insert_record(request, model_record, data['record'], data['custom'], data.get('meta'))
            if id_record:
                self.insert_attachment(model_record, id_record, data['attachments'])

        # Some fields have additional SQL constraints that we can't check generically
        # Ex: crm.lead.probability which is a float between 0 and 1
        # TODO: How to get the name of the erroneous field ?
        except IntegrityError:
            return json.dumps(False)

        request.session['form_builder_model'] = model_record.name
        request.session['form_builder_id']    = id_record

        return request.redirect('/page/website_crm.contactus_thanks')
