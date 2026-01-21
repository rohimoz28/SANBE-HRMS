from odoo import fields, models, api


class SbLoanRepayment (models.Model):
    _name = 'sb.loan.repayment'
    _description = 'Loan Installment Monitoring'

    loan_monitoring_id = fields.Many2one('sb.loan.installment.monitoring', string='Loan Monitoring')
    pay = fields.Float('Pay')
    pay_date = fields.Date('Pay Date')
    bb_amount = fields.Float('BB Amount')
    pay_amount = fields.Float('Pay Amount')
    eb_amount = fields.Float('EB Amount')
    status = fields.Char('Status')
