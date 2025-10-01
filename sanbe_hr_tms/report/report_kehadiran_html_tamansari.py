from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class AttendanceReportHTML(models.AbstractModel):
    _name = 'report.sanbe_hr_tms.report_attendance_html_tamansari'
    _description = 'HTML Attendance Report'

    @api.model
    def _get_report_values(self, docids, data=None):

        if not docids:
            active_ids = self.env.context.get('active_ids', [])
            active_model = self.env.context.get('active_model', 'hr.tmsentry.summary')
            
            if not active_ids:
                raise UserError(_("Tidak Ada data untuk record"))
            
            lines = self.env[active_model].browse(active_ids)
        else:
            lines = self.env['hr.tmsentry.summary'].browse(docids)

        
        report_lines = []
        for index, obj in enumerate(lines, 1):
            try:
                workingday = obj.employee_id.workingday or 0
                line_data = {
                    'no': index,
                    'employee_nik': obj.nik or 'Tidak Diketahui',
                    'employee_name': obj.employee_id.name or 'Tidak Diketahui',
                    'attendee_total': workingday,
                    'attendee_count': obj.attendee_count or 0,
                    'lk': obj.lk or 0,
                    'lb': obj.lb or 0,
                    'leave_count': obj.leave_count or 0,
                    'sick_count': obj.sick_count or 0,
                    'ch': obj.ch or 0,
                    'i30': obj.i30 or 0,
                    'absent_count': obj.absent_count or 0,
                    'paid_leave': obj.paid_leave or 0,
                    'remark': obj.remark or '',
                }
                
                report_lines.append(line_data)
                
            except Exception as e:
                _logger.info(f"Error processing record: {e}")

        # _logger.info(f"Processing row {index}: {report_lines}")
        
        return {
            'doc_model': 'hr.tmsentry.summary',
            'docs': lines,
            'report_lines': report_lines,
        }