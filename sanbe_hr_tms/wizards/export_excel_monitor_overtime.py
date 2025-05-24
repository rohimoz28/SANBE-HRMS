import io
import base64
from odoo import _, api, fields, models
from odoo.exceptions import UserError
import xlsxwriter
import logging
_logger = logging.getLogger(__name__)

class ExportExcelMonitorOvertime(models.TransientModel):
    _name='export.excel.monitor.ot'
    _description = 'Export Excel Monitoring Overtime'

    area_id = fields.Many2one('res.territory', 
                              string='Area',
                              domain=lambda self: self._get_areas_domain(),
                              options="{'no_create': True}")

    def _get_areas_domain(self):
        """
        Return the domain to filter areas based on the areas
        available in the sb.employee.overtime model.
        """
        area_ids = self.env['sb.employee.overtime'].search([]).mapped('area_id.id')
        return [('id', 'in', area_ids)]
    
    def button_export_xlsx(self):
        self.ensure_one()

        employee_overtime_domain = []

        if self.area_id:
            employee_overtime_domain.append(('area_id', '=', self.area_id.id))
        
        employee_overtime = self.env['sb.employee.overtime'].search(employee_overtime_domain)

        return {
            'type': 'ir.actions.report',
            'report_name': 'sanbe_hr_tms.report_monitor_overtime_excel',
            'report_type': 'xlsx',
            'report_file': f'Monitoring_Overtime_{self.area_id.name or "All"}',
            'context': {
                'active_model': 'sb.employee.overtime',
                'active_ids': employee_overtime.ids,  # semua record
            }
        }
        