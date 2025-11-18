from odoo import fields, models, tools, api, _

class SbViewHrEmployee(models.Model):
    _auto = False
    _name = 'sb.view.hr.employee'
    _description = 'View HR Employee'
    _order = 'name'

    id = fields.Integer('ID', required=True)
    name = fields.Char('Name')
    area_id = fields.Many2one('res.territory', string='Area')
    branch_id = fields.Many2one('res.branch', string='Business Unit')
    department_id = fields.Many2one('hr.department', string='Sub Department')
    job_id = fields.Many2one('hr.job', string='Job Position')
    nik = fields.Char('NIK')
    user_id = fields.Many2one('res.users', string='user')
    state = fields.Selection([
        ('draft', "Draft"),
        ('req_approval', 'Request For Approval'),
        ('rejected', 'Rejected'),
        ('inactive', 'Inactive'),
        ('approved', 'Approved'),
        ('hold', 'Hold'),
    ], string="Status")
    active = fields.Boolean('Active')
    job_status = fields.Selection([
        ('permanent', 'Permanent'),
        ('contract', 'Contract'),
        ('outsource', 'Outsource'),
        ('visitor', 'Visitor'),
        ('mitra', 'Mitra'),
        ('tka', 'TKA'),
    ], string='Job Status')
    emp_status = fields.Selection([
        ('probation', 'Probation'),
        ('confirmed', 'Confirmed'),
        ('end_contract', 'End Of Contract'),
        ('resigned', 'Resigned'),
        ('retired', 'Retired'),
        ('transfer_to_group', 'Transfer To Group'),
        ('terminated', 'Terminated'),
        ('pass_away', 'Pass Away'),
        ('long_illness', 'Long Illness')
    ], string='Employment Status')
    employee_group1 = fields.Selection([
        ('Group2', 'Group 2 - bulanan pabrik(bu Felisca)'),
        ('Group3', 'Group 3 - Apoteker and Mgt(pak Ryadi)'),
        ('Group4', 'Group 4 - Security and non apoteker (bu Susi)'),
        ('Group5', 'Group 5 - Tim promosi(pak Yosi)'),
        ('Group6', 'Group 6 - Adm pusat(pak Setiawan)'),
        ('Group7', 'Group 7 - Tim Proyek (pak Ferry)'),
    ], string='Employee P Group')
    no_npwp = fields.Char('No NPWP')
    no_ktp = fields.Char('NO KTP')
    identification_id = fields.Char('Identification ID')
    nik_lama = fields.Char('NIK LAMA')
    parent_id = fields.Many2one('hr.employee', string='Immediate Superior')
    join_date = fields.Date('Join Date')
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('separate', 'Separate'),
    ], string='Marital')
    employee_levels = fields.Many2one('employee.level', string='Employee Level')
    birthday = fields.Date('Birthday')
    work_unit = fields.Char('Work Unit')
    coach_id = fields.Many2one('hr.employee', string='Work Unit Superior')
    contract_id = fields.Many2one('hr.contract', string='Contract')
    contract_datefrom = fields.Date('Contract From')
    contract_dateto = fields.Date('Contract To')
    employee_id = fields.Char('Employee ID')
    join_date_contract = fields.Date('Join Date Contract')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                select 
                    he.id as id, 
                    he.name as name, 
                    he.area as area_id, 
                    he.branch_id, 
                    he.department_id, 
                    he.job_id, 
                    he.nik,
                    he.user_id,
                    he.state,
                    he.active,
                    he.job_status,
                    he.emp_status,
                    he.employee_group1,
                    he.no_npwp,
                    he.no_ktp,
                    he.identification_id,
                    he.nik_lama,
                    he.parent_id,
                    he.join_date,
                    he.marital,
                    he.employee_levels,
                    he.birthday,
                    he.work_unit,
                    he.coach_id,
                    he.contract_id,
                    he.contract_datefrom,
                    he.contract_dateto,
                    he.employee_id,
                    he.join_date_contract
                from hr_employee he 
        )
        """ % (self._table, ))