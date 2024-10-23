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
class HREmpGroupSetting(models.Model):
    _name = "hr.empgroup"
    _description = 'HR Employee Group Setting'

    #Function For Filter Branch in Area
    @api.depends('area_id')
    def _isi_semua_branch(self):
        for allrecs in self:
            databranch = []
            for allrec in allrecs.area_id.branch_id:
                mybranch = self.env['res.branch'].search([('name', '=', allrec.name)], limit=1)
                databranch.append(mybranch.id)
            allbranch = self.env['res.branch'].sudo().search([('id', 'in', databranch)])
            allrecs.branch_ids = [Command.set(allbranch.ids)]

    @api.depends('area_id','branch_id')
    def _isi_department_branch(self):
        for allrecs in self:
            databranch = []
            allbranch = self.env['hr.department'].sudo().search([('branch_id','=', allrecs.branch_id.id)])
            allrecs.alldepartment =[Command.set(allbranch.ids)]
            
            allwds = self.env['hr.working.days'].sudo().search([('area_id','=',allrecs.area_id.id),('available_for','in',allrecs.branch_id.ids),('is_active','=',True)])
            #allrecs.wdcode_ids = [Command.set(allwds.ids)]
            
    name = fields.Char('Code', copy=True,required=True)
    description = fields.Char('Description', copy=True)
    #wdcode_ids = fields.Many2many('hr.working.days','wd_emp_rel',string='WD Code All', copy=True,compute='_isi_department_branch', store=False)
    #wdcode = fields.Many2one('hr.working.days',domain="[('id','in',wdcode_ids)]",string='WD Code', copy=True,index=True, required=True)
    area_id = fields.Many2one("res.territory", string='Area ID', copy=True, index=True)
    branch_ids = fields.Many2many('res.branch', 'res_branch_emp_rel', string='AllBranch', copy=True, compute='_isi_semua_branch', store=False)
    is_active = fields.Boolean('Active', copy=True)
    is_inactive = fields.Boolean('In Active', copy=True)
    islabelstate = fields.Char('Status', copy=True)
    branch_id = fields.Many2one('res.branch',string='Bisnis Unit', copy=True,index=True,domain="[('id','in',branch_ids)]")
    area_id = fields.Many2one("res.territory", string='Area ID', copy=True, index=True, required=True)
    alldepartment = fields.Many2many('hr.department','hr_department_emp_set_rel', string='All Department', copy=True,compute='_isi_department_branch',store=False)
    department_id = fields.Many2one('hr.department',domain="[('id','in',alldepartment)]", copy=True,string='Sub Department')
    state = fields.Selection([('draft','Draft'),('approved','Approved'),('close','Close')], default='draft', copy=True)
    #valid_from = fields.Date('Valid From', required=True, copy=True)
    #valid_to = fields.Date('To', required=True, copy=True)
    empgroup_ids = fields.One2many('hr.empgroup.details','empgroup_id',auto_join=True,string='Employee Group Setting Details', copy=True)
            
    @api.constrains('is_active', 'is_inactive')
    def _check_active(self):
        for rec in self:
            if rec.is_active == False:
                raise UserError('Must selected Active or In Active for this This Employee Group Setting')
            
    @api.onchange('is_active')
    def rubahactive(self):
        for rec in self:
            if rec.is_active == True:
                rec.is_inactive = False
            else:
                rec.is_inactive = True
            
    @api.onchange('is_inactive')
    def rubahactivex(self):
        for rec in self:
            if rec.is_inactive == True:
                rec.is_active = False
            else:
                rec.is_active = True
    
    def cek_libur(self,tgl):
        
        sql = """select date_from::date, date_to::date 
                    from resource_calendar_leaves
                where date_from::date>='{_tgl}' and date_to::date<='{_tgl}'
        """.format(_tgl=tgl)
        
        self._cr.execute(sql)
        hasil = self._cr.dictfetchall()
        return hasil
    
    def btn_approved(self):
        for rec in self:
            rec.state = 'approved'
    
    def btn_process(self):
        for res in self:
            for rec in res.empgroup_ids:
                if rec.wdcode:
                    wdffrom = int(rec.wdcode.working_day_from)
                    wdfto = int(rec.wdcode.working_day_to)
                    wdhffrom = int(rec.wdcode.working_half_from)
                    wdhfto = int(rec.wdcode.working_half_from)
                    
                    wd1 = None
                    wd2 = None
                    
                    if rec.wdcode.type_hari == 'fday' or rec.wdcode.type_hari == 'hday':
                        wd1 = wdffrom
                        wd2 = wdfto
                    
                    if rec.wdcode.type_hari == 'fhday':
                        if wdffrom < wdhffrom:
                            wd1 = wdffrom
                        else:
                            wd1 = wdhffrom
                        
                        if wdfto < wdhfto:
                            wd2 = wdhfto
                        else:
                            wd2 = wdfto
                    tmsentry = self.env['hr.attendance'].sudo().search([('employee_id','=',rec.employee_id.id),('dates','>=',rec.valid_from),('dates','<=',rec.valid_to),('area_id', '=', rec.area_id.id),('branch_id', '=', rec.branch_id.id)],order='employee_id asc, dates asc')
                    for rex in tmsentry:
                        day_of_week = (rex.dates.weekday() + 1) % 7
                        chol = []
                        dy = ''
                        print('+++++++++++++')
                        if day_of_week and wd1 and wd2:
                            if day_of_week >= wd1 and day_of_week <= wd2:
                                chol = self.cek_libur(rex.dates)
                                
                                if chol:
                                    dy = 'h'
                                else:
                                    dy = 'w'
                            else:
                                dy = 'h'
                                
                            att_stat = 'absent'
                            if (rex.time_in and rex.time_out) or \
                                (rex.time_in_edited and rex.time_out) or \
                                (rex.time_in and rex.time_out_edited) or \
                                (rex.time_in_edited and rex.time_out_edited):
                                att_stat = 'attendee'
                            else:
                                if dy == 'w':
                                    att_stat = 'absent'
                                else:
                                    att_stat = False
                                
                            if rec.wdcode.type_hari == 'fday' or rec.wdcode.type_hari == 'fhday':
                                print('ini')
                                if dy == 'w':
                                    rex.sudo().write({
                                        'wdcode':rec.wdcode.id if dy =='w' else False,
                                        'day_type':dy,
                                        'codes':self.id if dy =='w' else False,
                                        'valid_from':rec.valid_from if dy =='w' else False,
                                        'valid_to':rec.valid_to if dy =='w' else False,
                                        'attendence_status':att_stat,
                                    })
                            elif rec.wdcode.type_hari == 'hday':
                                if dy == 'h' and att_stat == 'attendee':
                                    print('itu')
                                    rex.sudo().write({
                                        'wdcode':rec.wdcode.id,
                                        'day_type':dy,
                                        'codes':self.id,
                                        'valid_from':rec.valid_from,
                                        'valid_to':rec.valid_to,
                                        'attendence_status':att_stat,
                                    })
                
    def btn_close(self):
        for rec in self:
            rec.state = 'close'
    
    def btn_draft(self):
        for rec in self:
            rec.state = 'draft'
    
    #Function For PopUp Search Employee
    def action_search_employee(self):
            #if self.department_id:    
            return {
                'type': 'ir.actions.act_window',
                'name': _('Search Employee'),
                'res_model': 'hr.employeedepartment',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'active_id': self.id, 
                    'default_modelname':'hr.empgroup',
                    'default_area_id':self.area_id.id,
                    'default_branch_id':self.branch_id.id,
                    'default_department_id':self.department_id.id, 
                    #'default_wdcode':self.wdcode.id,
                    #'default_valid_from':self.valid_from,
                    #'default_valid_to':self.valid_to
                    },
                'views': [[False, 'form']]
            }
            #else:
            #    raise UserError('Sub Department Not Selected')

    #Function For AutoFill data Employee Based On Code
    @api.onchange('code')
    def _isi_details(self):
        for allrec  in self:
            if not allrec.code:
                return
            allrec.area_id = allrec.code.area_id.id
            allrec.branch_id = allrec.code.branch_id.id
            allrec.working_day_from = allrec.code.working_day_from
            allrec.working_day_to = allrec.code.working_day_to
            allrec.isbasic_wd = allrec.code.isbasic_wd
            allrec.fullday_from = allrec.code.fullday_from
            allrec.fullday_to = allrec.code.fullday_to
            allrec.halfday_from = allrec.code.halfday_from
            allrec.halfday_to = allrec.code.halfday_to

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
        return arch, view
