from odoo import api, fields, models, tools, _
import calendar
from datetime import *
from decimal import *
from dateutil.relativedelta import relativedelta
import base64
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
import logging
_logger = logging.getLogger(__name__)

class HrLoanLineExtend(models.Model):
	_inherit = 'hr.loan.line'

	amount = fields.Float(string='Monto', digits=(16, 4))
	debt = fields.Float(string='Deuda por Pagar', digits=(16, 4))

class HrLoanExtend(models.Model):
	_inherit = 'hr.loan'

	@api.multi
	def get_fees(self):

		count_payed = debt_total = 0

		for line in self.line_ids:
			if line.validation == 'not payed':
				line.unlink()
			else:
				count_payed += 1
				debt_total += line.amount

		date = datetime.strptime(self.date,'%Y-%m-%d')
		first_debit = debt = self.amount
		fees = self.fees_number

		if count_payed > 0:
			date = date + relativedelta(months=count_payed)
			first_debit = debt = self.amount - debt_total
			fees = self.fees_number - count_payed

		# validacion que el nuevo numero de cuotas sea mayor que las cuotas pagadas
		if self.fees_number <= count_payed :
			raise UserError(_('Debe colocar un numero de cuotas mayor a las cuotas ya pagadas.'))

		for c,fee in enumerate(range(fees),1):
			c += count_payed
			first_day,last_day = calendar.monthrange(date.year,date.month)
			if c == 1 and date.day == last_day:
				date = date + relativedelta(months=1)
			if c != 1:
				date = date + relativedelta(months=1)
			first_day,last_day = calendar.monthrange(date.year,date.month)
			date = date.replace(day=last_day)
			fee_amount = float(Decimal(str(first_debit/fees)).quantize(Decimal('0.000000000001'), rounding=ROUND_HALF_UP))
			_logger.info(fee_amount)
			debt -= fee_amount
			self.env['hr.loan.line'].create({
					'loan_id':self.id,
					'employee_id':self.employee_id.id,
					'input_id':self.loan_type_id.input_id.id,
					'fee':c,
					'amount':fee_amount,
					'date':date,
					'debt': abs(debt)
				})
		return {}

	@api.multi
	def refresh_fees(self):
		total = self.amount
		for line in self.line_ids.sorted(lambda l:l.fee):
			total -= line.amount
			line.debt = total
		self.fees_number = len(self.line_ids)
