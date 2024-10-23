
from odoo import fields, models, api, _, Command
from odoo.exceptions import ValidationError,UserError


class HrCariEmployeeDepartment(models.TransientModel):
    _name = 'hr.employeedepartment'
    _description = 'Search Employee Department Wizard'

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
            allbranch = self.env['hr.department'].sudo().search([('branch_id','=', allrecs.branch_id.id)])
            allrecs.alldepartment =[Command.set(allbranch.ids)]
            
            allwds = self.env['hr.working.days'].sudo().search([('area_id','=',allrecs.area_id.id),('available_for','in',allrecs.branch_id.ids),('is_active','=',True)])
            allrecs.wdcode_ids = [Command.set(allwds.ids)]
            
    area_id = fields.Many2one('res.territory', string='Area ID', index=True)
    branch_ids = fields.Many2many('res.branch', 'res_branch_plan_ot_rel', string='AllBranch', compute='_isi_semua_branch',
                                  store=False)
    branch_id = fields.Many2one('res.branch', string='Bisnis Unit', index=True, domain="[('id','in',branch_ids)]")
    alldepartment = fields.Many2many('hr.department','hr_department_plan_ot_rel', string='All Department',compute='_isi_department_branch',store=False)
    department_id = fields.Many2one('hr.department',domain="[('id','in',alldepartment)]",string='Sub Department')
    employee_ids = fields.One2many('hr.employeedepartment.details','cari_id',auto_join=True,string='Cari Employee Details')
    empgroup_id = fields.Many2one('hr.empgroup',string='Employee Group Setting')
    plan_id = fields.Many2one('hr.overtime.planning',string='Planning OT')
    modelname = fields.Selection([('hr.empgroup','hr.empgroup'),('hr.overtime.planning','hr.overtime.planning')])
    wdcode_ids = fields.Many2many('hr.working.days','wd_plan_ot_rel',string='WD Code All', copy=True,compute='_isi_department_branch', store=False)
    wdcode = fields.Many2one('hr.working.days',domain="[('id','in',wdcode_ids)]",string='WD Code', copy=True,index=True)
    plann_date_from = fields.Date('Plann Date From')
    plann_date_to = fields.Date('Plann Date to')
    ot_plann_from = fields.Float('OT Plann From')
    ot_plann_to = fields.Float('OT Plann To')
    approve_time_from = fields.Float('Approve Time From')
    approve_time_to = fields.Float('Approve Time To')
    machine = fields.Char('Machine')
    work_plann = fields.Char('Work Plann')
    output_plann = fields.Char('Output Plann')
    transport = fields.Boolean('Transport')
    meals = fields.Boolean('Meal')
    branch_id = fields.Many2one('res.branch', string='Bisnis Unit', index=True)
    valid_from = fields.Date('Valid From',copy=True)
    valid_to = fields.Date('To', copy=True)

    @api.model
    def default_get(self, fields):
        result = super(HrCariEmployeeDepartment, self).default_get(fields)
        myempg = self._context.get('active_id')
        if self._context.get('fieldname'):
            fieldname = self._context.get('fieldname')
        else:
            fieldname = 'empgroup_id'  
          
        if myempg:
            result[fieldname] = myempg
        return result

    @api.onchange('area_id')
    def _isi_employee_area(self):
        for alldata in self:
            if not alldata.area_id:
                return
            datadetails = self.env['hr.employeedepartment.details']
            myemp = self.env['hr.employee'].sudo().search([('area','=',alldata.area_id.id),('state','=','approved')])
            
            sql = """SELECT id,department_id,nik,job_id"""
            for allemp in myemp:
                datadetails |= self.env['hr.employeedepartment.details'].sudo().create({
                    'cari_id': alldata._origin.id or alldata.id,
                    'department_id': allemp.department_id.id,
                    'employee_id': allemp.id,
                    'nik': allemp.nik,
                    'job_id': allemp.job_id.id,
                    'is_selected': False,
                })
            alldata.employee_ids = datadetails.ids
    
    @api.onchange('area_id','branch_id')
    def _isi_employee_branch(self):
        for alldata in self:
            if not alldata.branch_id and not alldata.area_id:
                return
            
            datadetails = self.env['hr.employeedepartment.details']
            myemp = self.env['hr.employee'].sudo().search([('area','=',alldata.area_id.id),('branch_id','=',alldata.branch_id.id),('state','=','approved')])
            for allemp in myemp:
                datadetails |= self.env['hr.employeedepartment.details'].sudo().create({
                    'cari_id': alldata._origin.id or alldata.id,
                    'department_id': allemp.department_id.id,
                    'employee_id': allemp.id,
                    'nik': allemp.nik,
                    'job_id': allemp.job_id.id,
                    'is_selected': False,
                })
            alldata.employee_ids = datadetails.ids
    
    @api.onchange('department_id')
    def _isi_employee(self):
        for alldata in self:
            if not alldata.department_id:
                return
            datadetails = self.env['hr.employeedepartment.details']
            myemp = self.env['hr.employee'].sudo().search([('department_id','=',alldata.department_id.id),('state','=','approved')])
            for allemp in myemp:
                datadetails |= self.env['hr.employeedepartment.details'].sudo().create({
                    'cari_id': alldata._origin.id or alldata.id,
                    'department_id': allemp.department_id.id,
                    'employee_id': allemp.id,
                    'nik': allemp.nik,
                    'job_id': allemp.job_id.id,
                    'is_selected': False,
                })
            alldata.employee_ids = datadetails.ids
            
    def action_insert_empgroup(self):
        dataemp = []
        
        if self._context.get('fieldname') == 'plan_id':
            datadet = self.env['hr.overtime.employees']
            for alldet in self.employee_ids:
                if alldet.is_selected == True:
                    datadet |= self.env['hr.overtime.employees'].sudo().create({
                        'planning_id': self.plan_id.id,
                        'area_id': alldet.employee_id.area.id,
                        'branch_id': alldet.employee_id.branch_id.id,
                        'department_id': alldet.employee_id.department_id.id,
                        'employee_id': alldet.employee_id.id,
                        'nik': alldet.employee_id.nik,
                        'plann_date_from':self.plann_date_from,
                        'plann_date_to':self.plann_date_to,
                        'ot_plann_from':self.ot_plann_from,
                        'ot_plann_to':self.ot_plann_to,
                        'machine' : self.machine,
                        'work_plann' : self.work_plann,
                        'output_plann' : self.output_plann,
                        'transport' : self.transport,
                        'meals' : self.meals,
                        'ot_type' : 'regular',
                        'approve_time_from' : self.approve_time_from,
                        'approve_time_to' : self.approve_time_to,
                        })
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'hr.overtime.planning',
                'view_mode': 'form',
                'target': 'current',
                'res_id':self.plan_id.id,
                'views': [[False, 'form']]
            }
        else:
            datadet = self.env['hr.empgroup.details']
            if not(self.wdcode.id):
                raise UserError('WD Code Must Selected')
            
            if not(self.valid_from):
                raise UserError('Date Valid From Must be Selected')
            
            if not(self.valid_to):
                raise UserError('Date Valid to Must be  Selected')
            
            for alldet in self.employee_ids:
                if alldet.is_selected == True:
                    datadet |= self.env['hr.empgroup.details'].sudo().create({'empgroup_id': self.empgroup_id.id,
                        'area_id': alldet.employee_id.area.id,
                        'branch_id': alldet.employee_id.branch_id.id,
                        'department_id': alldet.department_id.id,
                        'employee_id': alldet.employee_id.id,
                        'nik': alldet.employee_id.nik,
                        'job_id':alldet.job_id.id,
                        'wdcode':self.wdcode.id,
                        'valid_from':self.valid_from,
                        'valid_to':self.valid_to})
            return True


class HrCariEmployeeDepartmentDetails(models.TransientModel):
    _name = 'hr.employeedepartment.details'
    _description = 'Search Employee Department Wizard'

    cari_id = fields.Many2one('hr.employeedepartment',string='Employee Cari ID')
    department_id = fields.Many2one('hr.department',string='Department ID')
    employee_id = fields.Many2one('hr.employee',string='Employee Name',index=True)
    nik = fields.Char('NIK')
    job_id = fields.Many2one('hr.job',string='Job Position',index=True)
    is_selected = fields.Boolean('Select',default=False)