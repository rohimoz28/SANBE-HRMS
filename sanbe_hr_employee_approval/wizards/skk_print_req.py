from odoo import api, fields, models
from odoo.exceptions import UserError


class SkkEmployeeReqWizard(models.TransientModel):
    _name = 'skk.employee.req.wizard'
    _description = 'SKK Employee Request Wizard'

    # Changed to Many2one for single employee SKK
    name = fields.Char(string="No.", required=True, store=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    descr = fields.Char("Reason", required=True)
    date_print = fields.Date("Date Print", default=fields.Date.context_today)
    hr_manager_id = fields.Many2one('hr.employee', string="HR Manager",
                                   default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
                                   )
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    first_join_date = fields.Char(store=True)
    join_date_contract = fields.Char(store=True)
    
    @api.model
    def default_get(self, fields):
        res = super(SkkEmployeeReqWizard, self).default_get(fields)
        if self.env.context.get('active_model') == 'hr.employee' and self.env.context.get('active_ids'):
            # If multiple employees are selected, take the first one for this wizard
            res['employee_id'] = self.env.context['active_ids'][0]
            employee = self.env['hr.employee'].browse(self.env.context['active_ids'][0])
            if employee.join_date:
                res['first_join_date'] = res['first_join_date'] = employee.join_date.strftime('%d %B %Y').replace(
                        'January', 'Januari'
                    ).replace(
                        'February', 'Februari'
                    ).replace(
                        'March', 'Maret'
                    ).replace(
                        'April', 'April'
                    ).replace(
                        'May', 'Mei'
                    ).replace(
                        'June', 'Juni'
                    ).replace(
                        'July', 'Juli'
                    ).replace(
                        'August', 'Agustus'
                    ).replace(
                        'September', 'September'
                    ).replace(
                        'October', 'Oktober'
                    ).replace(
                        'November', 'November'
                    ).replace(
                        'December', 'Desember'
                    ) # convert employee.join_date to 09 Mei 2025

            if employee.join_date_contract:
                res['join_date_contract'] = res['join_date_contract'] = employee.join_date_contract.strftime('%d %B %Y').replace(
                        'January', 'Januari'
                    ).replace(
                        'February', 'Februari'
                    ).replace(
                        'March', 'Maret'
                    ).replace(
                        'April', 'April'
                    ).replace(
                        'May', 'Mei'
                    ).replace(
                        'June', 'Juni'
                    ).replace(
                        'July', 'Juli'
                    ).replace(
                        'August', 'Agustus'
                    ).replace(
                        'September', 'September'
                    ).replace(
                        'October', 'Oktober'
                    ).replace(
                        'November', 'November'
                    ).replace(
                        'December', 'Desember'
                    ) # convert employee.join_date to 09 Mei 2025 
            
        return res
    
    def action_confirm(self):
        self.ensure_one()
        if not self.descr:
            raise UserError("Please reason for this SKK")
        elif self.employee_id.state != 'approved' or not self.employee_id.active:
            raise UserError("Cannot allowed to print")
        else:
            return self.env.ref('sanbe_hr_employee_approval.report_skk_pdf_action').report_action(self)