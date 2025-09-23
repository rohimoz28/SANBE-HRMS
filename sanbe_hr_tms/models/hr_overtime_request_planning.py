# -*- coding : utf-8 -*-
#################################################################################
# Author    => Albertus Restiyanto Pramayudha
# email     => xabre0010@gmail.com
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA
#################################################################################

from odoo import fields, models, api, _, Command
from odoo.exceptions import ValidationError,UserError
from odoo.osv import expression
import pytz
from datetime import datetime,time, timedelta
import logging
_logger = logging.getLogger(__name__)

TMS_OVERTIME_STATE = [
    ('draft', 'Draft'),
    ('approved_mgr', "Approved By MGR"),
    ('approved_pmr', "Approved By PMR"),
    ('approved_plan_spv', "Appv Plan By SPV"),
    ('approved_plan_mgr', "Appv Plan By MGR"),
    ('approved_plan_pm', "Appv Plan By PM"),
    ('approved_plan_hcm', "Appv Plan By HCM"),
    ('verification', 'Verif by SPV'),
    ('approved', 'Approved By HCM'),
    ('completed', 'Completed HCM'),
    ('done', "Close"),
    ('reject', "Reject"),
]

OT_HOURS_SELECTION = [
    ('h_morning', "H - Lembur Pagi"),
    ('h_afternoon', "H - Lembur Siang"),
    ('h_night', "H - Lembur Malam"),
    ('r_s1', "R - Shift 1"),
    ('r_s2', "R - Shift 2"),
    ('r_s3', "R - Shift 3"),
    ('others', "Others"),
]


