from odoo import models, fields, api
from odoo.exceptions import UserError

EMP_GROUP1 = [
    # ('Group1', 'Group 1 - Harian(pak Deni)'),
    ('Group2', 'Group 2 - bulanan pabrik(bu Felisca)'),
    ('Group3', 'Group 3 - Apoteker and Mgt(pak Ryadi)'),
    ('Group4', 'Group 4 - Security and non apoteker (bu Susi)'),
    ('Group5', 'Group 5 - Tim promosi(pak Yosi)'),
    ('Group6', 'Group 6 - Adm pusat(pak Setiawan)'),
    ('Group7', 'Group 7 - Tim Proyek (pak Ferry)'),
]

class EmployeeReportWizard(models.TransientModel):
    _name = 'employee.report.wizard'
    _description = 'Employee Report Wizard'

    start_date = fields.Date(string='Periode From')
    end_date = fields.Date(string='Period To')
    branch_id = fields.Many2one('res.branch',string='Bisnis Unit',domain=lambda self: [('id', 'in', self.env.user.branch_ids.ids)])
    employee_group1 = fields.Selection(selection=EMP_GROUP1,
                                       string='Employee P Group')
    employee_levels = fields.Many2one('employee.level', string='Employee Level')

    def button_export_html(self):
        self.ensure_one()

        emp_log_domain = []

        if self.start_date:
            emp_log_domain.append(('start_date', '>=', self.start_date))
        if self.end_date:
            emp_log_domain.append(('start_date', '<=', self.end_date))
        if self.branch_id:
            emp_log_domain.append(('bisnis_unit', '=', self.branch_id.id))
        if self.employee_group1:
            emp_log_domain.append(('employee_id.employee_group1', '=', self.employee_group1))
        if self.employee_levels:
            emp_log_domain.append(('employee_id.employee_levels', '=', self.employee_levels.id))

        emp_log = self.env['hr.employment.log'].search(emp_log_domain)

        return {
            'type': 'ir.actions.report',
            'report_name': 'sanbe_hr_extended.employee_report_html',
            'report_type': 'qweb-html',
            'report_file': f'Employee_Report_{self.employee_group1 or "All"}',
            'context': {
                'active_model': 'hr.employment.log',
                'active_ids': emp_log.ids,  # semua record
            },
            'data': {
                'start_date_filter': str(self.start_date or '-'),
                'end_date_filter': str(self.end_date or '-'),
                'employee_group1': self.employee_group1 or 'All',
                'employee_levels': self.employee_levels.name if self.employee_levels else 'All',
                'branch_id': (self.branch_id.name).upper() if self.branch_id else 'All',

            },
        }
    
    def button_export_excel(self):
        self.ensure_one()

        emp_log_domain = []

        if self.start_date:
            emp_log_domain.append(('start_date', '>=', self.start_date))
        if self.end_date:
            emp_log_domain.append(('start_date', '<=', self.end_date))
        if self.branch_id:
            emp_log_domain.append(('bisnis_unit', '=', self.branch_id.id))
        if self.employee_group1:
            emp_log_domain.append(('employee_id.employee_group1', '=', self.employee_group1))
        if self.employee_levels:
            emp_log_domain.append(('employee_id.employee_levels', '=', self.employee_levels.id))

        emp_log = self.env['hr.employment.log'].search(emp_log_domain)

        return {
            'type': 'ir.actions.report',
            'report_name': 'sanbe_hr_extended.employee_report_excel',
            'report_type': 'xlsx',
            'report_file': f'Employee_Report_{self.employee_group1 or "All"}',
            'context': {
                'active_model': 'hr.employment.log',
                'active_ids': emp_log.ids,  # semua record
            },
            'data': {
                'start_date_filter': str(self.start_date or '-'),
                'end_date_filter': str(self.end_date or '-'),
                'employee_group1': self.employee_group1 or 'All',
                'employee_levels': self.employee_levels.name if self.employee_levels else 'All',
                'branch_id': (self.branch_id.name).upper() if self.branch_id else 'All',

            },
        }

        