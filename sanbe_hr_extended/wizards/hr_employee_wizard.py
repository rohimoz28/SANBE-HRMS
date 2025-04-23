from odoo import models, fields, api
from odoo.exceptions import UserError


class HrEmployeeExportWizard(models.TransientModel):
    _name = 'hr.employee.export.wizard'
    _description = 'Export HR Employee Wizard'

    department_id = fields.Many2one('hr.department', string="Sub Department", required=False)

    def action_export_excel(self):
        self.ensure_one()

        # Cek jumlah karyawan terlebih dahulu sebelum redirect ke controller
        domain = [('branch_id', '=', self.env.user.branch_id.id)]
        if self.department_id:
            domain.append(('department_id', '=', self.department_id.id))

        employees = self.env['hr.employee'].search(domain)
        if not employees:
            if self.department_id:
                raise UserError(f"Tidak ada data Karyawan pada Sub Department '{self.department_id.name}'")
            else:
                raise UserError("Tidak ada data Karyawan pada cabang ini.")


        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = f"{base_url}/hr/employee/export/xlsx?department_id={self.department_id.id}"
        
        # Jika dipanggil secara interaktif dari wizard, return URL
        if self.env.context.get('export_excel'):
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'self',
            }

        # Fallback untuk menghindari error 'action.views is undefined'
        return {'type': 'ir.actions.act_window_close'}
    