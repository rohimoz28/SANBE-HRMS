from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class AttendanceReportHTML(models.AbstractModel):
    _name = 'report.sanbe_hr_tms.report_finance_html'
    _description = 'HTML Finance Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Prepare data for HTML report
        
        :param docids: List of record IDs
        :param data: Additional data passed from the report action
        :return: Dictionary of report values
        """
        # If no docids provided, try to get from context
        if not docids:
            active_ids = self.env.context.get('active_ids', [])
            active_model = self.env.context.get('active_model', 'hr.tmsentry.summary')
            
            if not active_ids:
                raise UserError(_("Tidak Ada data untuk record"))
            
            lines = self.env[active_model].browse(active_ids)
        else:
            lines = self.env['hr.tmsentry.summary'].browse(docids)

        # Prepare report data
        report_lines = []
        for index, obj in enumerate(lines, 1):
            try:
                workingday = obj.employee_id.workingday or 0
                line_data = {
                    'no': index,
                    'fkelompok': None,
                    'fbagian': None,
                    'fsalary_ke': None,
                    'fnik': obj.nik or None,
                    'employee_name': obj.employee_id.name or None,
                    'fsp': None,
                    'fmasakrj': None,
                    'fstatus': None,
                    'fnpwp': obj.employee_id.no_npwp or None,
                    'ftanggung': None,
                    'fkontrak': None,
                    'fhrnormal': None,
                    'fharibyr': obj.attendee_total + obj.leave_count + obj.sick_count,
                    'fhadir': obj.attendee_count,
                    'fharilmb': len(obj.tmsentry_details_30_ids),
                    'fdinas1': obj.nightshift_count,
                    'fdinas2': obj.nightshift2_count,
                    'flembur1': obj.ot1_totalx,
                    'flembur2': obj.ot2_totalx,
                    'flembur3': obj.ot3_totalx,
                    'flembur4': obj.ot4_totalx,
                    'fsakit': obj.sick_count,
                    'fijin': obj.leave_count,
                    'fsuka': None,
                    'fcclkop': None,
                    'fbunga': None,
                    'fhtrans': None,
                    'fhmakan': None,
                    'fcutihml': None,
                    'fcutibyr': None,
                    'fkoperasi': None,
                    'fcclbako': None,
                    'ftjbbm': None,
                    'ftrpsp': None,
                    'fincentive': None,
                    'ftjmk': None,
                    'ftjkel': None,
                    'fupsh': None,
                    'fbfflag001': None,
                    'fcutithn': None,
                    'flmbbi': None,
                    'flmbbs': None,
                    'flevel_jab': obj.employee_id.employee_levels.name,
                    'fjob_title': obj.employee_id.job_id.name,
                    'fkpi_ctgry': None,
                }
                
                report_lines.append(line_data)
                
            except Exception as e:
                # Log error but continue processing other records
                _logger.info(f"Error processing record: {e}")

        _logger.info(f"Processing row {index}: {report_lines}")
        
        return {
            'doc_model': 'hr.tmsentry.summary',
            'docs': lines,
            'doc': lines[0] if lines else None,
            'report_lines': report_lines,
        }