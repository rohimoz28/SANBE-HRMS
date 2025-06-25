from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError


class HrEmployeeAddresses(models.Model):
    _name = 'hr.employee.addresses'
    _description = 'List of Employee Addresses'

    employee_id = fields.Many2one('hr.employee', string='Employee ID', index=True)
    address_type = fields.Selection([
        ('KTP', 'KTP'),
        ('DOMISILI', 'Domisili'),
        ('MESS', 'Mess'),
        ('OTHER', 'Other')
    ], string='Address Type', required=True)
    address = fields.Text('Address')
    city = fields.Char('Kota/ Kab')
    district = fields.Char('Kecamatan')
    subdistrict = fields.Char('Kelurahan')
    rt = fields.Char('RT')
    rw = fields.Char('RW')
    default = fields.Boolean(string='Default', default=False)
    private_state_id = fields.Many2one(
        "res.country.state", string="State",
        domain="[('country_id', '=?', private_country_id)]",
        groups="hr.group_hr_user")
    private_country_id = fields.Many2one("res.country", string="Country", groups="hr.group_hr_user")
    private_zip = fields.Char(string="Private Zip", groups="hr.group_hr_user")

    _sql_constraints = [
        ('unique_address_type', 'unique(employee_id, address_type)', 'Only one address per type allowed for an employee'),
    ]

    '''
        validation : one employee can not 
        have more than one default address
    '''
    # @api.constrains('employee_id', 'default')
    # def _check_unique_default_address(self):
    #     for record in self:
    #         if record.default:
    #             domain = [('employee_id', '=', record.employee_id.id), ('id', '!=', record.id), ('default', '=', True)]
    #             # existing_default_address = self.search_count(domain)
    #             existing_default_address = self.search(domain, limit=1)
    #             if existing_default_address:
    #                 raise UserError(_('Only one address can be default per employee'))

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if vals.get('default') and vals.get('employee_id'):
            record._unset_other_default()
        return record

    def write(self, vals):
        result = super().write(vals)
        if vals.get('default') and vals.get('employee_id', self.employee_id.id):
            self._unset_other_default()
        return result

    def _unset_other_default(self):
        self.search([
            ('employee_id', '=', self.employee_id.id),
            ('id', '!=', self.id),
            ('default', '=', True)
        ]).write({'default': False})
    
    def action_confirm_delete(self):
        self.unlink()