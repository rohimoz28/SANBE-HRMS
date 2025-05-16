from odoo import fields, models, api


class SbOvertimeAttendance(models.Model):
    _name = 'sb.overtime.attendance'
    _description = 'Monitoring OT Request vs Realization'

    no_request = fields.Char(
        string='No Request',
        required=False)
    req_date = fields.Date(
        string='Request Date',
        required=False)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    nik = fields.Char(
        string='NIK',
        required=False)
    req_time_fr = fields.Float(
        string='Req Time Fr',
        required=False)
    req_time_to = fields.Float(
        string='Req Time To',
        required=False)
    rlz_time_fr = fields.Float(
        string='Rel Time Fr',
        required=False)
    rlz_time_to = fields.Float(
        string='Rel Time To',
        required=False)
    approve_time_from = fields.Float(
        string='App Time Fr',
        required=False)
    approve_time_to = fields.Float(
        string='App Time To',
        required=False)
    area_id = fields.Many2one('res.territory', string='Area ID', index=True)
    branch_id = fields.Many2one('res.branch', string='Bisnis Unit', index=True, domain="[('id','in',branch_ids)]")
    department_id = fields.Many2one('hr.department', domain="[('id','in',alldepartment)]", string='Sub Department', index=True)
    periode_id = fields.Many2one('hr.opening.closing',string='Period',index=True)
    state = fields.Char(
        string='State',
        required=False)
    is_shuttle_car = fields.Boolean('Shuttle Car')
    is_dine_in = fields.Boolean('Dine In')
    is_meal_cash = fields.Boolean('Meal Cash')
    is_cancel = fields.Boolean('Cancel')
    rlz_date = fields.Date(
        string='Realization Date',
        required=False)
    aot1 = fields.Float(
        string='OT 1',
        required=False)
    aot2 = fields.Float(
        string='OT 2',
        required=False)
    aot3 = fields.Float(
        string='OT 3',
        required=False)
    aot4 = fields.Float(
        string='OT 4',
        required=False)
    overtime = fields.Char(
        string='Overtime',
        required=False)
    
    