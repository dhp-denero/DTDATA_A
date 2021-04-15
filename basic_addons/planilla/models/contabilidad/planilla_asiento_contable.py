# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.base.res.res_request import referenceable_models
from datetime import datetime
from decimal import *
from odoo.exceptions import UserError


class PlanillaAsientoContable(models.TransientModel):
    _name = "planilla.asiento.contable"
    total_debe = fields.Float('Total debe', digits=(12, 2))
    total_haber = fields.Float('Total haber', digits=(12, 2))
    diferencia = fields.Float('Diferencia', digits=(12, 2))
    diario = fields.Many2one('account.journal')
    cuenta_ajuste = fields.Many2one('account.account')

    @api.multi
    def do_rebuild(self):
        if not self.diario:
            raise UserError(
                "Es necesario que especifique un diario")

        payslip_run = self.env['hr.payslip.run'].search(
            [('id', '=', self.env.context['current_id'])])

        account_move_lines = self.env.context['account_move_lines']
        n_vals = {
            'journal_id': self.diario.id,
            'date': payslip_run.date_end,
            'ref': payslip_run.name,
            'company_id': 1
        }
        account_move_id = self.env['account.move'].create(n_vals)
        
        for account_move_line in account_move_lines:
            if account_move_line['debe'] > 0:
                if account_move_line['partner_id'] == 0:
                    query = """
                    insert into account_move_line(move_id,account_id,analytic_account_id,debit,credit,name,date_maturity,company_id,date)
                    values(%d,%d,%d,%f,%f,'%s','%s',1,'%s')
                    """ % (account_move_id.id, account_move_line['cuenta_debe'],
                           account_move_line['cuenta_analitica_id'],
                           float(account_move_line['debe']),
                           0.0,
                           account_move_line['concepto'],
                           payslip_run.date_end,
                           payslip_run.date_end)
                else:
                    query = """
                    insert into account_move_line(move_id,account_id,analytic_account_id,debit,credit,name,date_maturity,company_id,date,partner_id,nro_comprobante)
                    values(%d,%d,%d,%f,%f,'%s','%s',1,'%s',%d,'%s')
                    """ % (account_move_id.id, account_move_line['cuenta_debe'],
                           account_move_line['cuenta_analitica_id'],
                           float(account_move_line['debe']),
                           0.0,
                           account_move_line['concepto'],
                           payslip_run.date_end,
                           payslip_run.date_end,
                           account_move_line['partner_id'],
                           account_move_line['nro_documento'] if account_move_line['nro_documento'] else '')
            else:
                if account_move_line['partner_id'] == 0:
                    query = """
                    insert into account_move_line(move_id,account_id,debit,credit,name,date_maturity,company_id,date)
                    values(%d,%d,%f,%f,'%s','%s',1,'%s')
                    """ % (account_move_id.id,
                           account_move_line['cuenta_debe'],
                           0.0,
                           float(account_move_line['haber']),
                           account_move_line['concepto'],
                           payslip_run.date_end,
                           payslip_run.date_end)
                else:
                    query = """
                    insert into account_move_line(move_id,account_id,debit,credit,name,date_maturity,company_id,date,partner_id,nro_comprobante)
                    values(%d,%d,%f,%f,'%s','%s',1,'%s',%d,'%s')
                    """ % (account_move_id.id,
                           account_move_line['cuenta_debe'],
                           0.0,
                           float(account_move_line['haber']),
                           account_move_line['concepto'],
                           payslip_run.date_end,
                           payslip_run.date_end,
                           account_move_line['partner_id'],
                           account_move_line['nro_documento'] if account_move_line['nro_documento'] else '')
            self.env.cr.execute(query)
        if self.diferencia > 0:
            if not self.cuenta_ajuste.id:
                raise UserError(
                    "Es necesario que especifique una cuenta de ajuste")
            nl_vals = {
                'move_id': account_move_id.id,
                'account_id': self.cuenta_ajuste.id,
                'analytic_account_id': None,
                'debit': 0,
                'credit': float(abs(self.diferencia)),
                'name': "regularizacion montos",
            }
            n_aml = self.env['account.move.line'].create(nl_vals)
        elif self.diferencia < 0:
            if not self.cuenta_ajuste.id:
                raise UserError(
                    "Es necesario que especifique una cuenta de ajuste")
            nl_vals = {
                'move_id': account_move_id.id,
                'account_id': self.cuenta_ajuste.id,
                'analytic_account_id': None,
                'debit': float(abs(self.diferencia)),
                'credit': 0,
                'name': "regularizacion montos",
            }
            n_aml = self.env['account.move.line'].create(nl_vals)
        payslip_run.state='generado'
        am = self.env['account.move'].browse(account_move_id).id
        total = float(Decimal(str(sum([line.debit for line in am.line_ids]))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        print(total)
        am.write({'amount':total})
        payslip_run.asiento_contable_id = am.id

