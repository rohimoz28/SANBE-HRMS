from odoo import fields, models, api
import logging


class SbLeaveAllocation(models.Model):
    _name = 'sb.leave.allocation'
    _description = 'Table For Populating Employee Leave Allocation'

    leave_allocation = fields.Float(string='Leave Allocation', required=False, default=0)
    leave_remaining= fields.Float(string='Remaining Leave', compute='_compute_leave_remaining', store=True)
    leave_used= fields.Float(string='Leave Used', required=False, default=0)
    area_id = fields.Many2one('res.territory', string='Area', index=True)
    branch_id = fields.Many2one('res.branch',string='Business Unit', tracking=True)
    department_id = fields.Many2one('hr.department', string='Sub Department', index=True)
    job_id = fields.Many2one('hr.job', string='Job Position', index=True)
    employee_id = fields.Many2one('hr.employee', string='Employee Name', index=True, tracking=True)
    date = fields.Date(string='Date', tracking=True)
    remarks = fields.Char(string='Remarks', tracking=True)
    description = fields.Text(string='Description', tracking=True)

    @api.depends('employee_id', 'leave_allocation', 'leave_used')
    def _compute_leave_remaining(self):
        for rec in self:
            if rec.employee_id:
                last_leave = self.env['sb.leave.allocation'].search([
                    ('employee_id', '=', rec.employee_id.id)
                ], order='id desc', limit=1)

                if last_leave:
                    rec.leave_remaining = last_leave.leave_remaining

                    if rec.leave_allocation > 0:
                        rec.leave_used = 0
                        rec.leave_remaining = last_leave.leave_remaining + rec.leave_allocation
                    if rec.leave_used > 0:
                        rec.leave_allocation = 0
                        rec.leave_remaining = last_leave.leave_remaining - rec.leave_used

                else:
                    if rec.leave_allocation > 0:
                        rec.leave_used = 0
                        rec.leave_remaining = rec.leave_allocation
                    else:
                        rec.leave_remaining = 0

                    if rec.leave_used > 0:
                        rec.leave_allocation = 0
                        rec.leave_remaining = rec.leave_remaining - rec.leave_used

                if rec.leave_remaining < 0:
                    rec.leave_remaining = 0
                elif rec.leave_remaining > 16:
                    rec.leave_remaining = 16


    def _cron_populate_leave_alloc(self):
        _logger = logging.getLogger(__name__)
        try:
            self.env.cr.execute("CALL procedure_leave_alloc()")
            self.env.cr.commit()
            _logger.info("Cron For Populate Leave Allocation is Running Successfully.")
        except Exception as e:
            self.env.cr.rollback()
            _logger.error("Error running Cron for Populate Leave Allocation: %s", str(e))
