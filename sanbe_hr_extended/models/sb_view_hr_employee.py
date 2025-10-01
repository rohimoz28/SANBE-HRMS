from odoo import fields, models, tools, api, _

class SbViewHrEmployee(models.Model):
    _auto = False
    _name = 'sb.view.hr.employee'
    _description = 'View HR Employee'
    
    id = fields.Integer('ID', required=True)
    name = fields.Char('Name')
    area_id = fields.Many2one('res.territory', string='Area')
    branch_id = fields.Many2one('res.branch', string='Business Unit')
    department_id = fields.Many2one('hr.department', string='Sub Department')
    job_id = fields.Many2one('hr.job', string='Job Position')
    nik = fields.Char('NIK')
    user_id = fields.Many2one('res.users', string='user')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                select 
                    he.id AS id, 
                    he."name" name, 
                    he.area area_id, 
                    he.branch_id, 
                    he.department_id, 
                    he.job_id, 
                    he.nik,
                    he.user_id 
                from hr_employee he 
                where he.state = 'approved'
        )
        """ % (self._table, ))