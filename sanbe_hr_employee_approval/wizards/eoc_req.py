from odoo import api, fields, models
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError


class SkkEmployeeEOCWizard(models.TransientModel):
    _name = 'skk.employee.eoc.wizard'
    _description = 'SKK Employee End of Contract Wizard'

    # Changed to Many2one for single employee SKK
    name = fields.Char(string="No.", required=True, store=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    receiver_id = fields.Many2one('hr.employee', string="Receive", default=lambda self:self.employee_id.parent_id.id, required=True)
    # contracts_count = fields.Integer(string="Contracts",default=1, required=True)
    
    date_print = fields.Date("Date Print", default=fields.Date.context_today)
    oec_date = fields.Date("End of Contract", default=lambda self:self.employee_id.contract_dateto)
    char_eoc_date = fields.Char(store=True)
    contract_year = fields.Integer('Contract Year', store=True)
    
    def month_to_roman(self,month):
        roman_list = [
            (0, '-'), (1, 'I'), (2, 'II'), (3, 'III'), 
            (4, 'IV'), (5, 'V'), (6, 'VI'), (7, 'VII'), (8, 'VIII'), 
            (9, 'IX'), (10, 'X'), (11, 'XI'),(12, 'XII')
        ]
        if 0 <= month <= 12:
            return roman_list[month][1]
        else:
            return "Invalid month"
    
    @api.model
    def default_get(self, fields):
        res = super(SkkEmployeeEOCWizard, self).default_get(fields)
        if self.env.context.get('active_model') == 'hr.employee' and self.env.context.get('active_ids'):
            # -----auto renumber --------
            # today = datetime.today()
            # month = today.month
            # format_number = f"/PERS-GA/EOC/{self.month_to_roman(month)}/{today.year}"
            # last_record = self.env['skk.employee.req.wizard'].search([], order='id desc', limit=1)
            # last_id = last_record.id if last_record else 0

            # res['name'] = f"{last_id + 1}{format_number}"
            # If multiple employees are selected, take the first one for this wizard
            res['employee_id'] = self.env.context['active_ids'][0]
            employee = self.env['hr.employee'].browse(self.env.context['active_ids'][0])
            res['receiver_id'] = employee.parent_id.id
            if employee.contract_id and employee.contract_id.contract_year != '5':
                res['contract_year'] = int(employee.contract_id.contract_year) + 1
            if employee.contract_id and employee.contract_id.contract_year == '5':
                res['contract_year'] = employee.contract_id.contract_year

            #definisikan contract_type
            contract_type=employee.contract_id.contract_type_id.name
            #jika contract_id ada, tapi tipenya BUKAN 'Extended'
            if employee.contract_id and contract_type != 'Extended':
                #kembalikan nilainya ke tahun yang ada di database (tanpa +1)
                res['contract_year'] = employee.contract_id.contract_year

            if employee.contract_dateto:
                res['char_eoc_date'] = employee.contract_dateto.strftime('%d %B %Y').replace(
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
        if self.employee_id.state != 'approved' or not self.employee_id.active:
            raise UserError("Cannot allowed to print")
        if self.employee_id.job_status != 'contract' or not self.employee_id.contract_dateto:
            raise UserError("Cannot allowed to print it used Contract only")
        else:
            if self.employee_id.contract_id.contract_year == '5' :
                return self.env.ref('sanbe_hr_employee_approval.report_eoc_final_year_pdf_action').report_action(self)
            else:
                return self.env.ref('sanbe_hr_employee_approval.report_eoc_pdf_action').report_action(self)