class HREmpOvertimeRequest(models.Model):
    _name = "hr.overtime.planning"
    _description = 'HR Employee Overtime Planning Request'
    _rec_name = 'name'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    # def _get_active_periode_from(self):
    #     mycari = self.env['hr.opening.closing'].sudo().search([('isopen','=',True)],limit=1)
    #     return mycari.open_periode_from or False

    # def _get_active_periode_to(self):
    #     mycari = self.env['hr.opening.closing'].sudo().search([('isopen','=',True)],limit=1)
    #     return mycari.open_periode_to or False

    @api.depends('area_id')
    def _isi_semua_branch(self):
        for allrecs in self:
            user_branch_ids = self.env.user.branch_ids.ids
            allrecs.branch_ids = [(6, 0, user_branch_ids)]
            # databranch = []
            # for allrec in allrecs.area_id.branch_id:
            #     mybranch = self.env['res.branch'].search([('name', '=', allrec.name)], limit=1)
            #     databranch.append(mybranch.id)
            # allbranch = self.env['res.branch'].sudo().search([('id', 'in', databranch)])
            # allrecs.branch_ids = [Command.set(allbranch.ids)]
            
    @api.depends('area_id','branch_id')
    def _isi_department_branch(self):
        for allrecs in self:
            allbranch = self.env['hr.department'].sudo().search([('branch_id','=', allrecs.branch_id.id)])
            allrecs.alldepartment =[Command.set(allbranch.ids)]

    name = fields.Char('Planning Request',default=lambda self: _('New'),
       copy=False, readonly=True, tracking=True, requirement=True)
    request_date = fields.Date('Planning Request Create', default=fields.Date.today(), readonly=True)
    area_id = fields.Many2one('res.territory', domain=lambda self: [('id', '=', self.env.user.area.id)], string='Area', index=True, required=True, default=lambda self: self._default_area_id())
    branch_ids = fields.Many2many('res.branch', 'res_branch_rel', string='AllBranch', compute='_isi_semua_branch',
                                  store=False)

    branch_id = fields.Many2one('res.branch', string='Business Unit', index=True, domain="[('id','in',branch_ids)]", default=lambda self: self._default_branch_id())
    alldepartment = fields.Many2many('hr.department','hr_department_plan_ot_rel', string='All Department',compute='_isi_department_branch',store=False)
    department_id = fields.Many2one('hr.department',domain="[('id','in',alldepartment)]",string='Sub Department', default=lambda self: self._default_department_id())
    periode_from = fields.Date('Tanggal OT Dari',default=fields.Date.today)
    periode_to = fields.Date('Tanggal OT Hingga',default=fields.Date.today)
    approve1 = fields.Boolean('Supervisor Department',default=False)
    approve2 = fields.Boolean('Manager Department',default=False)
    approve3 = fields.Boolean('HCM Department',default=False)
    approve4 = fields.Boolean('Plan Manager',default=False)
    state = fields.Selection(
        selection=TMS_OVERTIME_STATE,
        string="TMS Overtime Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')
    # periode_id = fields.Many2one('hr.opening.closing',string='Period',index=True, required=True)
    hr_ot_planning_ids = fields.One2many('hr.overtime.employees','planning_id',auto_join=True,index=True,required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee',domain="[('area','=',area_id),('branch_id','=',branch_id),('state','=','approved')]")
    company_id = fields.Many2one('res.company', string="Company Name", index=True)
    request_day_name = fields.Char('Request Day Name', compute='_compute_req_day_name', store=True)
    count_record_employees = fields.Integer(string="Total Employees on The List", compute="_compute_record_employees", store=True)
    ot_type = fields.Selection([('regular','Regular'),('holiday','Holiday')], string='Ot Type')
    supervisor_id = fields.Many2one(
        'hr.employee',
        string='Supervisor',
        # domain="[('area','=',area_id),('branch_id','=',branch_id),('department_id','=',department_id),('state','=','approved')]"
        )
    manager_id = fields.Many2one(
        'hr.employee',
        string='Manager',
        # domain="[('area','=',area_id),('branch_id','=',branch_id),('department_id','=',department_id),('state','=','approved')]"
        )
    plan_manager_id = fields.Many2one(
        'hr.employee',
        string='Plan Manager',
        # domain="[('area','=',area_id),('branch_id','=',branch_id),('state','=','approved')]"
        )
    hcm_id = fields.Many2one(
        'hr.employee',
        string='HCM',
        # domain="[('state','=','approved')]"
        )
    is_supervisor_user = fields.Boolean(compute='_compute_is_supervisor_user')
    is_manager_user = fields.Boolean(compute='_compute_is_manager_user')
    is_plan_manager_user = fields.Boolean(compute='_compute_is_plan_manager_user')
    is_hcm_user = fields.Boolean(compute='_compute_is_hcm_user')
    time_from_char = fields.Char()
    time_to_char = fields.Char()
    default_ot_hours = fields.Selection(
        selection=OT_HOURS_SELECTION,
        string='Default Jam OT')

    def _default_area_id(self):
        emp = self.env.user.employee_id
        return emp.area.id if emp and emp.area else False

    def _default_branch_id(self):
        emp = self.env.user.employee_id
        return emp.branch_id.id if emp and emp.branch_id else False

    def _default_department_id(self):
        emp = self.env.user.employee_id
        return emp.department_id.id if emp and emp.department_id else False

    @api.depends('supervisor_id.user_id')
    def _compute_is_supervisor_user(self):
        for rec in self:
            rec.is_supervisor_user = (rec.supervisor_id.user_id == self.env.user)

    @api.depends('manager_id.user_id')
    def _compute_is_manager_user(self):
        for rec in self:
            rec.is_manager_user = (rec.manager_id.user_id == self.env.user)

    @api.depends('plan_manager_id.user_id')
    def _compute_is_plan_manager_user(self):
        for rec in self:
            rec.is_plan_manager_user = (rec.plan_manager_id.user_id == self.env.user)

    @api.depends('hcm_id.user_id')
    def _compute_is_hcm_user(self):
        for rec in self:
            rec.is_hcm_user = (rec.hcm_id.user_id == self.env.user)

    @api.constrains('supervisor_id')
    def _constrains_supervisor_id(self):
        for rec in self:
            if rec.supervisor_id and not rec.supervisor_id.user_id:
                raise ValidationError(f"Supervisor: {rec.supervisor_id.name} does not have login access.")

    @api.constrains('manager_id')
    def _constrains_manager_id(self):
        for rec in self:
            if rec.manager_id and not rec.manager_id.user_id:
                raise ValidationError(f"Manager: {rec.manager_id.name} does not have login access.")

    @api.constrains('plan_manager_id')
    def _constrains_plan_manager_id(self):
        for rec in self:
            if rec.plan_manager_id and not rec.plan_manager_id.user_id:
                raise ValidationError(f"Plan Manager: {rec.plan_manager_id.name} does not have login access.")

    @api.constrains('hcm_id')
    def _constrains_hcm_id(self):
        for rec in self:
            if rec.hcm_id and not rec.hcm_id.user_id:
                raise ValidationError(f"HCM: {rec.hcm_id.name} does not have login access.")

    @api.onchange('periode_id')
    def _onchange_periode_id(self):
        """Update area_id and branch_id based on periode_id and apply dynamic domain."""
        if self.periode_id:
            # Set default values for area_id and branch_id
            self.area_id = self.periode_id.area_id.id if self.periode_id.area_id else False
            self.branch_id = self.periode_id.branch_id.id if self.periode_id.branch_id else False
            # import pdb
            # pdb.set_trace()
            # self.area_id = [('id', '=', self.periode_id.area_id.id)]
            # self.branch_id = [('id', '=', self.periode_id.branch_id.id)]
            # _logger.info("Domain for area_id: %s", self.area_id)
            # _logger.info("Domain for branch_id: %s", self.branch_id)

            # Apply dynamic domains for area_id and branch_id
            # return {
            #     'domain': {
            #         'area_id': domain_area,
            #         'branch_id': domain_branch,
            #     }
            # }
        else:
            self.area_id = False
            self.branch_id = False
            return {
                'domain': {
                    'area_id': [],
                    'branch_id': [],
                }
            }

    # restart running number
    def _reset_sequence_overtime_employees(self):
        sequences = self.env['ir.sequence'].search([('code', '=like', '%hr.overtime.planning%')])
        sequences.write({'number_next_actual': 1})

    def unlink(self):
        for record in self:
            # Check if there are any detail records linked to this master record
            if record.hr_ot_planning_ids:
                raise ValidationError(
                    _("You cannot delete this record as it has related detail records.")
                )
        return super(HREmpOvertimeRequest, self).unlink()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                area_id = vals.get('area_id')
                branch_id = vals.get('branch_id')

                # Fetch area and branch if missing
                if not area_id or not branch_id:
                    periode_id = vals.get('periode_id')
                    if periode_id:
                        periode = self.env['hr.opening.closing'].sudo().search([('id', '=', int(periode_id))], limit=1)
                        if periode:
                            area_id = periode.area_id.id
                            branch_id = periode.branch_id.id
                            vals['area_id'] = area_id
                            vals['branch_id'] = branch_id

                # Fetch related records for generating 'name'
                department_id = vals.get('department_id')
                area = self.env['res.territory'].sudo().search([('id', '=', int(area_id))], limit=1)
                department = self.env['hr.department'].sudo().search([('id', '=', int(department_id))], limit=1)
                branch = self.env['res.branch'].sudo().search([('id', '=', int(branch_id))], limit=1)

            # Validate necessary data and generate 'name'
            if area and department and branch:
                department_code = department.department_code
                branch_unit_id = branch.unit_id
                tgl = fields.Date.today()
                tahun = str(tgl.year)[2:]
                bulan = str(tgl.month)
                sequence_code = self.env['ir.sequence'].next_by_code('hr.overtime.planning')
                vals['name'] = f"{tahun}/{bulan}/{branch_unit_id}/RA/{department_code}/{sequence_code}"
                # res = super(HREmpOvertimeRequest,self).create(vals_list)

        return super(HREmpOvertimeRequest, self).create(vals_list)
    
    def btn_approved(self):
        for rec in self:
            rec.state = 'approved'
            # if rec.approve1 == True and rec.approve2 == True and rec.approve3 == True and rec.approve4 == True:
            #     rec.state = 'approved'
            # else:
            #     raise UserError('Approve Not Complete')
    
    def btn_done(self):
        for rec in self:
            rec.state = 'done'

    @api.model
    def _get_visible_states(self):
        """Menentukan state mana yang akan ditampilkan berdasarkan state saat ini"""
        self.ensure_one()
        if self.state == '':
            return 'draft,approved_mgr,done,reject'
        elif self.state == 'draft':
            return 'draft,approved_mgr,done,reject'
        elif self.state == 'approved_mgr':
            # return 'draft,approved_mgr,done,reject'
            return 'approved_mgr'
        elif self.state == 'approved_pmr':
            # return 'draft,approved_pmr,done,reject'
            return 'approved_pmr'
        elif self.state == 'approved':
            return 'draft,approved,done,reject'
        elif self.state == 'verification':
            return 'draft,verification,done,reject'
        elif self.state == 'completed':
            return 'draft,completed,done,reject'
        elif self.state == 'done':
            return 'draft,done,reject'
        elif self.state == 'reject':
            return 'draft,done,reject'
        else:
            return 'draft,approved,verification,completed,done,reject'

    # def btn_approved_mgr(self):
    #     for rec in self:
    #         rec.state = 'approved_mgr'
            
    # def btn_approved_pmr(self):
    #     for rec in self:
    #         rec.state = 'approved_pmr'
    
    def btn_reject(self):
        for rec in self:
            rec.state = 'reject'
    
    def btn_backdraft(self):
        for rec in self:
            rec.state = 'draft'

    def btn_verification(self):
        for rec in self:
            rec.state = 'verification'
    
    def btn_completed(self):
        for rec in self:
            rec.state = 'completed'
    
    def btn_plan_spv(self):
        for rec in self:
            rec.state = 'approved_plan_spv'
    
    def btn_plan_mgr(self):
        for rec in self:
            rec.state = 'approved_plan_mgr'
    
    def btn_plan_pm(self):
        for rec in self:
            rec.state = 'approved_plan_pm'
    
    def btn_plan_hcm(self):
        for rec in self:
            rec.state = 'approved_plan_hcm'

    def btn_print_pdf(self):
        if not self.hr_ot_planning_ids:
            raise UserError("Tidak ada data perencanaan lembur untuk dicetak.")
        first_line = self.hr_ot_planning_ids[0]
        self.time_from_char = '%02d:%02d' % (int(first_line.approve_time_from), int((first_line.approve_time_from % 1) * 60))
        self.time_to_char = '%02d:%02d' % (int(first_line.approve_time_to), int((first_line.approve_time_to % 1) * 60))
        self.default_ot_hours = first_line.default_ot_hours
        return self.env.ref('sanbe_hr_tms.overtime_request_report').report_action(self)   

    
    def get_dynamic_numbers(self):
        """ Menghasilkan nomor urut untuk digunakan dalam QWeb report. """
        numbering = {}
        counter = 1
        for record in self:
            numbering[record.id] = list(range(counter, counter + len(record.hr_ot_planning_ids))) #perbaikan disini
            counter += len(record.hr_ot_planning_ids)
        return numbering        
            
    def action_search_employee(self):
        #if self.department_id:
        return {
            'type': 'ir.actions.act_window',
            'name': _('Search Employee'),
            'res_model': 'hr.employeedepartment',
            'view_mode': 'form',
            'target': 'new',
            'domain': [('department_id', '=', self.department_id.id)],
            'context': {
                'active_id': self.id, 
                'fieldname':'plan_id', 
                'default_modelname':'hr.overtime.planning',
                'default_area_id':self.area_id.id,
                'default_branch_id':self.branch_id.id,
                'default_plann_date_from':self.periode_from,
                'default_plann_date_to':self.periode_to,
                'default_department_id':self.department_id.id,
                },
            'views': [[False, 'form']]
        }
        #else:
        #    raise UserError('Sub Department Not Selected')
    def action_generate_ot(self):
        try:
            self.env.cr.execute("CALL generate_ot_request()")
            self.env.cr.commit()
            _logger.info("Stored procedure executed successfully.")
        except Exception as e:
            _logger.error("Error calling stored procedure: %s", str(e))
            raise UserError("Error executing the function: %s" % str(e))

    @api.depends('request_date')
    def _compute_req_day_name(self):
        for record in self:
            if record.request_date:
                record.request_day_name = record.request_date.strftime('%A')
            else:
                record.request_day_name = False

    @api.depends('hr_ot_planning_ids')
    def _compute_record_employees(self):
        for record in self:
            record.count_record_employees = len(record.hr_ot_planning_ids)

    @api.onchange('ot_type')
    def _onchange_ot_type(self):
        for rec in self:
            if rec.ot_type and rec.hr_ot_planning_ids:
                for line in rec.hr_ot_planning_ids:
                    line.ot_type = rec.ot_type   
            
    
class HREmpOvertimeRequestEmployee(models.Model):
    _name = "hr.overtime.employees"
    _description = 'HR Employee Overtime Planning Request Employee'

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
            
    @api.depends('areah_id','branchh_id','departmenth_id')
    def _ambil_employee(self):
        for rec in self:
            if rec.areah_id:
                emp = self.env['hr.employee'].sudo().search([('area','=',rec.areah_id.id)])
                if rec.branchh_id:
                    emp = emp.filtered(lambda p:p.branch_id.id == rec.branchh_id.id)
                if rec.departmenth_id:
                    emp = emp.filtered(lambda p:p.department_id.id == rec.departmenth_id.id)
                rec.employee_ids = [Command.set(emp.ids)]

    branch_ids = fields.Many2many('res.branch', 'hr_permission_entry_rel', string='AllBranch', compute='_isi_semua_branch', store=False)
    alldepartment = fields.Many2many('hr.department','hr_employeelist_schedule_rel', string='All Department',compute='_isi_department_branch',store=False)
    planning_id = fields.Many2one('hr.overtime.planning',string='HR Overtime Request Planning',index=True)
    areah_id = fields.Many2one('res.territory', string='Area ID Header', related='planning_id.area_id',index=True, readonly=True)
    area_id = fields.Many2one('res.territory', string='Area',index=True)
    branchh_id = fields.Many2one('res.branch', related='planning_id.branch_id',string='Bisnis Unit Header', index=True, readonly=True)
    departmenth_id = fields.Many2one('hr.department', related='planning_id.department_id',string='Department ID Header', index=True, readonly=True)
    nik = fields.Char('Employee NIK',index=True)
    employee_ids = fields.Many2many('hr.employee','ov_plan_emp_rel',compute='_ambil_employee',string='Employee Name',store=False)
    employee_id = fields.Many2one('hr.employee',domain="[('id','in',employee_ids),('state','=','approved')]",string='Employee Name',index=True)
    plann_date_from = fields.Date('Plan Date From',default=fields.Date.today)
    plann_date_to = fields.Date('Plan Date To',default=fields.Date.today)

    # penambahan field char untuk penulisan waktu dari field float agar lebih mudah
    ot_plann_from = fields.Float('OT Plan From')
    ot_plann_to = fields.Float('OT Plan To')
    ot_plann_from_char = fields.Char('OT Plan From (Str)', compute="convert_float_to_time", store=True)
    ot_plann_to_char = fields.Char('OT Plan To (Str)', compute="convert_float_to_time", store=True)

    approve_time_from = fields.Float('OT App From')
    approve_time_to = fields.Float('OT App To')
    approve_time_from_char = fields.Char('OT App From (Str)', compute="convert_float_to_time", store=True)
    approve_time_to_char = fields.Char('OT App To (Str)', compute="convert_float_to_time", store=True)

    realization_time_from = fields.Float('Realization Time From')
    realization_time_to = fields.Float('Realization Time To')
    realization_time_from_char = fields.Char('Realization Time From (Str)', compute="convert_float_to_time", store=True)
    realization_time_to_char = fields.Char('Realization Time To (Str)', compute="convert_float_to_time", store=True)

    verify_time_from = fields.Float('Verify Time From')
    verify_time_to = fields.Float('Verify Time To')
    verify_time_from_char = fields.Char('Verify Time From (Str)', compute="convert_float_to_time", store=True)
    verify_time_to_char = fields.Char('Verify Time To (Str)', compute="convert_float_to_time", store=True)

    @api.depends('ot_plann_from','ot_plann_to',
                 'approve_time_from','approve_time_to',
                 'realization_time_from','realization_time_to',
                 'verify_time_from','verify_time_to')
    def convert_float_to_time(self):
        for line in self:
            line.ot_plann_from_char = self.float_to_time_str(line.ot_plann_from)
            line.ot_plann_to_char = self.float_to_time_str(line.ot_plann_to)

            line.approve_time_from_char = self.float_to_time_str(line.approve_time_from)
            line.approve_time_to_char = self.float_to_time_str(line.approve_time_to)

            line.realization_time_from_char = self.float_to_time_str(line.realization_time_from)
            line.realization_time_to_char = self.float_to_time_str(line.realization_time_to)

            line.verify_time_from_char = self.float_to_time_str(line.verify_time_from)
            line.verify_time_to_char = self.float_to_time_str(line.verify_time_to)

    def float_to_time_str(self, float_time):
        if float_time is None:
            return ''
        hours = int(float_time)
        minutes = int(round((float_time - hours) * 60))
        return f'{hours:02d}:{minutes:02d}'

    default_ot_hours = fields.Selection(
        selection=OT_HOURS_SELECTION,
        string='Default Jam OT')
    # -------------------------------------------------------
    machine = fields.Char('Machine')
    work_plann = fields.Char('Work Plan')
    output_plann = fields.Char('Output Plan')
    branch_id = fields.Many2one('res.branch', domain="[('id','in',branch_ids)]", string='Business Unit', index=True)
    department_id = fields.Many2one('hr.department', domain="[('id','in',alldepartment)]", string='Sub Department')
    bundling_ot = fields.Boolean(string="Bundling OT")
    transport = fields.Boolean('Jemputan')
    meals = fields.Boolean(string='Meal Dine In')
    meals_cash = fields.Boolean(string='Meal Cash')
    ot_type = fields.Selection([('regular','Regular'),('holiday','Holiday')],string='OT Type')
    planning_req_name = fields.Char(string='Planning Request Name',required=False)
    is_cancel = fields.Boolean('Cancel')
    state = fields.Selection(related='planning_id.state', string='state', store=True)
    output_realization = fields.Char('Output Realization')
    explanation_deviation = fields.Char('Explanation Deviation')
    is_approved_mgr = fields.Boolean('Approved by MGR')
    route_id = fields.Many2one('sb.route.master', domain="[('branch_id','=',branch_id)]", string='Rute')

    @api.onchange('approve_time_from', 'approve_time_to')
    def _onchange_meals(self):
        for rec in self:
            if rec.approve_time_to - rec.approve_time_from >= 4:
                self.meals = True
            else:
                self.meals = False

    @api.onchange('employee_id')
    def rubah_employee(self):
        for rec in self:
            if rec.employee_id:
                emp = self.env['hr.employee'].sudo().search([('id','=',rec.employee_id.id)],limit=1)
                if emp:
                    rec.nik = emp.nik
                    #rec.branch_id = emp.branch_id.id
                    #rec.department_id = emp.department_id.id
                    #rec.area_id = emp.area.id

    @api.constrains('nik','plann_date_from','plann_date_to')
    def check_duplicate_record(self):
        for rec in self:
            '''Method to avoid duplicate overtime request'''
            duplicate_record = self.search([
                ('id', '!=', rec.id),
                ('nik','=',rec.nik),
                ('plann_date_from','=',rec.plann_date_from),
                ('plann_date_to','=',rec.plann_date_to),
            ])
            if duplicate_record:
                raise ValidationError(f"Duplicate record found for employee {rec.employee_id.name} in {rec.planning_id.name}. "
                                      f"Start date: {rec.plann_date_from} and end date: {rec.plann_date_to}.")

    @api.model
    def create(self, vals):
        # Add the duplicate check before creating a new record
        self.check_duplicate_record()
        return super(HREmpOvertimeRequestEmployee, self).create(vals)

    def write(self, vals):
        # Add the duplicate check before updating a record
        res = super(HREmpOvertimeRequestEmployee, self).write(vals)
        self.check_duplicate_record()
        return res
    
    def btn_view_overtime_details(self):
        return {
            'name': 'action_view_overtime_details',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.overtime.employees',
            # 'views': [(False, 'form')],
            # 'view_id': False,
            'view_id': self.env.ref('sanbe_hr_tms.hr_overtime_employees_view_form').id,
            'target': 'new',
            'res_id': self.id,
            'context': False,
        }