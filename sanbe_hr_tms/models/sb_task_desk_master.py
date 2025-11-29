from odoo import fields, models, api,  _, Command
from odoo.exceptions import ValidationError, UserError
import logging

class SbTaskDeskMaster(models.Model):
    _name = 'sb.task.desk.master'

    branch_id = fields.Many2one('res.branch', string='Business Unit')
    department_id = fields.Many2one('hr.department', string='Sub Department')
    code = fields.Char('Code')
    work_plan = fields.Text('Work Plan')
    output_plan = fields.Text('Output Plan')
    active = fields.Boolean('Active')