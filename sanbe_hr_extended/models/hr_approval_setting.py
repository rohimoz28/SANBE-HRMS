from odoo import fields, models, api, _, Command

class HrApprovalSetting(models.Model):
    _name = 'hr.approval.setting'
    _description = 'Approval Setting'

    branch_id = fields.Many2one('res.branch', string='Business Unit')
    department_id = fields.Many2one('hr.department', domain="[('branch_id','=',branch_id),('is_active','=',True)]", string='Sub Department')
    approval1_id = fields.Many2one('hr.employee', string='Approval 1', domain=lambda self: self.get_all_employee_domain())
    approval2_id = fields.Many2one('hr.employee', string='Approval 2')
    approval3_id = fields.Many2one('hr.employee', string='Approval 3')
    approval4_id = fields.Many2one('hr.employee', string='Approval 4')
    approval5_id = fields.Many2one('hr.employee', string='Approval 5')
    desc = fields.Text('Description')

    @api.model
    def get_all_employee_domain(self):
        # bypass branch rule, semua employee kelihatan
        # emp_ids = self.env['hr.employee'].sudo().search([]).ids
        # return [('id', 'in', emp_ids)]
        user = self.env.user
        import pdb
        pdb.set_trace()
        if user.has_group('sanbe_hr_extended.group_hr_approval_setting_staff') \
           or user.has_group('sanbe_hr_extended.group_hr_approval_setting_supervisor') \
           or user.has_group('sanbe_hr_extended.group_hr_approval_setting_manager'):
            # full access (tanpa filter branch)
            return [('state', '=', 'approved')]
        else:
            # tetap ikut branch_id user
            return [('state', '=', 'approved'),('branch_id', '=', user.branch_id.id)]