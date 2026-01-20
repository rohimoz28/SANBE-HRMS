from odoo import fields, models, api, Command
from odoo.exceptions import ValidationError, UserError

class SbLoanInstallmentMonitoring (models.Model):
    _name = 'sb.loan.installment.monitoring'
    _description = 'Loan Installment Monitoring'

    area_id = fields.Many2one('res.territory', string='Area')
    branch_id = fields.Many2one('res.branch', string='Business Unit')
    department_id = fields.Many2one('hr.department', string='Sub Department')
    nik = fields.Char('NIK')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    creditor = fields.Char('Creditor')
    loan_contract_no = fields.Char('Loan Contract No')
    amount_loan = fields.Float('Amount Loan')
    installment = fields.Integer('# of Installment')
    amt_installment = fields.Float('Amt Installment')
    date_from = fields.Date('Start From')
    date_to = fields.Date('To')
    loan_repayment_ids = fields.One2many('sb.loan.repayment', 'loan_monitoring_id', string='Loan Repayment Ids')

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