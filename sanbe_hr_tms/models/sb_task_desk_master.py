from odoo import fields, models, api,  _, Command
from odoo.exceptions import ValidationError, UserError
import logging

class SbTaskDeskMaster(models.Model):
    _name = 'sb.task.desk.master'

    name = fields.Char(string='Task Desk Code', copy=False, readonly=True, tracking=True, requirement=True)
    branch_id = fields.Many2one('res.branch', string='Business Unit')
    department_id = fields.Many2one('hr.department', string='Sub Department', domain="[('branch_id','=',branch_id),('is_active','=',True)]")
    code = fields.Char('Code')
    work_plan = fields.Text('Work Plan')
    output_plan = fields.Text('Output Plan')
    active = fields.Boolean('Active')

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', "Task desk code must be unique, this one is already assigned to another record."),
    ]

    def _get_branch_sequence(self, branch):
        """Fungsi untuk create/return sequence per-branch"""
        seq_code = f'hr.empgroup.branch.{branch.id}'

        seq = self.env['ir.sequence'].sudo().search([
            ('code', '=', seq_code)
        ], limit=1)

        if not seq:
            seq = self.env['ir.sequence'].sudo().create({
                'name': f'HR Emp Group {branch.name}',
                'code': seq_code,
                'padding': 4,
                'number_next': 1,
                'company_id': False,
            })

        return seq
    
    @api.model_create_multi
    def create(self, vals_list):
        """generate kode sequencce dengan format branch_code - sequence number"""
        for vals in vals_list:
            if not vals.get('name'):
                branch = self.env['res.branch'].sudo().browse(vals.get('branch_id'))

                if branch:
                    seq = self._get_branch_sequence(branch)
                    seq_number = seq.next_by_id()

                    vals['name'] = f"{branch.branch_code} - {seq_number}"
        
        res = super(SbTaskDeskMaster,self).create(vals_list)
        return res