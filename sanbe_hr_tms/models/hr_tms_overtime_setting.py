from odoo import fields, models, api


class HrTmsOvertimeSetting(models.Model):
    _name = 'hr.overtime.setting'
    _description = 'Overtime Configuration'

    name = fields.Char()
    type = fields.Selection(
        string='Type',
        selection=[('automatic', 'Automatic'),
                   ('reguler', 'Reguler'),
                   ('holiday', 'Holiday'),],
        required=True, )
    aot_from = fields.Integer(
        string='From',
        required=False)
    mandays = fields.Integer(
        string='man days')
    aot_to = fields.Integer(
        string='To',
        required=False)
    branch_id = fields.Many2one(comodel_name='res.branch', string='Business Unit')