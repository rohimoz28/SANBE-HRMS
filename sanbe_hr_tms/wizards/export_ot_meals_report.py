from odoo import fields, models, api, _, tools, Command
from odoo.exceptions import ValidationError,UserError


class HRWizOTMeals(models.TransientModel):
    _name = 'report.ot.meals.rute.wiz'
    _description = 'HR OT Meals Rute Report Wizard'
    
    type_report = fields.Selection([('route', 'Route'), ('meal', 'Meals'), ('cash_meal', 'Cash Meals')], string='Report Type', required=True, default='route')
    branch_id = fields.Many2one('res.branch', string='Bisnis Unit', default=lambda self: self.env.user.branch_id.id)
    date_from = fields.Date(string='Date From', required=True, default=lambda self: fields.Date.today())
    date_to = fields.Date(string='Date To', required=True,default=lambda self: fields.Date.today())
    department_id = fields.Many2one('hr.department', string='Sub Department', 
        domain=lambda self: self._get_departments_domain(),
        options="{'no_create': True}"
    )
    # status_ids = fields.Many2many('ot.status', string='Statuses', domain=[('id', '>=', 6)], required=True)
    
    
    def _get_departments_domain(self):
        department_ids = []
        branch_id = self.branch_id.id or self.env.user.branch_id.id
        if branch_id:
            department_ids = self.env['hr.overtime.employees'].search([('branch_id', '=', branch_id)]).mapped('department_id.id')
        else:
            department_ids = self.env['hr.overtime.employees'].search([]).mapped('department_id.id')
        return [('id', 'in', department_ids)]
                
    def button_export_pdf(self):
        self.ensure_one()
        ot_attendance_domain = [
            ('branch_id', '=', self.branch_id.id),
            ('state', 'in', (
                'approved_plan_mgr', 'approved_plan_pm',
                'approved_plan_hcm', 'verification',
                'approved', 'completed', 'done'
            ))]
        

        if self.type_report == 'route':
            ot_attendance_domain.append(('route_id', '!=', False))
        if self.type_report == 'meal':
            ot_attendance_domain.append(('meals', '!=', False))
            ot_attendance_domain.append(('meals_cash', '=', False))
        elif self.type_report == 'cash_meal':
            ot_attendance_domain.append(('meals_cash', '!=', False))
            ot_attendance_domain.append(('meals', '=', False))
        if self.date_from and self.date_to and self.date_from <= self.date_to:
            ot_attendance_domain += [
                ('plann_date_from', '>=', self.date_from),
                ('plann_date_from', '<=', self.date_to)
            ]

        if self.department_id:
            ot_attendance_domain.append(('departmenth_id', '=', self.department_id.id))

        ot_attendance = self.env['hr.overtime.employees'].search(ot_attendance_domain)
        
        if not ot_attendance:
            raise UserError(_("Tidak Ada Data Record Dari department yang dipilih"))
        if self.type_report == 'route': 
            return {
            'type': 'ir.actions.report',
            'report_name': 'sanbe_hr_tms.report_ot_route_html',
            'report_type': 'qweb-html',
            'report_file': f'Rekap_Overtime_Route_{self.department_id.complete_name or "All"}',
            'context': {
                'active_model': 'hr.overtime.employees',
                'active_ids': ot_attendance.ids,  # semua record
                }
            }
        elif self.type_report == 'meal':
            return {
                'type': 'ir.actions.report',
                'report_name': 'sanbe_hr_tms.report_ot_meals_html',
                'report_type': 'qweb-html',
                'report_file': f'Rekap_Overtime_Meals_{self.department_id.complete_name or "All"}',
                'context': {
                    'active_model': 'hr.overtime.employees',
                    'active_ids': ot_attendance.ids,
                }
            }
        elif self.type_report == 'cash_meal':
            return {
                'type': 'ir.actions.report',
                'report_name': 'sanbe_hr_tms.report_ot_meals_cash_html',
                'report_type': 'qweb-html',
                'report_file': f'Rekap_Overtime_Cash_Meals_{self.department_id.complete_name or "All"}',
                'context': {
                    'active_model': 'hr.overtime.employees',
                    'active_ids': ot_attendance.ids,
                }
            }