#Details Data
class HREmpGroupSettingDetails(models.Model):
    _name = "hr.empgroup.details"
    _description = 'HR Employee Group Setting Details'
    
    @api.depends('area_id')
    def _isi_semua_branch(self):
        for allrecs in self:
            databranch = []
            for allrec in allrecs.area_id.branch_id:
                mybranch = self.env['res.branch'].search([('name', '=', allrec.name)], limit=1)
                databranch.append(mybranch.id)
            allbranch = self.env['res.branch'].sudo().search([('id', 'in', databranch)])
            allrecs.branch_ids = [Command.set(allbranch.ids)]

    @api.depends('area_id','branch_id')
    def _isi_department_branch(self):
        for allrecs in self:
            databranch = []
            allbranch = self.env['hr.department'].sudo().search([('branch_id','=', allrecs.branch_id.id)])
            allrecs.alldepartment =[Command.set(allbranch.ids)]
            
            allwds = self.env['hr.working.days'].sudo().search([('area_id','=',allrecs.area_id.id),('available_for','in',allrecs.branch_id.ids),('is_active','=',True)])
            allrecs.wdcode_ids = [Command.set(allwds.ids)]

    empgroup_id = fields.Many2one('hr.empgroup',string='Employee Group Setting ID', index=True)
    branch_ids = fields.Many2many('res.branch', 'res_branch_emp_detail_rel', string='AllBranch', copy=True, compute='_isi_semua_branch', store=False)
    branch_id = fields.Many2one('res.branch',string='Bisnis Unit', copy=True,index=True,domain="[('id','in',branch_ids)]")
    area_id = fields.Many2one("res.territory", string='Area ID', copy=True, index=True)
    alldepartment = fields.Many2many('hr.department','hr_department_emp_detail_set_rel', string='All Department', copy=True,compute='_isi_department_branch',store=False)
    department_id = fields.Many2one('hr.department',string='Sub Department',copy=True,index=True,domain="[('id','in',alldepartment)]")
    wdcode_ids = fields.Many2many('hr.working.days','wd_emp_detail_rel',string='WD Code All', copy=True,compute='_isi_department_branch', store=False)
    wdcode = fields.Many2one('hr.working.days',domain="[('id','in',wdcode_ids)]",string='WD Code', copy=True,index=True, required=True)
    #state = fields.Selection([('draft','Draft'),('approved','Approved'),('close','Close')], related='empgroup_id.sate',store=True)
    
    employee_id = fields.Many2one('hr.employee',string='Employee Name',index=True,domain="[('area','=',area_id),('branch_id','=',branch_id),('department_id','=',department_id),('state','=','approved')]")
    nik = fields.Char('NIK')
    job_id = fields.Many2one('hr.job',string='Job Position',index=True)
    valid_from = fields.Date('Valid From', required=True, copy=True)
    valid_to = fields.Date('To', required=True, copy=True)
    emp_status = fields.Selection([('probation','Probation'),
                                   ('confirmed','Confirmed'),
                                   ('probation', 'Probation'),
                                   ('end_contract', 'End Of Contract'),
                                   ('resigned', 'Resigned'),
                                   ('retired', 'Retired'),
                                   ('terminated', 'Terminated'),
                                   ],string='Employment Status',related='employee_id.emp_status',store=False)

    #Function For Autofill Employee data based on Employee_id
    def btn_clear(self):
        raise UserError(self.empgroup_id)
        
    @api.onchange('employee_id')
    def isi_employee(self):
        for allrec in self:
            if not allrec.employee_id:
                return
            allrec.nik = allrec.employee_id.nik
            allrec.department_id = allrec.employee_id.department_id.id
            allrec.job_id = allrec.employee_id.job_id.id


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
        return (arch, view)