from odoo import fields, models, api, _, Command
from odoo.exceptions import ValidationError, UserError

class HrApprovalSetting(models.Model):
    _name = 'hr.approval.setting'
    _description = 'Approval Setting'

    branch_id = fields.Many2one('res.branch', string='Business Unit')
    department_id = fields.Many2one('hr.department', domain="[('branch_id','=',branch_id),('is_active','=',True)]", string='Sub Department')
    model = fields.Selection([
        ('overtime_request', 'Overtime Request'),
        ('permission_entry', 'Permission Entry')
    ], string='Model')
    approval1_ids = fields.Many2many(
        comodel_name='sb.view.hr.employee',
        relation='approval_setting_view_employee_rel_1',
        column1='setting_id',   
        column2='employee_id',
        string='Approval 1',
        domain=[('state', '=', 'approved'), ('active', '=', True)]
    )
    approval2_ids = fields.Many2many(
        comodel_name='sb.view.hr.employee',
        relation='approval_setting_view_employee_rel_2',
        column1='setting_id',
        column2='employee_id',
        string='Approval 2',
        domain=[('state', '=', 'approved'), ('active', '=', True)]
    )
    approval3_ids = fields.Many2many(
        comodel_name='sb.view.hr.employee',
        relation='approval_setting_view_employee_rel_3',
        column1='setting_id',
        column2='employee_id',
        string='Approval 3',
        domain=[('state', '=', 'approved'), ('active', '=', True)]
    )
    approval4_ids = fields.Many2many(
        comodel_name='sb.view.hr.employee',
        relation='approval_setting_view_employee_rel_4',
        column1='setting_id',
        column2='employee_id',
        string='Approval 4',
        domain=[('state', '=', 'approved'), ('active', '=', True)]
    )
    approval5_ids = fields.Many2many(
        comodel_name='sb.view.hr.employee',
        relation='approval_setting_view_employee_rel_5',
        column1='setting_id',
        column2='employee_id',
        string='Approval 5',
        domain=[('state', '=', 'approved'), ('active', '=', True)]
    )
    desc = fields.Text('Description')

    @api.constrains('branch_id','department_id','model')
    def duplicate_approval_check(self):
        for rec in self:
            model_display_name = dict(rec._fields['model'].selection).get(rec.model)
            duplicate_approval = self.search([
                ('id', '!=', rec.id),
                ('branch_id','=',rec.branch_id.id),
                ('department_id','=',rec.department_id.id),
                ('model','=',rec.model),
            ])
            if duplicate_approval:
                raise ValidationError(
                _("Duplicate approval setting found.\n"
                  "Business Unit: %s\n"
                  "Sub Department: %s\n"
                  "Model: %s\n") % (
                    rec.branch_id.name,
                    rec.department_id.name,
                    model_display_name,
                )
            )
