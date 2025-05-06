# -*- coding : utf-8 -*-
#################################################################################
# Author    => Albertus Restiyanto Pramayudha
# email     => xabre0010@gmail.com
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA
#################################################################################


from odoo import api, fields, models, _
class EducationLevel(models.Model):
    _name = 'employee.educations'
    _description = "Employee Education"
    _rec_name = 'name'

    employee_id = fields.Many2one('hr.employee',string='Employee ID',index=True)
    school_level = fields.Selection([('universitas','Perguruan Tinggi'),
                                     ('sma','SMA'),
                                     ('smp','SMP'),
                                     ('sd','SD')],default='universitas',required=True,string='School Level')
    name = fields.Char('School Name')
    year_garduated = fields.Char('Year')
    majoring= fields.Char('Majoring')
    level_certificated = fields.Selection([('s3','S3'),
                                     ('s2','S2'),
                                     ('s1','S1'),
                                     ('d3','D3'),
                                     ('d4', 'D4'),
                                     ('sma','SMA'),
                                     ('smp','SMP'),
                                     ('sd','SD')],default='s1',compute="_compute_level_certificated",string='Certificate Level')
    level_certificated_sd = fields.Selection([('sd','SD')],default='sd',string='Certificate Level')
    level_certificated_smp = fields.Selection([('smp','SMP')],default='smp',string='Certificate Level')
    level_certificated_sma = fields.Selection([('sma','SMA')],default='sma',string='Certificate Level')
    level_certificated_univ = fields.Selection([('s3','S3'),
                                     ('s2','S2'),
                                     ('s1','S1'),
                                     ('d4','D4'),
                                     ('d3', 'D3')
                                     ],default='s1',string='Certificate Level')
    gpa = fields.Float('GPA')
    is_last_edu = fields.Boolean('Last Education')
    
    @api.depends('school_level', 'level_certificated_sd', 'level_certificated_smp', 'level_certificated_sma', 'level_certificated_univ')
    def _compute_level_certificated(self):
        for rec in self: 
            if rec.school_level in ['sd']:
                rec.level_certificated = rec.level_certificated_sd
            elif rec.school_level in ['smp']:
                rec.level_certificated = rec.level_certificated_smp
            elif rec.school_level in ['sma']:
                rec.level_certificated = rec.level_certificated_sma
            else:
                rec.level_certificated = rec.level_certificated_univ

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if vals.get('is_last_edu') and vals.get('employee_id'):
            record._unset_other_last_edu()
        return record

    def write(self, vals):
        result = super().write(vals)
        if vals.get('is_last_edu') and vals.get('employee_id', self.employee_id.id):
            self._unset_other_last_edu()
        return result

    def _unset_other_last_edu(self):
        self.search([
            ('employee_id', '=', self.employee_id.id),
            ('id', '!=', self.id),
            ('is_last_edu', '=', True)
        ]).write({'is_last_edu': False})
    
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