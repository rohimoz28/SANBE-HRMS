from odoo import fields, models, api


class HREmployee(models.Model):
    _inherit = "hr.employee"

    address_ids = fields.One2many('hr.employee.addresses', 'employee_id', auto_join=True, string='Asset Details')
