# -*- coding : utf-8 -*-

from odoo import fields, models, api, _, Command
from odoo.exceptions import ValidationError,UserError
from odoo.osv import expression
from pytz import timezone, UTC
from datetime import datetime, timedelta, time
from odoo.tools.misc import format_date


class HRPermissionEntry(models.Model):
    _name = "hr.permission.entry"
    _rec_name = 'trans_number'
    _description = 'HR Permission Entry'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    @api.depends('area_id')
    def _isi_semua_branch(self):
        for allrecs in self:
            databranch = []
            for allrec in allrecs.area_id.branch_id:
                mybranch = self.env['res.branch'].search([('name','=', allrec.name)], limit=1)
                databranch.append(mybranch.id)
            allbranch = self.env['res.branch'].sudo().search([('id','in', databranch)])
            allrecs.branch_ids =[Command.set(allbranch.ids)]

    @api.depends('area_id', 'branch_id')
    def _isi_department_branch(self):
        for allrecs in self:
            databranch = []
            allbranch = self.env['hr.department'].sudo().search([('branch_id', '=', allrecs.branch_id.id),('active','=',True)])
            allrecs.alldepartment = [Command.set(allbranch.ids)]

    area_id = fields.Many2one('res.territory', string='Area', index=True)
    branch_ids = fields.Many2many('res.branch', 'hr_permission_entry_rel', string='AllBranch', compute='_isi_semua_branch', store=False)
    alldepartment = fields.Many2many('hr.department', 'hr_employeelist_schedule_rel', string='All Department', compute='_isi_department_branch', store=False)
    branch_id = fields.Many2one('res.branch', string='Business Unit', domain="[('id','in',branch_ids)]", tracking=True,)
    department_id = fields.Many2one('hr.department', domain="[('id','in',alldepartment)]", string='Sub Department')
    employee_id = fields.Many2one('hr.employee', domain="[('area','=',area_id),('branch_id','=',branch_id)]", string='Employee Name', index=True, tracking=True)
    job_id = fields.Many2one('hr.job', string='Job Position', index=True)
    permission_date_from = fields.Date('Permission From')
    permission_date_To = fields.Date('Permission To')
    permission_status = fields.Selection(selection=[('draft', 'Draft'),
                                                    ('approved', "Approved"),
                                                    ('close','Close'),
                                                    ('cancel','Cancel by System')],
                                        string="Status", readonly=True, copy=False,
                                        index=True, tracking=3, default='draft')

    permission_time_from = fields.Float('Time From')
    permission_time_to = fields.Float('Time To')
    time_days = fields.Float('Time', compute='_get_days_duration') # re-create to accomodate table sb_leave_allocation
    time_hour = fields.Float('Hours',compute='_total_jam_ijin',store=False)
    handled_temp_to = fields.Many2one('hr.employee', string='Handled By')
    back_to_office = fields.Date('Back To Office')
    back_tooffice_time = fields.Float('Time')
    remarks = fields.Text('Remarks')
    doc_number = fields.Char('Ref Doc Number')
    trans_number = fields.Char('Transaction Number', default=lambda self: _('New'),
                               copy=False, readonly=True, tracking=True, requirement=True)
    approve1_by = fields.Many2one('hr.employee', string='Approved 1 By')
    approve1_job_title = fields.Many2one('hr.job', string='Job Title')
    approve2_by = fields.Many2one('hr.employee', string='Approved 2 By')
    approve2_job_title = fields.Many2one('hr.job', string='Job Title')
    approve3_by = fields.Many2one('hr.employee', string='Approved 3 By')
    approve3_job_title = fields.Many2one('hr.job', string='Job Title')
    is_holiday = fields.Boolean('Is Holiday', default=False)
    leave_id = fields.Many2one('hr.leave', string='Leaves ID',index=True)
    employee_company_id = fields.Many2one(related='employee_id.company_id', string="Employee Company", store=True)
    is_approved = fields.Boolean(default=False, string='is Approved')
    approved1 = fields.Boolean(default=False, string='Approved1')
    approved2 = fields.Boolean(default=False, string='Approved2')
    approved3 = fields.Boolean(default=False, string='Approved3')
    holiday_status_id = fields.Many2one("hr.leave.type", store=True, string="Permission Code",
                                        required=True, readonly=False, tracking=True)
    nik = fields.Char(related='employee_id.nik')
    periode_id = fields.Many2one('hr.opening.closing',string='Period',index=True)

    @api.depends('permission_date_from','permission_date_To')
    def _get_days_duration(self):
        date_format = "%Y-%m-%d"
        for rec in self:
            if rec.permission_date_To and rec.permission_date_from:
                ganti1 = rec.permission_date_To.strftime(date_format)
                ganti2 = rec.permission_date_from.strftime(date_format)
                tgl1 = datetime.strptime(ganti1, date_format)
                tgl2 = datetime.strptime(ganti2, date_format)
                total_days = (tgl1 - tgl2).days
                rec.time_days = total_days + 1
                #rec.time_days = (tgl1 - tgl2).days
            else:
                rec.time_days = 0

    @api.depends('permission_time_from','permission_time_to')
    def _total_jam_ijin(self):
        for allrec in self:
            if allrec.permission_time_from and allrec.permission_time_to:
                mytime = allrec.permission_time_to - allrec.permission_time_from
                allrec.time_hour = mytime
            else:
                allrec.time_hour = 0

    @api.onchange('employee_id')
    def isi_job_post(self):
        for recs in self:
            if not recs.employee_id:
                return
            recs.job_id = recs.employee_id.job_id.id
            recs.department_id = recs.employee_id.department_id.id
            recs.branch_id = recs.employee_id.branch_id.id

    def _validate_leave_alloc(self, employee, holiday_status_id, time_days):
        time_days += 1
        if holiday_status_id == 6:
            leave_alloc = self.env['sb.leave.allocation'].sudo().search([('employee_id', '=', employee)], limit=1)
            if not leave_alloc or leave_alloc.leave_remaining < time_days:
                raise ValidationError('Employee Has No Leave Allocation.\nPlease choose Leave Type: Unpaid Leave.')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # validation fullday leave
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            holiday_status_id = vals['holiday_status_id']
            time_days = vals['time_days']
            self._validate_leave_alloc(employee.id,holiday_status_id,time_days)
            # END validation fullday leave

            if vals.get('trans_number', _('New')) == _('New'):
                if 'area_id' in vals:
                    area = vals.get('area_id')
                    department = vals.get('department_id')
                    branch_id = vals.get('branch_id')
                    dt_area = self.env['res.territory'].sudo().search([('id', '=', int(area))], limit=1)
                    dept = self.env['hr.department'].sudo().search([('id', '=', int(department))], limit=1)
                    department_code = dept.department_code
                    branch = self.env['res.branch'].sudo().search([('id', '=', int(branch_id))], limit=1)
                    branch_unit_id = branch.unit_id
                    if dt_area:
                        tgl = fields.Date.today()
                        tahun = str(tgl.year)[2:]
                        bulan = str(tgl.month)
                        vals['trans_number'] = f"{tahun}/{bulan}/{branch_unit_id}/PE/{department_code}/{self.env['ir.sequence'].next_by_code('hr.permission.entry')}"
        return super(HRPermissionEntry, self).create(vals_list)

    @api.model_create_multi
    def write(self, vals_list):
        for vals in vals_list:
            # validation fullday leave
            if vals.get('holiday_status_id') == 1:
                self._validate_leave_alloc(self.employee_id.id, vals['holiday_status_id'], self.time_days)
            # END validation fullday leave
        return super(HRPermissionEntry, self).write(vals)

    @api.onchange('approved1','approved2','approved3')
    def set_approved_status(self):
        for allrec in self:
            print('param 1 ',(allrec.approved1 == True and allrec.approved2 == True))
            print('param 2 ',(allrec.approved1 == True and allrec.approved3 == True))
            print('param 3 ',(allrec.approved2 == True and allrec.approved3 == True))
            if (allrec.approved1 == True and allrec.approved2 == True) or \
                (allrec.approved1 == True and allrec.approved3 == True) or \
                (allrec.approved2 == True and allrec.approved3 == True):
                allrec.is_approved = True
            else:
                allrec.is_approved = False

    @api.onchange('approve1_by')
    def set_approved_status1(self):
        for allrec in self:
            if not allrec.approve1_by:
               return
            allrec.approve1_job_title = allrec.approve1_by.job_id.id
            
    @api.onchange('approve2_by')
    def set_approved_status2(self):
        for allrec in self:
            if not allrec.approve2_by:
               return
            allrec.approve2_job_title = allrec.approve2_by.job_id.id
            
    @api.onchange('approve3_by')
    def set_approved_status3(self):
            for allrec in self:
                if not allrec.approve3_by:
                    return
                allrec.approve3_job_title = allrec.approve3_by.job_id.id

    def btn_approve(self):
        for rec in self:
            if rec.is_approved == True:
                rec.permission_status = 'approved'
            else:
                raise UserError('Need 2 Approver check List')
            
    def btn_draft(self):
        for rec in self:
            rec.permission_status = 'draft'
            
    def btn_close(self):
        for rec in self:
            rec.permission_status = 'done'

    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type in ('tree', 'form'):
               group_name = self.env['res.groups'].search([('name','=','HRD CA')])
               cekgroup = self.env.user.id in group_name.users.ids
               if cekgroup:
                   for node in arch.xpath("//field"):
                          node.set('readonly', 'True')
                   for node in arch.xpath("//button"):
                          node.set('invisible', 'True')
                          node.set('create', '0')
        return arch, view

    # restart running number
    def _reset_sequence_permission_entry(self):
        sequences = self.env['ir.sequence'].search([('code', '=like', '%permission.entry%')])
        sequences.write({'number_next_actual': 1})


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    permition_id = fields.Many2one('hr.permission.entry',string='Permission ID', index=True)
    is_permition = fields.Boolean('Is From Permition', default=False)

    #Function to create data permition
    @api.model_create_multi
    def create(self, vals_list):
        res = super(HolidaysRequest,self).create(vals_list)
        for alldata in res:
            #Search for flagging if not from permition than create permition data
            if not alldata.is_permition:
                #Search if permition entry already create with leave
                myleave = self.env['hr.permission.entry'].sudo().search([('leave_id','=',alldata.id)])
                if not myleave:
                    #IF permition dont have leave id than we create new one
                    myleave = self.env['hr.permission.entry'].sudo().create({'area_id': alldata.employee_id.area.id,
                                                                            'branch_id': alldata.employee_id.branch_id.id,
                                                                            'employee_id': alldata.employee_id.id,
                                                                            'permission_date_from': alldata.date_from,
                                                                            'permission_date_To': alldata.date_to,
                                                                            'leave_id': alldata.id or alldata._origin.id,
                                                                            'holiday_status_id': alldata.holiday_status_id.id,
                                                                            'is_holiday': True})
                    alldata.permition_id = myleave.id
        return res

    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type in ('tree', 'form'):
               group_name = self.env['res.groups'].search([('name','=','HRD CA')])
               cekgroup = self.env.user.id in group_name.users.ids
               if cekgroup:
                   for node in arch.xpath("//field"):
                          node.set('readonly', 'True')
                   for node in arch.xpath("//button"):
                          node.set('invisible', 'True')
                          node.set('create', '0')
        return arch, view
