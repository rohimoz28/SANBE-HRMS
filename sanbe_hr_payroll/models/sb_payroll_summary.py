from odoo import fields, models, api

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

class SbPayrollSummary(models.Model):
    _name = 'sb.payroll.summary'
    _description = 'Payroll Summary'

    @api.model
    def _selection1(self):
        return EMP_GROUP1

    employee_group1 = fields.Selection(selection=_selection1, string='Employee P Group')
    employee_id = fields.Many2one('hr.employee', index=True)
    nik = fields.Char(
        string='NIK',
        required=False)
    basic_salary = fields.Float(
        string='Basic Salary',
        required=False)
    overtime = fields.Float(
        string='Overtime',
        required=False)
    allowance = fields.Float(
        string='T. Allowance',
        required=False)
    deduction = fields.Float(
        string='T. Deduction',
        required=False)
    net_salary = fields.Float(
        string='T. Net Salary',
        required=False)

    def action_view_payroll_summary(self):
        pass