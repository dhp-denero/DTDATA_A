# -*- coding: utf-8 -*-

from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import Warning

class JobCosting(models.Model):
    _name = 'job.costing'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "Job Costing"
    _rec_name = 'number'
    
    @api.model
    def create(self,vals):
        number = self.env['ir.sequence'].next_by_code('job.costing')
        vals.update({
            'number': number,
        })
        return super(JobCosting, self).create(vals) 
    
    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise Warning(_('You can not delete Job Cost Sheet which is not draft or cancelled.'))
        return super(JobCosting, self).unlink()
    
    @api.depends(
        'job_cost_line_ids',
        'job_cost_line_ids.product_qty',
        'job_cost_line_ids.cost_price',
    )
    def _compute_material_total(self):
        for rec in self:
            rec.material_total = sum([(p.product_qty * p.cost_price) for p in rec.job_cost_line_ids])
                
    @api.depends(
        'job_labour_line_ids',
        'job_labour_line_ids.hours',
        'job_labour_line_ids.cost_price'
    )
    def _compute_labor_total(self):
        for rec in self:
            rec.labor_total = sum([(p.hours * p.cost_price) for p in rec.job_labour_line_ids])

    @api.depends(
        'job_overhead_line_ids',
        'job_overhead_line_ids.product_qty',
        'job_overhead_line_ids.cost_price'
    )
    def _compute_overhead_total(self):
        for rec in self:
            rec.overhead_total = sum([(p.product_qty * p.cost_price) for p in rec.job_overhead_line_ids])

    @api.depends(
        'material_total',
        'labor_total',
        'overhead_total'
    )
    def _compute_jobcost_total(self):
        for rec in self:
            rec.jobcost_total = rec.material_total + rec.labor_total + rec.overhead_total
                
    @api.multi
    def _purchase_order_line_count(self):
        purchase_order_lines_obj = self.env['purchase.order.line']
        for order_line in self:
            order_line.purchase_order_line_count = purchase_order_lines_obj.search_count([('job_cost_id','=',order_line.id)])
            
    @api.multi
    def _timesheet_line_count(self):
        hr_timesheet_obj = self.env['account.analytic.line']
        for timesheet_line in self:
            timesheet_line.timesheet_line_count = hr_timesheet_obj.search_count([('job_cost_id', '=', timesheet_line.id)])
    
    @api.multi
    def _account_invoice_line_count(self):
        account_invoice_lines_obj = self.env['account.invoice.line']
        for invoice_line in self:
            invoice_line.account_invoice_line_count = account_invoice_lines_obj.search_count([('job_cost_id', '=', invoice_line.id)])
            
    @api.onchange('project_id')
    def _onchange_project_id(self):
        for rec in self:
            rec.analytic_id = rec.project_id.analytic_account_id.id
                
    number = fields.Char(
        readonly=True,
        default='New',
        copy=False,
    )
    name = fields.Char(
        required=True,
        copy=True,
        default='New',
        string='Name',
    )
    notes_job = fields.Text(
        required=False,
        copy=True,
        string='Job Cost Details'
    )
    user_id = fields.Many2one(
        'res.users', 
        default=lambda self: self.env.user, 
        string='Created By', 
        readonly=True
    )
    description = fields.Char(
        string='Description',
    )
    currency_id = fields.Many2one(
        'res.currency', 
        string='Currency', 
        default=lambda self: self.env.user.company_id.currency_id, 
        readonly=True
    )
    company_id = fields.Many2one(
        'res.company', 
        default=lambda self: self.env.user.company_id, 
        string='Company', 
        readonly=True
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
    )
    analytic_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
    )
    contract_date = fields.Date(
        string='Contract Date',
    )
    start_date = fields.Date(
        string='Create Date',
        readonly=True,
        default=fields.Date.today(),
    )
    complete_date = fields.Date(
        string='Closed Date',
        readonly=True,
    )
    material_total = fields.Float(
        string='Total Material Cost',
        compute='_compute_material_total',
        store=True,
    )
    labor_total = fields.Float(
        string='Total Labour Cost',
        compute='_compute_labor_total',
        store=True,
    )
    overhead_total = fields.Float(
        string='Total Overhead Cost',
        compute='_compute_overhead_total',
        store=True,
    )
    jobcost_total = fields.Float(
        string='Total Cost',
        compute='_compute_jobcost_total',
        store=True,
    )
    job_cost_line_ids = fields.One2many(
        'job.cost.line',
        'direct_id',
        string='Direct Materials',
        copy=False,
        domain=[('job_type','=','material')],
    )
    job_labour_line_ids = fields.One2many(
        'job.cost.line',
        'direct_id',
        string='Direct Materials',
        copy=False,
        domain=[('job_type','=','labour')],
    )
    job_overhead_line_ids = fields.One2many(
        'job.cost.line',
        'direct_id',
        string='Direct Materials',
        copy=False,
        domain=[('job_type','=','overhead')],
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
    )
    state = fields.Selection(
        selection=[
                    ('draft','Draft'),
                    ('confirm','Confirmed'),
                    ('approve','Approved'),
                    ('done','Done'),
                    ('cancel','Canceled'),
                  ],
        string='State',
        track_visibility='onchange',
        default=lambda self: _('draft'),
    )
    task_id = fields.Many2one(
        'project.task',
        string='Job Order',
    )
    so_number = fields.Char(
        string='Sale Reference'
    )
    issue_id = fields.Many2one(
        'project.issue',
        string='Job Issue',
    )
    
    purchase_order_line_count = fields.Integer(
        compute='_purchase_order_line_count'
    )
    
    purchase_order_line_ids = fields.One2many(
        "purchase.order.line",
        'job_cost_id',
    )
    
    timesheet_line_count = fields.Integer(
        compute='_timesheet_line_count'
    )
    
    timesheet_line_ids = fields.One2many(
        'account.analytic.line',
        'job_cost_id',
    )
    
    account_invoice_line_count = fields.Integer(
        compute='_account_invoice_line_count'
    )
    
    account_invoice_line_ids = fields.One2many(
        "account.invoice.line",
        'job_cost_id',
    )
    
    @api.multi
    def action_draft(self):
        for rec in self:
            rec.write({
                'state' : 'draft',
            })
    
    @api.multi
    def action_confirm(self):
        for rec in self:
            rec.write({
                'state' : 'confirm',
            })
        
    @api.multi
    def action_approve(self):
        for rec in self:
            rec.write({
                'state' : 'approve',
            })
    
    @api.multi
    def action_done(self):
        for rec in self:
            rec.write({
                'state' : 'done',
                'complete_date':date.today(),
            })
        
    @api.multi
    def action_cancel(self):
        for rec in self:
            rec.write({
                'state' : 'cancel',
            })
    @api.multi
    def action_view_purchase_order_line(self):
        self.ensure_one()
        purchase_order_lines_obj = self.env['purchase.order.line']
        cost_ids = purchase_order_lines_obj.search([('job_cost_id','=',self.id)]).ids
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order Line',
            'res_model': 'purchase.order.line',
            'res_id': self.id,
            'domain': "[('id','in',[" + ','.join(map(str, cost_ids)) + "])]",
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target' : self.id,
        }
        return action
        
    @api.multi
    def action_view_hr_timesheet_line(self):
        hr_timesheet = self.env['account.analytic.line']
        cost_ids = hr_timesheet.search([('job_cost_id','=',self.id)]).ids
        action = self.env.ref('hr_timesheet.act_hr_timesheet_line').read()[0]
        action['domain'] = [('id', 'in', cost_ids)]
        return action
        
    @api.multi
    def action_view_vendor_bill_line(self):
        account_invoice_lines_obj = self.env['account.invoice.line']
        cost_ids = account_invoice_lines_obj.search([('job_cost_id','=',self.id)]).ids
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Account Invoice Line',
            'res_model': 'account.invoice.line',
            'res_id': self.id,
            'domain': "[('id','in',[" + ','.join(map(str, cost_ids)) + "])]",
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target' : self.id,
        }
        return action
