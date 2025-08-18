from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError
from datetime import date

class HrPensionMonitoring(models.Model):
    _inherit = 'hr.employee'

    pension_date = fields.Date('Pension Date')
    retire_age = fields.Integer('Retire Age')
    pension_state = fields.Selection([
        ('expired', 'Expired'),
        ('running', 'Running')
    ], string='Pension State', compute='_pension_state_compute', store=False)
    emp_status_id = fields.Many2one('hr.emp.status', string='Employment Status')

    @api.depends('pension_date')
    def _pension_state_compute(self):
        for rec in self:
            if rec.pension_date:
                if date.today() < rec.pension_date:
                    rec.pension_state = 'running'
                else:
                    rec.pension_state = 'expired'
            else:
                rec.pension_state = False