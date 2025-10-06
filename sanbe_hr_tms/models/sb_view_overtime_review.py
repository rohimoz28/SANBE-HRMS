from odoo import fields, models, tools, api, _

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

class SbViewOvertimeReview(models.Model):
    _auto = False
    _name = 'sb.view.overtime.review'
    _description = 'View Overtime Review'

    id = fields.Integer('ID', required=True)
    area_id = fields.Many2one('res.territory', string='Area')
    name = fields.Char('Planning Request')
    request_date = fields.Date('Planning Request Create')
    state = fields.Selection(
        selection=TMS_OVERTIME_STATE,
        string="TMS Overtime Status")
    department_id = fields.Many2one('hr.department', string='Sub Department')
    branch_id = fields.Many2one('res.branch', string='Business Unit')
    periode_from = fields.Date('Tanggal OT Dari')
    periode_to = fields.Date('Tanggal OT Hingga')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                select
                    hop.id, 
                    hop.area_id, 
                    hop.name, 
                    hop.request_date, 
                    hop.state,
                    hop.department_id,
                    hop.branch_id,
                    hop.periode_from,
                    hop.periode_to
                from hr_overtime_planning hop
        )
        """ % (self._table, ))