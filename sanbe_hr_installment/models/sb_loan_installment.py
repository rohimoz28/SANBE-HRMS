from odoo import fields, models, api, Command
from odoo.exceptions import ValidationError, UserError

class SbLoanInstallment (models.Model):
    _name = 'sb.loan.installment'
    _description = 'Loan Installment'

    trx_no = fields.Char('Trx No')
    trx_date = fields.Date('Trx Date', default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved_by_hrd', 'Approved by HRD'),
        ('payment_process', 'Payment Process'),
        ('closed', 'Closed'),
    ], default='draft', string='Status')
    creditor = fields.Selection([
        ('koperasi', 'Koperasi'),
        ('bsa', 'BSA'),
    ], string='Creditor')
    area_id = fields.Many2one('res.territory', string='Area', required=True, 
                              default=lambda self: self.env.user.area.id)
    branch_ids = fields.Many2many('res.branch', 'res_branch_rel', string='AllBranch', compute='_compute_branch_ids',
                                  store=False)
    branch_id = fields.Many2one('res.branch', string='Business Unit', domain="[('id','in',branch_ids)]")
    department_id = fields.Many2one('hr.department', string='Sub Department', domain="[('branch_id','=',branch_id)]")
    employee_id = fields.Many2one('hr.employee', string='Employee', domain="[('area','=',area_id),('branch_id','=',branch_id),('department_id','=',department_id)]")
    job_status = fields.Selection([('permanent', 'Permanent'),
                                   ('contract', 'Contract'),
                                   ('outsource', 'Outsource'),
                                   ('visitor', 'Visitor'),
                                   ('mitra', 'Mitra'),
                                   ('tka', 'TKA'),
                                   ],
                                  string='Job Status')
    emp_status_id = fields.Many2one('hr.emp.status', string='Employment Status')
    join_date_contract = fields.Date('Join Date')
    pension_date = fields.Date('Pension Date')
    contract_id = fields.Many2one('hr.contract', string='Contract No')
    contract_datefrom = fields.Date('Contract From')
    contract_dateto = fields.Date('Contract To')
    loan_contract_no = fields.Char('Loan Contract No')
    contract_date = fields.Date('Contract Date', default=fields.Date.today)
    amount_loan = fields.Float('Amount Loan')
    installment = fields.Integer('# of Installment')
    amt_installment = fields.Float('Amt Installment')
    date_from = fields.Date('Start From')
    date_to = fields.Date('To')
    desc = fields.Text('Keterangan')
    is_hrd_user = fields.Boolean('Is HRD User', compute='_compute_is_hrd_user', store=False)

    @api.depends('area_id')
    def _compute_branch_ids(self):
        for allrecs in self:
            databranch = []
            for allrec in allrecs.area_id.branch_id:
                mybranch = self.env['res.branch'].search([('name', '=', allrec.name)], limit=1)
                databranch.append(mybranch.id)
            allbranch = self.env['res.branch'].sudo().search([('id', 'in', databranch)])
            allrecs.branch_ids = [Command.set(allbranch.ids)]

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            if rec.employee_id:
                rec.job_status = rec.employee_id.job_status
                rec.emp_status_id = rec.employee_id.emp_status_id.id
                rec.join_date_contract = rec.employee_id.join_date_contract
                rec.pension_date = rec.employee_id.pension_date
                rec.contract_id = rec.employee_id.contract_id
                rec.contract_datefrom = rec.employee_id.contract_datefrom
                rec.contract_dateto = rec.employee_id.contract_dateto
    
    @api.constrains('date_to','job_status')
    def _constrains_end_installment(self):
        for rec in self:
            if not rec.date_to:
                continue
            
            if rec.job_status == 'contract':
                if rec.date_to > rec.contract_dateto:
                    raise ValidationError(
                        "Masa akhir installment tidak boleh melebihi Contract To atau Pension Date"
                    )
            elif rec.job_status == 'permanent':
                if rec.date_to > rec.pension_date:
                    raise ValidationError(
                        "Masa akhir installment tidak boleh melebihi Contract To atau Pension Date"
                    )

    @api.depends('branch_id')
    def _compute_is_hrd_user(self):
        for rec in self:
            param = self.env['ir.config_parameter'].sudo()
            value = param.get_param('sb_loan_installment_hrd') or ''

            hrd_employee_ids = []
            if value:
                hrd_employee_ids = [int(x) for x in value.split(',') if x.strip()]
            
            user = self.env.user
            
            has_group = user.has_group(
                'sanbe_hr_installment.module_sub_category_loan_installment_hrd'
            )

            employee = self.env['hr.employee'].sudo().search(
                [('user_id', '=', user.id),
                ('branch_id', '=', rec.branch_id.id)],
                limit=1
            )

            rec.is_hrd_user = (employee.id in hrd_employee_ids and has_group)
    
    def btn_appv_hrd(self):
        for rec in self:
            rec.state = 'approved_by_hrd'
    
    def btn_payment(self):
        for rec in self:
            rec.state = 'payment_process'
    
    def btn_closed(self):
        for rec in self:
            rec.state = 'closed'