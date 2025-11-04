from odoo import fields, models, api, _, Command
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class SbLeaveAllocationRequest(models.Model):
    _name = 'sb.leave.allocation.request'
    _description = 'Leave Allocation Request'

    area_id = fields.Many2one('res.territory', string='Area')
    branch_ids = fields.Many2many('res.branch', 'res_branch_rel', string='All Branch', compute='_isi_semua_branch',
                                store=False)
    branch_id = fields.Many2one('res.branch', domain="[('id','in',branch_ids)]", string='Bussines Unit')
    department_id = fields.Many2one('hr.department', domain="[('branch_id','=',branch_id),('is_active','=',True)]", string='Sub Department')
    employee_id = fields.Many2one('hr.employee',domain="[('area','=',area_id), ('branch_id','=',branch_id), ('department_id','=',department_id)]", string='Employee')
    job_id = fields.Many2one('hr.job', domain="[('department_id','=',department_id)]", string='Job Position')
    employee_levels = fields.Many2one('employee.level', string='Employee Level')
    total_leave = fields.Float('Total Cuti', compute='_compute_total_leave', store=True)
    leave_tracking_ids = fields.One2many('sb.leave.tracking', 'leave_req_id', string='Leave Tracking')
    leave_benfit_ids = fields.One2many('sb.leave.benefit', 'leave_req_id', string='Leave Benfit')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('hold', 'Hold'),
    ], string='State', default='draft')

    @api.model
    def _cron_add_monthly_leave(self):
        """Run add_monthly_leave setiap tanggal 1"""
        _logger.info("Running cron: Add Monthly Leave Balance")
        try:
            self.env.cr.execute("SELECT add_monthly_leave();")
            self.env.cr.commit()
            _logger.info("add_monthly_leave() executed successfully.")
        except Exception as e:
            _logger.error("Error calling function: %s", str(e))
            raise UserError("Error executing the function: %s" % str(e))

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            if rec.employee_id:
                rec.job_id = rec.employee_id.job_id.id
                rec.employee_levels = rec.employee_id.employee_levels.id

    @api.depends('area_id')
    def _isi_semua_branch(self):
        for allrecs in self:
            databranch = []
            for allrec in allrecs.area_id.branch_id:
                mybranch = self.env['res.branch'].search([('name', '=', allrec.name)], limit=1)
                databranch.append(mybranch.id)
            allbranch = self.env['res.branch'].sudo().search([('id', 'in', databranch)])
            allrecs.branch_ids = [Command.set(allbranch.ids)]
    
    @api.depends('leave_benfit_ids.total_leave_balance', 'leave_benfit_ids.code')
    def _compute_total_leave(self):
        for rec in self:
            benefits = rec.leave_benfit_ids.filtered(lambda b: b.code == 'A1')
            if benefits:
                latest = max(benefits, key=lambda b: b.id, default=False)
                rec.total_leave = latest.total_leave_balance if latest else 0
                    
    def btn_draft(self):
        for rec in self:
            rec.state = 'draft'
    
    def btn_running(self):
        for rec in self:
            rec.state = 'running'

    def btn_hold(self):
        for rec in self:
            rec.state = 'hold'

class SbLeaveTracking(models.Model):
    _name = 'sb.leave.tracking'
    _description = 'Leave Tracking'

    leave_req_id = fields.Many2one('sb.leave.allocation.request', string='Leave Req')
    date = fields.Date('Transaction Date')
    permission_date_from = fields.Date('Permission From')
    permission_date_to = fields.Date('Permission To')
    leave_master_id = fields.Many2one('sb.leave.master', string='Permission Type')
    leave_allocation = fields.Float('Leave Adjustment')
    leave_used = fields.Float('Leave Used')
    leave_remaining = fields.Float('Remaining Leave')
    remarks = fields.Char('Remarks')
    description = fields.Text('Description')
    permission_status = fields.Selection(selection=[('draft', 'Draft'),
                                                    ('approved', "Approved"),
                                                    ('close','Close'),
                                                    ('cancel','Cancel')],
                                        string="Status")

class SbLeaveBenefit(models.Model):
    _name = 'sb.leave.benefit'
    _description = 'Leave Benefit'

    leave_req_id = fields.Many2one('sb.leave.allocation.request', string='Leave Req')
    leave_master_id = fields.Many2one('sb.leave.master', string='Name')
    name = fields.Char('Name', compute='_compute_leave_master_id', store=True)
    code = fields.Char('Code')
    description = fields.Char('Description')
    total_leave_balance = fields.Float('Total Leave Balance')
    notes = fields.Char('Keterangan')
    start_date = fields.Date('Masa Berlaku Dari')
    end_date = fields.Date('Masa Berlaku Hingga')

    @api.onchange('leave_master_id')
    def _onchange_leave_master_id(self):
        for rec in self:
            if rec.leave_master_id:
                rec.code = rec.leave_master_id.code
                rec.total_leave_balance = rec.leave_master_id.days
    
    @api.depends('leave_master_id')
    def _compute_leave_master_id(self):
        for rec in self:
            if rec.leave_master_id:
                rec.name = f'{rec.code} - {rec.leave_master_id.name}'