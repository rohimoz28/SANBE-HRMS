from odoo import fields, models, api, Command
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta

class SbLoanInstallment (models.Model):
    _name = 'sb.loan.installment'
    _description = 'Loan Installment'

    trx_no = fields.Char('Trx No', readonly=True)
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
    join_date = fields.Date('Join Date Permanent')
    pension_date = fields.Date('Pension Date')
    contract_id = fields.Many2one('hr.contract', string='Contract No')
    contract_datefrom = fields.Date('Contract From')
    contract_dateto = fields.Date('Contract To')
    loan_contract_no = fields.Char('Loan Contract No')
    contract_date = fields.Date('Contract Date', default=fields.Date.today)
    amount_loan = fields.Float('Amount Loan')
    installment = fields.Integer('# of Installment')
    amt_installment = fields.Float('Amt Installment', compute='_compute_amt_installment', store=True)
    date_from = fields.Date('Start From')
    date_to = fields.Date('To', compute='_compute_amt_installment', store=True)
    desc = fields.Text('Keterangan')
    is_hrd_user = fields.Boolean('Is HRD User', compute='_compute_is_hrd_user', store=False)

    def _get_branch_sequence(self, branch, trx_date):
        """Fungsi untuk create/return sequence per-branch"""

        year = trx_date.strftime('%y')   # 26
        month = trx_date.strftime('%m')  # 01
        
        seq_code = f'sb.loan.installment.branch.{branch.id}.{year}{month}'

        seq = self.env['ir.sequence'].sudo().search([
            ('code', '=', seq_code)
        ], limit=1)

        if not seq:
            seq = self.env['ir.sequence'].sudo().create({
                'name': f'Loan Installment {branch.name}',
                'code': seq_code,
                'padding': 6,
                'number_next': 1,
                'company_id': False,
            })

        return seq, year, month
    
    @api.model_create_multi
    def create(self, vals_list):
        """generate kode sequencce dengan format branch_code - year - month - sequence number"""
        for vals in vals_list:
            if not vals.get('trx_no'):
                trx_date = vals.get('trx_date') or fields.Date.today()
                trx_date = fields.Date.from_string(trx_date)

                branch = self.env['res.branch'].sudo().browse(vals.get('branch_id'))
                
                if branch:
                    seq, year, month = self._get_branch_sequence(branch, trx_date)
                    seq_number = seq.next_by_id()

                    vals['trx_no'] = f"{branch.branch_code}-{year}-{month}-{seq_number}"
        
        res = super(SbLoanInstallment,self).create(vals_list)
        return res

    @api.depends('date_from', 'amount_loan', 'installment')
    def _compute_amt_installment(self):
        for rec in self:
            if rec.date_from and rec.amount_loan and rec.installment:
                rec.amt_installment = rec.amount_loan / rec.installment 
                rec.date_to = rec.date_from + relativedelta(months=rec.installment - 1)
            else:
                rec.amt_installment = False
                rec.date_to = False

    @api.constrains('installment')
    def _constrains_installment(self):
        for rec in self:
            if rec.installment == 0:
                raise ValidationError(
                        "# of Installment tidak boleh 0"
                    )
    
    @api.constrains('amount_loan')
    def _constrains_amount_loan(self):
        for rec in self:
            if rec.amount_loan < 1:
                raise ValidationError(
                        "Amount Loan harus lebih dari 0"
                    )

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
                rec.join_date = rec.employee_id.join_date
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