from odoo import fields, models, api, _, tools, Command
from odoo.exceptions import ValidationError,UserError

# TMS_OVERTIME_STATE = [
#     ('draft', 'Draft'),
#     ('approved_mgr', "Approved By MGR"),
#     ('approved_pmr', "Approved By PMR"),
#     ('approved_plan_spv', "Appv Plan By SPV"),
#     ('approved_plan_mgr', "Appv Plan By MGR"),
#     ('approved_plan_pm', "Appv Plan By PM"),
#     ('approved_plan_hcm', "Appv Plan By HCM"),
#     ('verification', 'Verif by SPV'),
#     ('approved', 'Approved By HCM'),
#     ('completed', 'Completed HCM'),
#     ('done', "Close"),
#     ('reject', "Reject"),
# ]


# class OTStatus(models.Model):
#     _name = 'ot.status'
#     _description = 'OT Status'

#     code = fields.Char(string='Code', required=True)
#     name = fields.Char(string='Name', required=True)
#     active = fields.Boolean(default=True)

#     _sql_constraints = [
#         ('code_uniq', 'unique(code)', 'Code must be unique.'),
#     ]
    
    
#     def name_get(self):
#         return [(rec.id, rec.name) for rec in self]

class HRWizOTMeals(models.TransientModel):
    _name = 'report.ot.meals.rute.wiz'
    _description = 'HR OT Meals Rute Report Wizard'
    
    
    
    type_report = fields.Selection([('route', 'Route'), ('meal', 'Meals')], string='Report Type', required=True, default='route')
    branch_id = fields.Many2one('res.branch', string='Bisnis Unit', default=lambda self: self.env.user.branch_id.id)
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
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
            ))
        ]

        if self.type_report == 'route':
            ot_attendance_domain.append(('route_id', '!=', False))
        if self.type_report == 'meal':
            ot_attendance_domain.append(('meals', 'ilike', 'dine'))
        if self.date_from and self.date_to and self.date_from < self.date_to:
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
        else:
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
