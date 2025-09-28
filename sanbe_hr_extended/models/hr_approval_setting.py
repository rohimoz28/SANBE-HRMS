from odoo import fields, models, api, _, Command

class HrApprovalSetting(models.Model):
    _name = 'hr.approval.setting'
    _description = 'Approval Setting'

    branch_id = fields.Many2one('res.branch', string='Business Unit')
    department_id = fields.Many2one('hr.department', domain="[('branch_id','=',branch_id),('is_active','=',True)]", string='Sub Department')
    approval1_id = fields.Many2one('hr.employee', string='Approval 1', domain="[('id', 'in', allowed_employee_ids)]")
    approval2_id = fields.Many2one('hr.employee', string='Approval 2', domain="[('id', 'in', allowed_employee_ids)]")
    approval3_id = fields.Many2one('hr.employee', string='Approval 3', domain="[('id', 'in', allowed_employee_ids)]")
    approval4_id = fields.Many2one('hr.employee', string='Approval 4', domain="[('id', 'in', allowed_employee_ids)]")
    approval5_id = fields.Many2one('hr.employee', string='Approval 5', domain="[('id', 'in', allowed_employee_ids)]")
    desc = fields.Text('Description')
    allowed_employee_ids = fields.Many2many(
        'hr.employee',
        compute='_compute_allowed_employee_ids',
        store=False, # Tidak disimpan di database
    )

    @api.depends('branch_id')
    def _compute_allowed_employee_ids(self):
        all_approved_employees = self.env['hr.employee'].sudo().search([('state', '=', 'approved')])
        allowed_ids = all_approved_employees.ids

        for record in self:
            record.allowed_employee_ids = [(6, 0, allowed_ids)]