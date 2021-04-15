from odoo import api, fields, models, _

import logging



_logger = logging.getLogger(__name__)


class ProjectNativeReport(models.TransientModel):
    _name = "project.native.report"

    project_id = fields.Many2one('project.project', 'Project', readonly=True)
    name = fields.Char(string='Name', default='PDF Report', readonly=True)



    @api.multi
    def print_pdf(self):
        datas = {
            'ids': [self.project_id.id],
            'model': 'project.project',
        }

        return self.env['report'].get_action([], 'project_native_report.project_native_gantt_report', data=datas)

        # docargs = {
        #     'doc_ids': docids,
        #     'doc_model': 'project.project',
        #     'docs': self.env['project.project'].browse(docids),
        #     'get_gantt': self.get_gantt,
        #     'data': data,
        # }
        # return self.env['report'].render('project_native_report.project_native_gantt_report', docargs)

        # @api.model
        # def render_html(self, docids, data=None):
        #     docargs = {
        #         'doc_ids': docids,
        #         'doc_model': 'project.project',
        #         'docs': self.env['project.project'].browse(docids),
        #         'get_gantt': self.get_gantt,
        #         'data': data,
        #     }
        #     return self.env['report'].render('project_native_report.project_native_gantt_report', docargs)

        # datas = {
        #      'ids': active_ids,
        #      'model': 'hr.contribution.register',
        #      'form': self.read()[0]
        # }
        # return self.env['report'].get_action([], 'hr_payroll.report_contributionregister', data=datas)

        # return self.env.ref('project_native_report.action_report_project_native_gantt').report_action([self.group_id.id])

# return self.env['report'].get_action(self, 'sale.report_saleorder')
#        data = {'ids': self.env.context.get('active_ids', [])}
#        res = self.read()
#        res = res and res[0] or {}
#        data.update({'form': res})
#        return self.env['report'].get_action(self, 'l10n_in_hr_payroll.report_hryearlysalary', data=data)
