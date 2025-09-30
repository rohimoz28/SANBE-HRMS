from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo import models, api
import logging

_logger = logging.getLogger(__name__)



class MealsReportHTML(models.Model):
    _name = 'report.sanbe_hr_tms.report_ot_meals_html'
    _description = 'HTML Bundling Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        if not docids:
            active_ids = self.env.context.get('active_ids', [])
            active_model = self.env.context.get('active_model', 'hr.overtime.employees')

            if not active_ids:
                raise UserError(_("Tidak Ada data untuk record"))

            lines = self.env[active_model].browse(active_ids)
        else:
            lines = self.env['hr.overtime.employees'].browse(docids)

        grouped_lines = {}

        for obj in lines:
            department_name = obj.department_id.complete_name or 'Tidak Diketahui'

            line_data = {
                'area': self.env.user.area.name or 'Tidak Diketahui',
                'branch': obj.branch_id.name or 'Tidak Diketahui',
                'department': department_name,
                'employee_name': obj.employee_id.name or '-',
                'nik': obj.nik or '-',
                'address': obj.address_employee or '-',
                'shift': dict(obj._fields['default_ot_hours'].selection).get(obj.default_ot_hours, '-'),
                'overtime_date': obj.plann_date_from.strftime('%d %b %Y') if obj.plann_date_from else '-',
                'overtime_day': obj.plann_date_from.strftime('%A') if obj.plann_date_from else '-',
                'plan_start': obj.ot_plann_from_char or '-',
                'plan_end': obj.ot_plann_to_char or '-',
                'real_start': obj.realization_time_from_char or '-',
                'real_end': obj.realization_time_to_char or '-',
                'route': obj.route_id.name or '-',
                'meal': 'Dine' if obj.meals else ('Cash' if obj.meals_cash else '-'),
            }

            # Tambahkan ke dalam grup berdasarkan department
            if department_name not in grouped_lines:
                grouped_lines[department_name] = []

            grouped_lines[department_name].append(line_data)

        # Susun final report_lines sesuai format yang diinginkan
        report_lines = []
        for dept_name, lines_list in grouped_lines.items():
            for idx, line in enumerate(lines_list, 1):
                line['no'] = idx  # Beri nomor urut per-department
            report_lines.append({
                'department': dept_name,
                'lines': lines_list,
            })
        total_lines = sum(len(lines_list) for lines_list in grouped_lines.values())
        area = self.env.user.area.name or 'Tidak Diketahui'
        _logger.info(f"Processed {len(report_lines)} departments for area {area}")

        return {
            'doc_model': 'hr.overtime.employees',
            'docs': lines,
            'report_lines': report_lines,
            'area': area,
            'total_lines': total_lines,
        }