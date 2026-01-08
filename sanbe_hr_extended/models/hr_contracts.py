# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.osv import expression
import logging
_logger = logging.getLogger(__name__)

class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.depends('area')
    def _isi_semua_branch(self):
        for allrecs in self:
            databranch = []
            for allrec in allrecs.area.branch_id:
                mybranch = self.env['res.branch'].search([('name','=', allrec.name)], limit=1)
                databranch.append(mybranch.id)
            allbranch = self.env['res.branch'].sudo().search([('id','in', databranch)])
            allrecs.branch_ids =[Command.set(allbranch.ids)]

    @api.depends('area','branch_id')
    def _isi_department_branch(self):
        for allrecs in self:
            databranch = []
            allbranch = self.env['hr.department'].sudo().search([('branch_id','=', allrecs.branch_id.id)])
            allrecs.alldepartment =[Command.set(allbranch.ids)]


    attachment_contract =  fields.Many2many('ir.attachment', 'hr_contract_rel',string='Contract Document',
                                          help="You may attach files to with this")
    number = fields.Char('Contract Number')
    area = fields.Many2one('res.territory',string='Area',tracking=True,readonly=False)
    branch_ids = fields.Many2many('res.branch','res_branch_rel',string='AllBranch',compute='_isi_semua_branch',store=False)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True, domain="[('state','not in',['hold','inactive'])]", index=True)
    date_end = fields.Date('End Date', tracking=True, help="End date of the contract (if it's a fixed-term contract).", required=True)
    alldepartment = fields.Many2many('hr.department','hr_department_rel', string='All Department',compute='_isi_department_branch',store=False)
    branch_id = fields.Many2one('res.branch',string='Business Units',domain="[('id','in',branch_ids)]",tracking=True,readonly=False)
    depart_id = fields.Many2one('hr.department', domain="[('id','in',alldepartment)]",string='Sub Department' )
    wage = fields.Monetary('Wage', required=False, tracking=True, help="Employee's monthly gross wage.", group_operator="avg")
    ws_month = fields.Integer('Working Service Month', compute="_compute_service_duration_display",readonly=True)
    ws_year  = fields.Integer('Working Service Year', compute="_compute_service_duration_display",readonly=True)
    ws_day = fields.Integer('Working Service Day', compute="_compute_service_duration_display",readonly=True)
    nilai_pa = fields.Char('Nilai PA')
    sallary_amount = fields.Monetary('Sallary Amount')
    nik = fields.Char('Nik')
    nik_lama = fields.Char('Nik Lama')
    emp_id = fields.Char('Employee ID',related='employee_id.employee_id',readonly=True)
    emp_name = fields.Char('Employee Name',related='employee_id.name',readonly=True)
    no_pkwt = fields.Selection([('1','1'),
                                ('2','2'),
                                ('3','3'),
                                ('4','4'),
                                ('5','5')],string='# of PKWT',ondelete='cascade')
    contract_type_id = fields.Many2one('hr.contract.type', "Contract Type", domain=[('is_active', '=', True)], tracking=True)
    contract_type_code = fields.Char('Contract Ttpe Code', related='contract_type_id.code')
    contract_year = fields.Selection([('1','1'),
                                ('2','2'),
                                ('3','3'),
                                ('4','4'),
                                ('5','5')],string='Tahun Ke')
    contract_ref_id = fields.Many2one('hr.contract', string='Referensi Kontrak', domain="[('employee_id', '=', employee_id),('state', '=', 'open'),('date_start', '<=', date_start),('date_end', '>=', date_start)]")
    # @api.model
    # def name_create(self, name):
    #     default_type = self._context.get('employee_name')
    #     create_values = {self._rec_name: name}
    #     partner = self.create(create_values)
    #     return partner.id, partner.display_name
    _sql_constraints = [
        ('contract_code_unique', 'UNIQUE(name)', 'A Contract must have a unique name.'),
    ]

    # @api.model
    # def create(self, vals):
    #     check_contract = self.env['hr.contract'].search(
    #         [('employee_id', '=', vals.get('employee_id')),
    #          #  ('state', '!=', 'close')
    #          ('state', '=', 'open')
    #          ], limit=1)
        
    #     if check_contract:
    #         raise UserError('A contract with the same employee is already active. You cannot create another contract for the same employee.')
        
    #     return super(HrContract, self).create(vals)

    @api.constrains('name')
    def _contrains_name(self):
        # Prevent a coupon from having the same code a program
        cekktp  = self.env['hr.contract'].sudo().search([('name','=', self.name)])
        if len(cekktp) > 1:
            raise UserError(_('A Contract with the same name already exist.'))

    @api.model
    def default_get(self, default_fields):
        res = super(HrContract, self).default_get(default_fields)
        empname = self._context.get('employee_name')
        isemployee = self._context.get('is_employee')
        if isemployee:
            myemp = self.env['hr.employee'].sudo().search([('name','=', empname)])
            if myemp:
                res.update({'employee_id': myemp.id})
            else:
                myemp = False
                myemp = self.env['hr.employee'].create({'name': empname,
                                                        'area':  self._context.get('area',False),
                                                        'branch_id':  self._context.get('branch',False),
                                                        'department_id':  self._context.get('department',False),
                                                        'job_id':  self._context.get('job_id',False),})
                myemp.write({'name': empname})
                res.update({'employee_id': myemp.id})
        return res

    @api.depends('employee_id','state')
    @api.onchange('employee_id')
    def _compute_employee_contract(self):
        for contract in self.filtered('employee_id'):
            contract.job_id = contract.employee_id.job_id
            contract.depart_id = contract.employee_id.department_id
            contract.resource_calendar_id = contract.employee_id.resource_calendar_id
            contract.company_id = contract.employee_id.company_id
            contract.area = contract.employee_id.area.id
            contract.branch_id = contract.employee_id.branch_id.id
            contract.nik = contract.employee_id.nik
            contract.nik_lama = contract.employee_id.nik_lama

    def write(self,vals_list):
        res = super(HrContract,self).write(vals_list)
        for allrec in self:
            contract_ref = self.env['hr.contract'].sudo().search([('id','=',allrec.contract_ref_id.id)], limit=1)
            if allrec.state =='open':
                # if allrec.employee_id.state !='approved':
                #     raise UserError('Cannot Running Contract Because The Employee Not Yet Being Approved!')
                # empstatus = ''
                empstatus = allrec.employee_id.emp_status
                allrec.employee_id.contract_id = allrec.id
                allrec.employee_id.contract_datefrom = allrec.date_start
                allrec.employee_id.contract_dateto = allrec.date_end
                mycari = self.env['hr.employment.log'].sudo().search([('employee_id','=',allrec.employee_id.id),('job_status','=','contract'),('service_type','=', allrec.contract_type_id.code),('start_date','=',allrec.date_start),('end_date','=', allrec.date_end)])
                if not mycari:
                    self.env['hr.employment.log'].sudo().create({'employee_id': allrec.employee_id.id,
                                                                 'service_type': allrec.contract_type_id.code,
                                                                 'start_date': allrec.date_start,
                                                                 'end_date': allrec.date_end,
                                                                 'bisnis_unit': allrec.branch_id.id,
                                                                 'department_id': allrec.depart_id.id,
                                                                 'job_title': allrec.job_id.name,
                                                                 'job_status': 'contract',
                                                                 'emp_status': empstatus,
                                                                 'model_name': 'hr.contract',
                                                                 'model_id': allrec.id,
                                                                 'doc_number': allrec.name,
                                                                 })
                    
                if contract_ref and allrec.contract_type_id.code == 'ADCO':                   
                    contract_ref.write({'state': 'close'})
    
    @api.constrains('employee_id', 'state', 'kanban_state', 'date_start', 'date_end')
    def _check_current_contract(self):
        """ Two contracts in state [incoming | open | close] cannot overlap """
        # excluded_ids = []
        excluded_ids = set()
        for contract in self.filtered(lambda c: (c.state not in ['draft', 'cancel'] or c.state == 'draft' and c.kanban_state == 'done') and c.employee_id and c.contract_type_id.code != 'ADCO'): 
            
            excluded_ids.add(contract.id)

            if contract.contract_ref_id and contract.contract_ref_id.employee_id == contract.employee_id:
                excluded_ids.add(contract.contract_ref_id.id)
            
            contract_ref = self.env['hr.contract'].sudo().search([('contract_ref_id','=',contract.id)])
            if contract_ref:
                excluded_ids.update(contract_ref.ids)

            domain = [
                ('id', 'not in', list(excluded_ids)),
                ('employee_id', '=', contract.employee_id.id),
                ('company_id', '=', contract.company_id.id),
                '|',
                    ('state', 'in', ['open', 'close']),
                    '&',
                        ('state', '=', 'draft'),
                        ('kanban_state', '=', 'done')
            ]

            if not contract.date_end:
                start_domain = []
                end_domain = ['|', ('date_end', '>=', contract.date_start), ('date_end', '=', False)]
            else:
                start_domain = [('date_start', '<=', contract.date_end)]
                end_domain = ['|', ('date_end', '>', contract.date_start), ('date_end', '=', False)]

            domain = expression.AND([domain, start_domain, end_domain])
            if self.search_count(domain):
                raise ValidationError(
                    _(
                        'An employee can only have one contract at the same time. (Excluding Draft and Cancelled contracts).\n\nEmployee: %(employee_name)s',
                        employee_name=contract.employee_id.name
                    )
                )
                

    @api.depends("date_start","date_end")
    def _compute_service_duration_display(self):
        for record in self:
            if record.date_start and record.date_end:
                service_until = record.date_end
                if record.date_start and service_until > record.date_start:
                    service_duration = relativedelta(
                        service_until, record.date_start
                    )
                    record.ws_year = service_duration.years
                    record.ws_month = service_duration.months
                    record.ws_day = service_duration.days
                else:
                    record.ws_year = 0
                    record.ws_month = 0
                    record.ws_day = 0
            else:
                record.ws_year = 0
                record.ws_month = 0
                record.ws_day = 0
    #
    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        domain = domain or []
        if name:
            #mybranch = self.env['res.branch'].sudo().search([('branch_code','=','BU3')])
            mybranch = self.env.user.branch_id
            search_domain = [('name', operator, name),('branch_id','=',mybranch.id)]
            user_ids = self._search(search_domain, limit=1, order=order)
            return user_ids
        else:
            return super()._name_search(name, domain, operator, limit, order)

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

    @api.model
    def default_get(self, default_fields):
        res = super(HrContract, self).default_get(default_fields)
        if self.env.user.branch_id:
            res.update({
                'branch_id' : self.env.user.branch_id.id or False
            })
        return res
    
    def get_contract_list(self):
        today = date.today()

        contracts = self.search([
            ('date_end', '!=', False),
            ('date_end', '>=', today)
            ], limit=10)

        result = []
        for index, contract in enumerate(contracts, start=1):
            result.append({
                'no': index,
                'nik': contract.employee_id.nik or '',
                'name': contract.employee_id.name or '',
                'job': contract.job_id.name or '',
                'department': contract.depart_id.name or '',
                'company': contract.company_id.name or '',
                'start_date': contract.date_start.strftime('%d-%m-%Y') if contract.date_start else '',
                'end_date': contract.date_end.strftime('%d-%m-%Y') if contract.date_end else '',
                'duration': self._get_duration(contract),
            })
        return result
    
    def _get_duration(self, contract):
        if not contract.date_start or not contract.date_end:
            return ''

        duration = contract.date_end - contract.date_start
        
        years = duration.days // 365
        remaining_days = duration.days % 365
        months = remaining_days // 30
        days = remaining_days % 30

        result = []
        if years and duration >= 365:
            result.append(f"{years} tahun")
        if months:
            result.append(f"{months} bulan")
        if days or not result:
            result.append(f"{days} hari")

        return ' '.join(result)