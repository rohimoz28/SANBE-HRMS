from odoo import fields, models, api
from odoo.exceptions import UserError


EMP_PROFILE_STATE = [
    ('active', 'Active'),
    ('in_active', 'In Active'),
    ('hold', 'Hold')
]

EMP_GROUP1 = [
    ('Group1', 'Group 1 - Harian(pak Deni)'),
    ('Group2', 'Group 2 - bulanan pabrik(bu Felisca)'),
    ('Group3', 'Group 3 - Apoteker and Mgt(pak Ryadi)'),
    ('Group4', 'Group 4 - Security and non apoteker (bu Susi)'),
    ('Group5', 'Group 5 - Tim promosi(pak Yosi)'),
    ('Group6', 'Group 6 - Adm pusat(pak Setiawan)'),
    ('Group7', 'Group 7 - Tim Proyek (pak Ferry)'),
]

EMP_GROUP2 = [
    ('Group1', 'Group 1 - Harian(pak Deni)'),
    ('Group2', 'Group 2 - bulanan pabrik(bu Felisca)'),
    ('Group3', 'Group 3 - Apoteker and Mgt(pak Ryadi)'),
    ('Group4', 'Group 4 - security(bu Susi)'),
    ('Group5', 'Group 5 - Tim promosi(pak Yosi)'),
    ('Group6', 'Group 6 - Adm pusat(pak Setiawan)'),
]

TAX_METHOD1 = [
    ('nett', 'Nett'),
    ('gross', 'Gross'),
]

