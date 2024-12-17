from odoo import fields, models, api
import logging


class SbLeaveAllocation(models.Model):
    _name = 'sb.leave.allocation'
    _description = 'Table For Populating Employee Leave Allocation'

    leave_allocation = fields.Float(string='Leave Allocation', required=False, default=0)
    leave_remaining= fields.Float(string='Remaining Leave', required=False, default=0)
    leave_used= fields.Float(string='Leave Used', required=False, default=0)
    area_id = fields.Many2one('res.territory', string='Area ID', index=True)
    branch_id = fields.Many2one('res.branch',string='Bussines Unit', tracking=True)
    department_id = fields.Many2one('hr.department', string='Sub Department', index=True)
    job_id = fields.Many2one('hr.job', string='Job Position', index=True)
    employee_id = fields.Many2one('hr.employee', string='Employee Name', index=True, tracking=True)

    def _cron_populate_leave_alloc(self):
        _logger = logging.getLogger(__name__)
        try:
            self.env.cr.execute("CALL procedure_leave_alloc()")
            self.env.cr.commit()
            _logger.info("Cron For Populate Leave Allocation is Running Successfully.")
        except Exception as e:
            self.env.cr.rollback()
            _logger.error("Error running Cron for Populate Leave Allocation: %s", str(e))
