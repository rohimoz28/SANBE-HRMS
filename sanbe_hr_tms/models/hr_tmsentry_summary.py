# -*- coding : utf-8 -*-
#################################################################################
# Author    => Albertus Restiyanto Pramayudha
# email     => xabre0010@gmail.com
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA
#################################################################################

from odoo import fields, models, api,  _, Command
from odoo.exceptions import ValidationError,UserError
from odoo.osv import expression
import pytz
from datetime import date,datetime,time, timedelta
TMS_ENTRY_STATE = [
    ('draft', 'Draft'),
    ('to_approved', "To Approved"),
    ('approved', "Approved"),
    ('transfer_payroll','Transfer Payroll'),
    ('done', "Close"),
]
class HRTMSEntrySummary(models.Model):
    _name = "hr.tmsentry.summary"
    _description = 'HR TMS Entry Summary'
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
    def _default_employee(self):
        return self.env.user.employee_id

    @api.depends('tmsentry_ids.tms_status')
    def _cek_for_tmsentry_status(self):
        for alldata in self:
            laststate = False
            cntdata = 0
            if alldata.state:
                mylaststate = alldata.state
            else:
                mylaststate = 'draft'
            allentrydata = len(alldata.tmsentry_ids)
            for allentry in alldata.tmsentry_ids:
                if laststate == False:
                    if allentry.tms_status:
                        laststate = allentry.tms_status
                    else:
                        laststate = 'draft'
                if laststate == allentry.tms_status:
                    cntdata += 1
            if cntdata == allentrydata:
                if alldata.state != laststate:
                    if laststate =='approved':
                        alldata.state = 'approved'
                    else:
                        alldata.state= laststate
            else:
                alldata.state = mylaststate
    def _get_active_periode_from(self):
        mycari = self.env['hr.opening.closing'].sudo().search([('isopen','=',True)],limit=1)
        return mycari.open_periode_from or False

    def _get_active_periode_to(self):
        mycari = self.env['hr.opening.closing'].sudo().search([('isopen','=',True)],limit=1)
        return mycari.open_periode_to or False

    periode_id = fields.Many2one('hr.opening.closing',string='Periode ID',index=True)
    employee_id =fields.Many2one('hr.employee', string="Employee", default=_default_employee, required=True, ondelete='cascade', index=True ,readonly="state =='done'")
    area_id = fields.Many2one('res.territory',string='Area ID', index=True,readonly="state =='done'")
    branch_ids = fields.Many2many('res.branch', 'res_branch_rel', string='AllBranch', compute='_isi_semua_branch',
                                  store=False)
    branch_id = fields.Many2one('res.branch',string='Business Unit',index=True,domain="[('id','in',branch_ids)]" ,readonly="state =='done'")
    department_id = fields.Many2one('hr.department',string='Sub Department' ,readonly="state =='done'")
    nik = fields.Char('Employee NIK')
    job_id = fields.Many2one('hr.job',string='Job Title' ,readonly="state =='done'")
    date_from  = fields.Date('Periode From',readonly="state =='done'",related='periode_id.open_periode_from')
    date_to = fields.Date('Periode To',readonly="state =='done'",related='periode_id.open_periode_to')
    tmsentry_ids = fields.One2many('hr.attendance','tmsentry_id',auto_join=True ,readonly="state =='done'")
    state = fields.Selection(
        selection=TMS_ENTRY_STATE,
        string="TMS Entry Summary Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        compute='_cek_for_tmsentry_status',
        default='draft')
    attendee_count = fields.Integer('Attendee',compute='_hitung_total_data',store=False,precompute=True)
    attendee_total = fields.Float('Total Attendee',compute='_hitung_total_data',store=False,precompute=True)
    sick_count = fields.Integer('Sick',compute='_hitung_total_data',store=False,precompute=True)
    absent_count = fields.Integer('Absent',compute='_hitung_total_data',store=False,precompute=True)
    leave_count = fields.Integer('Leave',compute='_hitung_total_data',store=False,precompute=True)
    permission_count =  fields.Integer('Permission',compute='_hitung_total_data',store=False,precompute=True)
    outstation_count =  fields.Integer('Out Station',compute='_hitung_total_data',store=False,precompute=True)
    ot1_count = fields.Integer('OT1',compute='_hitung_total_data',store=False,precompute=True)
    ot2_count = fields.Integer('OT2', compute='_hitung_total_data',store=False, precompute=True)
    ot3_count = fields.Integer('OT3', compute='_hitung_total_data',store=False,precompute=True)
    ot4_count = fields.Integer('OT4', compute='_hitung_total_data',store=False,precompute=True)
    ot1_total = fields.Float('Total OT1x',compute='_hitung_total_data',store=False,precompute=True)
    ot2_total = fields.Float('Total OT2x', compute='_hitung_total_data',store=False, precompute=True)
    ot3_total = fields.Float('Total OT3x', compute='_hitung_total_data',store=False,precompute=True)
    ot4_total = fields.Float('Total OT4x', compute='_hitung_total_data',store=False,precompute=True)
    ot_auto_count = fields.Integer('OT Auto', compute='_hitung_total_data',store=False,precompute=True)
    ot_auto_total = fields.Float('Total OT Autox', compute='_hitung_total_data',store=False,precompute=True)
    ot1_totalx = fields.Float('Total OT1',compute='_hitung_total_data',store=False,precompute=True)
    ot2_totalx = fields.Float('Total OT2', compute='_hitung_total_data',store=False, precompute=True)
    ot3_totalx = fields.Float('Total OT3', compute='_hitung_total_data',store=False,precompute=True)
    ot4_totalx = fields.Float('Total OT4', compute='_hitung_total_data',store=False,precompute=True)
    ot_auto_totalx = fields.Float('Total OT Auto', compute='_hitung_total_data',store=False,precompute=True)
    delay_count = fields.Float('Delay', compute='_hitung_total_data',store=False,precompute=True)
    delay_total = fields.Float('Total Delay', compute='_hitung_total_data',store=False,precompute=True)
    pattendace_count = fields.Float('Premi Attendance', compute='_hitung_total_data',store=False,precompute=True)
    transport_count = fields.Float('Transport Allowance', compute='_hitung_total_data',store=False,precompute=True)
    nightshift_count = fields.Float('Night Shift', compute='_hitung_total_data',store=False,precompute=True)
    is_deduction = fields.Boolean('Deducton', default=False)
    deduction = fields.Float('total deductions (days)',default=0)

    def _getwaktu(self,waktu):
        ret = timedelta()
        for i in waktu:
            x=str(self.ubahjam(i))
            (h, m, s) = x.split(':')
            d = timedelta(hours=int(h), minutes=int(m), seconds=int(s))
            ret += d
        return ret
    
    def _getwaktu2(self,waktu):
        ret = timedelta()
        (h, m, s) = waktu.split(':')
        d = timedelta(hours=int(h), minutes=int(m))
        ret += d
        return ret
    
    def _getwaktu4(self,waktu):
        ret = timedelta()
        (h, m, s) = waktu.split(':')
        d = timedelta(hours=int(h), minutes=int(m), seconds=int(s))
        ret += d
        return ret
    
    def _getwaktu3(self,waktu):
        #ret = timedelta()
        (h, m, s) = waktu.split(':')
        d = timedelta(hours=int(h), minutes=int(m), seconds=int(s))
        ret = self._getfloat(d)
        return ret
    
    def ubahjam(self,hours_float):
        midnight = datetime.combine(date.today(), time.min)
        time_delta = timedelta(hours=hours_float)
        time_obj = (midnight + time_delta).time()
        return time_obj

    def ubahjam2(self,waktu):
        detik = waktu * 3600
        hours = divmod(detik, 3600)[0] # split to hours and seconds
        sisad = detik - (hours * 3600)
        minutes = divmod(sisad,60)[0]
        seconds = sisad - (minutes * 60)
        #result = '{0:02.0f}:{1:02.0f}'.format(*divmod(waktu * 60, 60))
        result = "{0:02.0f}:{1:02.0f}:{2:02.0f}".format(hours, minutes, seconds)
        return result
    
    def _getjam(self,jam):
        ret = None
        detik = jam.total_seconds()
        hour = divmod(detik,3600)[0]
        sisad = detik - (hour * 3600)
        minute = divmod(sisad,60)[0]
        second = sisad - (minute * 60)
        ret = str(hour) + ":" + minute + ":" + second
        return ret
    
    def _getfloat(self,jam):
        ret = None
        detik = jam.total_seconds()
        hour = divmod(detik,3600)[0]
        minute = divmod(detik,3600)[1]/3600
        #hour = divmod(detik,3600)[0]
        #sisad = detik - (hour * 3600)
        #minute = divmod(sisad,60)[0]
        #second = sisad - (minute * 60)
        ret = hour + minute
        return ret
    
    def mass_approve(self):
        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['hr.tmsentry.summary'].browse(selected_ids)
        attendance_records = self.env['hr.attendance'].sudo().search([('tmsentry_id','in',selected_records.ids)])
        for rec in attendance_records:
            rec.approved_data()
            rec.env.cr.commit()
        
    @api.depends('tmsentry_ids','state')
    def _hitung_total_data(self):
        for rec in self:
            attende = rec.tmsentry_ids.filtered(lambda p: p.attendence_status in ['attendee','delay_in','leave','outstation'] and p.day_type=='w')
            rec.attendee_count = len(attende)
            
            sicks = rec.tmsentry_ids.filtered(lambda p: p.attendence_status =='sick' and p.day_type=='w')
            absent = rec.tmsentry_ids.filtered(lambda p: p.attendence_status =='absent' and p.day_type=='w')
            leaves = rec.tmsentry_ids.filtered(lambda p: p.attendence_status =='leave' and p.day_type=='w')
            permission = rec.tmsentry_ids.filtered(lambda p: p.permision_code != False)
            outstation  = rec.tmsentry_ids.filtered(lambda p: p.attendence_status =='outstation' and p.day_type=='w')
            rec.sick_count  = len(sicks)
            rec.absent_count = len(absent)
            rec.leave_count  = len(leaves)
            rec.permission_count  = len(permission)
            rec.outstation_count  = len(outstation)
            
            dataot1 =  rec.tmsentry_ids.filtered(lambda p: p.ot1 != False)
            tot1x =  (dataot1.mapped('ot1_time'))
            tot1xx =  sum(dataot1.mapped('ot1_timex'))
            tot1 = self._getfloat(self._getwaktu(tot1x))
            rec.ot1_count  = len(dataot1)
            rec.ot1_total = tot1
            rec.ot1_totalx = tot1xx
                
            dataot2 =  rec.tmsentry_ids.filtered(lambda p: p.ot2 != False)
            tot2x =  (dataot2.mapped('ot2_time'))
            tot2xx =  sum(dataot2.mapped('ot2_timex'))
            tot2 = self._getfloat(self._getwaktu(tot2x))
            rec.ot2_count  = len(dataot2)
            rec.ot2_total = tot2
            rec.ot2_totalx = tot2xx
                
            dataot3 =  rec.tmsentry_ids.filtered(lambda p: p.ot3 != False)
            tot3x =  (dataot3.mapped('ot3_time'))
            tot3xx =  sum(dataot3.mapped('ot3_timex'))
            tot3 = self._getfloat(self._getwaktu(tot3x))
            rec.ot3_count  = len(dataot3)
            rec.ot3_total = tot3
            rec.ot3_totalx = tot3xx
                
            dataot4 =  rec.tmsentry_ids.filtered(lambda p: p.ot4 != False)
            tot4x =  (dataot4.mapped('ot4_time'))
            tot4xx =  sum(dataot4.mapped('ot4_timex'))
            tot4 = self._getfloat(self._getwaktu(tot4x))
            rec.ot4_count  = len(dataot4)
            rec.ot4_total = tot4
            rec.ot4_totalx = tot4xx
                
            dataot_auto =  rec.tmsentry_ids.filtered(lambda p: p.ot_auto != False)
            tot_autox =  (dataot_auto.mapped('ot_auto_time'))
            tot_autoxx = sum(dataot_auto.mapped('ot_auto_timex'))
            tot_auto = self._getfloat(self._getwaktu(tot_autox))
            rec.ot_auto_count  = len(dataot_auto)
            rec.ot_auto_total = tot_auto
            rec.ot_auto_totalx = tot_autoxx
                
            datapatt =  rec.tmsentry_ids.filtered(lambda p: p.premi_attendee != False)
            datatrans =  rec.tmsentry_ids.filtered(lambda p: p.tunjangan_trp != False)
            datanight =  rec.tmsentry_ids.filtered(lambda p: p.night_shift != False)
            rec.pattendace_count  = len(datapatt)
            rec.transport_count  = len(datatrans)
            rec.nightshift_count  = len(datanight)
            
            datadelay =  rec.tmsentry_ids.filtered(lambda p: p.delayed != False)
            tdelayx =  (datadelay.mapped('delayed'))
            tdelay = self._getfloat(self._getwaktu(tdelayx))
            rec.delay_count  = len(datadelay)
            rec.delay_total = tdelay
            
            tatt = timedelta()
            tattx =  ((rec.tmsentry_ids.filtered(lambda p: p.add_hour != False)).mapped('add_hour'))
            
            if tattx and tattx != '' and tattx != False :
                tatt = self._getfloat(self._getwaktu(tattx))
            rec.attendee_total = tatt
        return
    
    @api.onchange('employee_id')
    def isi_employee(self):
        for allrec in self:
            if not allrec.employee_id:
                return
            allrec.nik = allrec.employee_id.nik
            allrec.department_id = allrec.employee_id.department_id.id
            allrec.job_id = allrec.employee_id.job_id.id
            allrec.area_id  = allrec.employee_id.area.id
            allrec.branch_id = allrec.employee_id.branch_id.id

    @api.onchange('date_from','date_to','employee_id')
    def isi_details(self):
        for allrec in self:
            if not allrec.date_from and not allrec.date_to and not allrec.employee_id:
                return
            if len(allrec.tmsentry_ids) > 0:
                allrec.tmsentry_ids = [Command.set([])]

            myentry = self.env['hr.attendance'].sudo().search([('dates','>=', allrec.date_from),('dates','<=',allrec.date_to),('employee_id','=',allrec.employee_id.id)])
            allrec.tmsentry_ids = [Command.set(myentry.ids)]

    def btn_toapproved(self):
        for rec in self:
            rec.state = 'to_approved'
            
    def btn_draft(self):
        for rec in self:
            rec.state = 'draft'
            
    def transfer_payroll(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.transfer.payroll',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'res_id': self.id,
            'context': False,
        }

    def action_done(self):
        for allrec in self:
            for allentry in allrec.tmsentry_ids:
                allentry.action_done()

    def unlink(self):
        self = self.sudo()
        for allrec in self:
            if allrec.state !='draft':
                raise UserError('Cannot Delete Data That Not in Draft State')
            for alldet in allrec.tmsentry_ids:
                alldet.unlink()
        return super(HRTMSEntrySummary,self).unlink()

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

    def action_calculation(self):
        for alldata in self:
            for allentry in alldata.tmsentry_ids:
                allentry.action_calculation()
            return

class HRTMSEntry(models.Model):
    _name = "hr.tms.entry"
