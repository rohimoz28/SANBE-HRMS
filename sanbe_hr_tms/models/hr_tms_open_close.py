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
from datetime import timedelta, datetime, time,date
import dateutil.parser
import holidays
date_format = "%Y-%m-%d"
from odoo.exceptions import AccessError, MissingError, UserError


class HRTmsOpenClose(models.Model):
    _name = "hr.opening.closing"
    _description = 'HR TMS Open And Close'

    @api.depends('area_id')
    def _isi_semua_branch(self):
        for allrecs in self:
            databranch = []
            for allrec in allrecs.area_id.branch_id:
                mybranch = self.env['res.branch'].search([('name','=', allrec.name)], limit=1)
                databranch.append(mybranch.id)
            allbranch = self.env['res.branch'].sudo().search([('id','in', databranch)])
            allrecs.branch_ids =[Command.set(allbranch.ids)]
    name = fields.Char('Periode Name')
    area_id = fields.Many2one('res.territory',string='Area ID', index=True )
    branch_ids = fields.Many2many('res.branch', 'res_branch_rel', string='AllBranch', compute='_isi_semua_branch',
                                  store=False)
    branch_id = fields.Many2one('res.branch',string='Bisnis Unit',index=True,domain="[('id','in',branch_ids)]")
    open_periode_from = fields.Date('Opening Periode From')
    open_periode_to = fields.Date('Opening Periode To')
    close_periode_from = fields.Date('Closing Periode From')
    close_periode_to = fields.Date('Closing Periode To')
    isopen = fields.Boolean('Is Open')
    state_process = fields.Selection([('draft','Draft'),('running', 'Running'),('transfer_to_payroll','Transfer To Payroll'),('done','Close')], default='draft', String='Process State')

    @api.model_create_multi
    def create(self, values):
        for vals in values:
            
            if ('branch_id' in vals) and ('open_periode_from' in vals):
                if 'open_periode_to' in vals:
                    br = self.env['res.branch'].sudo().search([('id','=',vals['branch_id'])])
                    vals['name'] = br.name + '/' +str((datetime.strptime(str(vals['open_periode_from']), "%Y-%m-%d").date()).strftime('%d-%m-%Y'))+'-'+str((datetime.strptime(str(vals['open_periode_to']), "%Y-%m-%d").date()).strftime('%d-%m-%Y'))
                    check = self.env['hr.opening.closing'].sudo().search([('branch_id','=',br.id),('open_periode_from','<=',datetime.strptime(str(vals['open_periode_from']), "%Y-%m-%d").date()),('open_periode_to','>=',datetime.strptime(str(vals['open_periode_from']), "%Y-%m-%d").date())])
                    if check:
                        raise UserError('Open Periode From for This Branch Already Used')
                    check = self.env['hr.opening.closing'].sudo().search([('branch_id','=',br.id),('open_periode_from','<=',datetime.strptime(str(vals['open_periode_to']), "%Y-%m-%d").date()),('open_periode_to','>=',datetime.strptime(str(vals['open_periode_to']), "%Y-%m-%d").date())])
                    if check:
                        raise UserError('Open Periode To for This Branch Already used')
            else:
                raise UserError('Branch or Open Periode From Not Selected')
        res = super(HRTmsOpenClose,self).create(values)
        return res
    
    #def init(self):
    #    dat = self.env['hr.opening.closing'].sudo().search([])
    #    for rec in dat:
    #        if rec.branch_id and rec.open_periode_from and rec.open_periode_to:
    #            br = self.env['res.branch'].sudo().search([('id','=',rec.branch_id.id)])
    #            #rec.name = br.name + '/' +str(datetime.strptime(str(rec.open_periode_from), "%d-%m-%Y").date())+'-'+str(datetime.strptime(str(rec.open_periode_to), "%d-%m-%Y").date())
    #            if br:
    #                rec.write({'name': br.name + '/' + str((datetime.strptime(str(rec.open_periode_from), "%Y-%m-%d").date()).strftime('%d-%m-%Y'))+'-'+str((datetime.strptime(str(rec.open_periode_to), "%Y-%m-%d").date()).strftime('%d-%m-%Y'))})
    #                rec.env.cr.commit()
            
    def write(self,vals):
        for rec in self:
            if rec.branch_id and rec.open_periode_from and rec.open_periode_to:
                vals['name'] = self.branch_id.name + '/' + str((datetime.strptime(str(rec.open_periode_from), "%Y-%m-%d").date()).strftime('%d-%m-%Y'))+'-'+str((datetime.strptime(str(rec.open_periode_to), "%Y-%m-%d").date()).strftime('%d-%m-%Y'))
        res = super(HRTmsOpenClose,self).write(vals)
        return res
    
    def action_opening_periode(self):
        for alldata in self:
            if not alldata.open_periode_from or not alldata.open_periode_to:
                raise UserError("Please Input Periode From And To First")
            #self.env.cr.execute("DELETE FROM hr_tmsentry_summary where")
            #self.env.cr.execute("DELETE FROM hr_attendance")
            awal = datetime.strptime(str(alldata.open_periode_from), date_format)
            akhir = datetime.strptime(str(alldata.open_periode_to), date_format)
            selisih = (akhir - awal).days
            entrydata = []
            prawal = datetime.strptime(str(alldata.open_periode_from), "%Y-%m-%d")
            prakhir = datetime.strptime(str(alldata.open_periode_to), "%Y-%m-%d")
            adadataawal = self.env['hr.tmsentry.summary'].sudo().search([('periode_id','=', alldata.id or alldata._origin.id)])
            if adadataawal:
                raise UserError(
                    'There is already transaction in the periode that you have been choose, please input other periode')
            else:
                datatmssum =[]
                emp_query = """SELECT id, area,branch_id,department_id, nik,job_id FROM hr_employee where area=%s and branch_id=%s and state='approved'"""
                self.env.cr.execute(emp_query,(alldata.area_id.id,alldata.branch_id.id))
                # myemployee = self.env['hr.employee'].sudo().search([('area','=',alldata.area_id.id),('branch_id','=',alldata.branch_id.id),('state','=','approved')])
                myemployee = self.env.cr.fetchall()
                liburan = holidays.country_holidays('ID')
        
                for allemp in myemployee:
                    self.env.cr.execute("INSERT INTO hr_tmsentry_summary (employee_id,periode_id,area_id,branch_id,department_id,nik,job_id) VALUES(%s,%s,%s,%s,%s,%s,%s)",(allemp[0],alldata.id or alldata._origin.id,allemp[1],allemp[2],allemp[3],allemp[4],allemp[5]))
                    self.env.cr.execute("SELECT id FROM hr_tmsentry_summary where employee_id=%s and area_id=%s and branch_id=%s and periode_id=%s",(allemp[0],allemp[1],allemp[2],alldata.id or alldata._origin.id))
                    tmssum = self.env.cr.fetchone()
                    for tglawal in range(int(selisih) + 1):
                        hariurutan =awal+ timedelta(days=tglawal)
                        namahari = hariurutan.strftime('%a')
                        
                        libur_id = liburan.get(str(hariurutan).split(' ')[0])
                        iniliburan = False
                        if libur_id != None or namahari =='Sun':
                            iniliburan = True
                        daytype = 'w'
                        if iniliburan:
                            daytype='h'
                        urutantgl = datetime.date(datetime.strptime(hariurutan.strftime('%Y-%m-%d'), '%Y-%m-%d'))
                        shiftgue = self.env['hr.empgroup'].sudo().search([('valid_from','<=',urutantgl),('valid_to','>=',urutantgl)])
                        mywdcodes = False
                        for allshifts in shiftgue:
                            for allempshift in allshifts.empgroup_ids:
                                if allempshift.employee_id.id == allemp[0]:
                                    mywdcodes = allshifts.id
                                    break
                        mynik = self.env['hr.employee'].sudo().browse(allemp[0]).nik
                        if mywdcodes:
                            #self.env.cr.execute("INSERT INTO hr_attendance (dates,day_type,employee_id,nik,codes,area_id,branch_id,tmsentry_id,tms_status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",(urutantgl,daytype,allemp[0],mynik,int(mywdcodes),alldata.area_id.id,alldata.branch_id.id,tmssum,'draft'))
                            self.env.cr.execute("INSERT INTO hr_attendance (dates,employee_id,nik,codes,area_id,branch_id,tmsentry_id,tms_status,department_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",(urutantgl,allemp[0],mynik,int(mywdcodes),alldata.area_id.id,alldata.branch_id.id,tmssum,'draft',allemp[3]))
                        else:
                            #self.env.cr.execute("INSERT INTO hr_attendance (dates,day_type,employee_id,nik,area_id,branch_id,tmsentry_id,tms_status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(urutantgl,daytype,allemp[0],mynik,alldata.area_id.id,alldata.branch_id.id,tmssum,'draft'))
                            self.env.cr.execute("INSERT INTO hr_attendance (dates,employee_id,nik,area_id,branch_id,tmsentry_id,tms_status,department_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(urutantgl,allemp[0],mynik,alldata.area_id.id,alldata.branch_id.id,tmssum,'draft',allemp[3]))
                    alldata.isopen = True
                    alldata.state_process = "running"

    def action_closing_periode(self):
        for alldata in self:
            if not alldata.close_periode_from or not alldata.close_periode_to:
                raise UserError("Please Input Periode From And To First")
            carisummary= self.env['hr.tmsentry.summary'].sudo().search(
                [('date_from', '=', alldata.open_periode_from),
                 ('date_to', '<=', alldata.open_periode_to), ('branch_id', '=', alldata.branch_id.id)])
            for allsummary in carisummary:
                if allsummary.state !='transfer_payroll':
                    raise UserError('The Closing process cannot be carried out because there still transaction that have not been transffered to payroll')
                else:
                    allsummary.write({'state': 'done'})
            return