class SbEmployeeProfile(models.Model):
    _name = 'sb.employee.profile'
    _description = 'Employee Profile'

    @api.model
    def _selection1(self):
        return EMP_GROUP1

    employee_group1 = fields.Selection(selection=_selection1, string='Employee P Group',  readonly=True)
    employee_id = fields.Many2one('hr.employee', index=True)
    # employee_name = fields.Char(
    #     string='Employee Name',
    #     required=False)
    nik_new = fields.Char(string='NIK Baru', required=False, readonly=True)
    nik_old = fields.Char(string='NIK Lama', required=False , readonly=True)
    npwp = fields.Char(string='NPWP', required=False, readonly=True)
    gender = fields.Char(string='Gender', required=False, readonly=True)
    area_id = fields.Many2one('res.territory', string='Area', index=True)
    branch_id = fields.Many2one('res.branch', string='Business Unit', index=True)
    department_id = fields.Many2one('hr.department', string='Department')
    job_id = fields.Many2one('hr.job',readonly=True, string="Job Position")
    job_status = fields.Char(string='Job Status',required=False, readonly=True)
    employement_status = fields.Char(string='Employement Status', required=False, readonly=True)
    state = fields.Selection(string='State', selection=EMP_PROFILE_STATE, default='active')
    # employement details
    pay_type = fields.Selection(
        string='Pay Type',
        selection=[('monthly', 'Monthly'),
                   ('daily', 'Daily'), ],
        required=False)
    pay_period = fields.Selection(
        string='Pay Period',
        selection=[('monthly', 'Monthly'),
                   ('daily', 'Daily'), ],
        required=False)
    effective_date = fields.Date(string='Effective Date', required=False)
    bank_account = fields.Char(string='Bank Account', required=False)
    basic_salary = fields.Float(string='Basic Salary', required=False)
    status_ptkp = fields.Selection(
        string='Status PTKP',
        selection=[('tk0', 'TKO'),
                   ('tk1', 'TK1')],
        required=False)
    type_ter = fields.Selection(
        string='Type TER',
        selection=[('tera', 'TER A'),
                   ('terb', 'TER B')],
        required=False)
    tax_method = fields.Selection(selection=TAX_METHOD1, string="Tax Method", index=True, default="nett")
    bpjs_no = fields.Char(string='BPJS No', required=False)
    jamsostek_no = fields.Char(string='Jamsostek No', required=False)
    # end employement details
    compensation_ids = fields.One2many(
        comodel_name='sb.compensation',
        inverse_name='compensation_id',
        string='Compensation Details',
        required=False)
    
    # allowance and deduction fields
    pay_code = fields.Selection(string='Pay Code',
                                selection=[('trans', 'TRANS'),
                                           ('cash', 'CASH')], 
                                required=False)
    amount = fields.Float(string='Amount', required=False)
    times = fields.Float(string='Times')
    pct_from_bs = fields.Float(string="% from BS")
    formula = fields.Char(string='Formula')
    start_date = fields.Date(string='Start date')
    taxed = fields.Boolean(string="Tax")
    remarks = fields.Char(string="Remarks")
    allowance_ids = fields.One2many(comodel_name="allowance.deduction.detail", 
                                    inverse_name="allowance_id", 
                                    string="Allowance Id")

    selected_detail_id = fields.Many2one(
    comodel_name='allowance.deduction.detail', 
    string="Selected Detail", 
    help="Menyimpan ID detail yang sedang diedit"
    )


    @api.onchange('employee_id')
    def employee_onchange(self):
        for rec in self:
            if rec.employee_id:
                emp = self.env['hr.employee'].sudo().search([('id','=',rec.employee_id.id)],limit=1)
                if emp:
                    rec.nik_new = emp.nik
                    rec.nik_old = emp.nik_lama
                    rec.department_id = emp.department_id
                    rec.job_id = emp.job_id
                    rec.employement_status = emp.emp_status
                    rec.job_status = emp.job_status
                    rec.gender = emp.gender
                    rec.area_id = emp.area
                    rec.branch_id = emp.branch_id

    # # Override the create method to persist data when a new record is created
    # @api.model
    # def create(self, vals):
    #     record = super(SbEmployeeProfile, self).create(vals)
    #     if record.employee_id:
    #         emp = self.env['hr.employee'].sudo().search([('id', '=', record.employee_id.id)], limit=1)
    #         if emp:
    #             record.sudo().write({
    #                 'nik_new': emp.nik,
    #                 'nik_old': emp.nik_lama,
    #                 'department_id': emp.department_id.id,
    #                 'job_id': emp.job_id.id,
    #                 'employement_status': emp.emp_status,
    #                 'job_status': emp.job_status,
    #                 'gender': emp.gender,
    #                 'area_id': emp.area.id,
    #                 'branch_id': emp.branch_id.id
    #             })
    #     return record
    
    def unlink(self):
        return super(SbEmployeeProfile, self).unlink()
            
    # def btn_add(self):
    #     self.env['allowance.deduction.detail'].sudo().create({
    #         'allowance_id': self.id,
    #         'pay_code': self.pay_code,
    #         'amount': self.amount, 
    #         'times': self.times,
    #         'remarks': self.remarks,
    #         'formula': self.formula,
    #         'pct_from_bs': self.pct_from_bs,
    #         'start_date': self.start_date,
    #     })
        
    def btn_save(self):
        # Pastikan hanya satu record yang diproses
        self.ensure_one()

        if self.selected_detail_id:
            self.selected_detail_id.sudo().write({
                'pay_code': self.pay_code,
                'amount': self.amount, 
                'times': self.times,
                'remarks': self.remarks,
                'formula': self.formula,
                'pct_from_bs': self.pct_from_bs,
                'start_date': self.start_date,
            })
        else:
            # Jika tidak ada yang sedang diedit, buat baru
            new_detail = self.env['allowance.deduction.detail'].sudo().create({
                'allowance_id': self.id,
                'pay_code': self.pay_code,
                'amount': self.amount, 
                'times': self.times,
                'remarks': self.remarks,
                'formula': self.formula,
                'pct_from_bs': self.pct_from_bs,
                'start_date': self.start_date,
                })
            self.selected_detail_id = new_detail

        # Kosongkan input di header setelah save    
        self.pay_code = False
        self.amount = False
        self.times = False
        self.remarks = False
        self.formula = False
        self.pct_from_bs = False
        self.start_date =  False
        self.selected_detail_id = False


    def action_view_employee_profile_details(self):
        pass
        # return {
        #     'name': 'action_view_tms_details',
        #     'type': 'ir.actions.act_window',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'sb.tms.tmsentry.details',
        #     # 'views': [(False, 'form')],
        #     # 'view_id': False,
        #     'view_id': self.env.ref('sanbe_hr_tms.tmsentry_details_form_view').id,
        #     'target': 'new',
        #     'res_id': self.id,
        #     'context': False,
        # }


class AllowanceDeductionDetail(models.Model):
    _name = 'allowance.deduction.detail'
    _description = 'Allowance Deduction Detail'


    allowance_id = fields.Many2one(comodel_name="sb.employee.profile", 
                                   string="Allowance and Deduction ID",
                                   ondelete="cascade", index=True) 
    pay_code = fields.Selection(string='Pay Code',
                                selection=[('trans', 'TRANS'),
                                           ('cash', 'CASH')], 
                                required=False)
    # pay_group = fields.Char(string="Pay Group")
    # pay_type = fields.Selection(related="allowance_id.pay_type", string="Pay Type", readonly=True)
    amount = fields.Float(string='Amount', readonly=True)
    formula = fields.Char(string='Formula', readonly=True)
    times = fields.Float(string='Times', readonly=True)
    start_date = fields.Date(string='Start date')
    taxed = fields.Boolean(string="Tax")
    remarks = fields.Char(string="Remarks", readonly=True)
    pct_from_bs = fields.Float(string="% from BS")


    def btn_edit(self):
        for record in self:
            if record.allowance_id:
                record.allowance_id.write({
                    'selected_detail_id': record.id,  # Simpan ID yang sedang diedit
                    'pay_code': self.pay_code,
                    'amount': self.amount, 
                    'times': self.times,
                    'remarks': self.remarks,
                    'formula': self.formula,
                    'pct_from_bs': self.pct_from_bs,
                    'start_date': self.start_date,
                })