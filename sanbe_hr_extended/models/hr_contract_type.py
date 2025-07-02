from odoo import api, fields, models, _

class HrContractType(models.Model):
    _inherit = 'hr.contract.type'

    is_active = fields.Boolean('Active')