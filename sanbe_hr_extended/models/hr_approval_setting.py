from odoo import fields, models, api, _, Command

class HrApprovalSetting(models.Model):
    _name = 'hr.approval.setting'
    _description = 'Approval Setting'

    branch_id = fields.Many2one('res.branch', string='Business Unit')
    department_id = fields.Many2one('hr.department', domain="[('branch_id','=',branch_id),('is_active','=',True)]", string='Sub Department')
    approval1_id = fields.Many2one('hr.employee', string='Approval 1')
    approval2_id = fields.Many2one('hr.employee', string='Approval 2')
    approval3_id = fields.Many2one('hr.employee', string='Approval 3')
    approval4_id = fields.Many2one('hr.employee', string='Approval 4')
    approval5_id = fields.Many2one('hr.employee', string='Approval 5')
    desc = fields.Text('Description')